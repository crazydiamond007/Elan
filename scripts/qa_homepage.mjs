/* Optional QA tool. Dependencies live outside the application; see docs/phase-5-validation.md. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const qaDirectory = process.env.MAISON_QA_DIR || "/tmp/maison-elan-browser";
const require = createRequire(path.join(qaDirectory, "package.json"));
const browserType =
  require("playwright")[process.env.MAISON_BROWSER || "chromium"];
const AxeBuilder = require("@axe-core/playwright").default;
const baseUrl = process.env.MAISON_BASE_URL || "http://127.0.0.1:8000";
const output = path.resolve(
  process.env.MAISON_QA_OUTPUT ||
    ".qa/phase-6/" + (process.env.MAISON_BROWSER || "chromium"),
);
await mkdir(output, { recursive: true });

const browser = await browserType.launch({ headless: true });
const report = {
  browser: browser.version(),
  viewports: [],
  routes: [],
  checks: [],
};
try {
  for (const [width, height] of [
    [1440, 1000],
    [1024, 900],
    [768, 1024],
    [390, 844],
    [320, 750],
  ]) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("response", (response) => {
      if (response.status() >= 400)
        errors.push(`${response.status()} ${response.url()}`);
    });
    page.on("request", (request) => {
      if (new URL(request.url()).origin !== new URL(baseUrl).origin) {
        errors.push(`Unexpected external request: ${request.url()}`);
      }
    });
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    // Full-page screenshots alone do not activate below-the-fold lazy images.
    await page.evaluate(async () => {
      for (
        let top = 0;
        top < document.documentElement.scrollHeight;
        top += innerHeight
      ) {
        window.scrollTo({ top, behavior: "instant" });
        await new Promise((resolve) => setTimeout(resolve, 120));
      }
      window.scrollTo({ top: 0, behavior: "instant" });
    });
    await page.waitForFunction(() =>
      Array.from(document.images).every(
        (image) =>
          image.closest("details:not([open])") ||
          !image.getClientRects().length ||
          (image.complete && image.naturalWidth > 0),
      ),
    );
    assert.equal(
      await page
        .locator(".header-inner")
        .evaluate((element) => getComputedStyle(element).display),
      "grid",
      "The current component stylesheet must be applied before UI checks",
    );
    assert.equal(await page.locator("h1").count(), 1);
    assert.equal(
      await page.getByRole("heading", { level: 1 }).innerText(),
      "The art\nof less.",
    );
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
      `Overflow at ${width}px`,
    );
    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    report.viewports.push({
      width,
      height,
      violations: accessibility.violations.map(({ id, impact, nodes }) => ({
        id,
        impact,
        targets: nodes.map(({ target }) => target),
      })),
    });
    await page.screenshot({
      path: path.join(output, `home-${width}.png`),
      fullPage: true,
    });
    if (width === 1440)
      await page.screenshot({ path: path.join(output, "desktop-hero.png") });
    if (width === 390)
      await page.screenshot({ path: path.join(output, "mobile-hero.png") });
    assert.deepEqual(errors, [], `Browser errors at ${width}px`);
    assert.equal(
      accessibility.violations.length,
      0,
      `Accessibility violations at ${width}px`,
    );
    await context.close();
    console.log(
      `Viewport ${width}×${height}: no overflow, browser errors or axe violations`,
    );
  }

  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  await page.goto(baseUrl);
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "Skip to content");
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(":focus").getAttribute("id"), "main-content");
  const summary = page.locator(".mobile-nav summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  assert.ok(await page.locator(".mobile-nav").evaluate((menu) => menu.open));
  await page.waitForFunction(
    () => document.getElementById("navigation-dialog")?.open,
  );
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "New in");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => !document.querySelector(".mobile-nav").open);
  assert.equal(
    await page.locator(".mobile-nav").evaluate((menu) => menu.open),
    false,
  );
  assert.ok(
    await summary.evaluate((element) => element === document.activeElement),
  );
  await summary.click();
  await page.waitForFunction(
    () => document.getElementById("navigation-dialog")?.open,
  );
  await page.mouse.click(389, 430);
  await page.waitForFunction(() => !document.querySelector(".mobile-nav").open);
  assert.equal(
    await page.locator(".mobile-nav").evaluate((menu) => menu.open),
    false,
  );
  await summary.click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "New in", exact: true })
    .click();
  await page.waitForURL("**/shop/new-arrivals/");
  assert.equal(await page.locator("h1").innerText(), "New arrivals");
  await page.goto(baseUrl);
  assert.equal(
    await page.locator(".mobile-nav").evaluate((menu) => menu.open),
    false,
  );
  await summary.click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Women", exact: true })
    .click();
  await page.waitForURL("**/shop/women/");
  assert.ok(
    await page
      .getByRole("heading", { level: 1, name: "Women", exact: true })
      .isVisible(),
  );
  report.checks.push(
    "Skip link, keyboard menu, Escape/focus return, outside dismissal, catalog and Women navigation passed",
  );
  await page.goto(baseUrl);
  assert.ok(await page.locator("#newsletter-email").isEnabled());
  assert.ok(
    await page
      .getByRole("button", { name: "Try signup", exact: true })
      .isEnabled(),
  );
  assert.equal(await page.locator(".site-footer form").count(), 1);
  report.checks.push(
    "Newsletter demo form enabled with fictional-address disclosure",
  );

  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page
      .locator(".product-image")
      .first()
      .evaluate((image) => getComputedStyle(image).transitionDuration),
    "0s",
  );
  assert.equal(
    await page.evaluate(
      () => getComputedStyle(document.documentElement).scrollBehavior,
    ),
    "auto",
  );
  report.checks.push(
    "Reduced motion disables transitions and smooth scrolling",
  );

  const routes = [
    "/shop/",
    "/shop/women/",
    "/shop/men/",
    "/shop/accessories/",
    "/collections/",
    "/collections/autumn-winter-26/",
    "/shop/sale/",
    "/products/sculpted-coat/",
    "/products/pleated-trouser/",
    "/products/everyday-tote/",
    "/our-story/",
    "/product-care/",
    "/size-guide/",
    "/demo/",
  ];
  for (const route of routes) {
    const response = await page.goto(new URL(route, baseUrl).href, {
      waitUntil: "networkidle",
    });
    assert.equal(response.status(), 200);
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    report.routes.push({
      route,
      violations: result.violations.map(({ id, impact }) => ({ id, impact })),
    });
    assert.equal(
      result.violations.length,
      0,
      `Accessibility violations at ${route}`,
    );
  }
  await context.close();
  const noScript = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 390, height: 844 },
  });
  const fallback = await noScript.newPage();
  await fallback.goto(baseUrl);
  await fallback.locator(".mobile-nav summary").click();
  await fallback
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Men", exact: true })
    .click();
  await fallback.waitForURL("**/shop/men/");
  report.checks.push(
    "Native mobile menu navigation works with JavaScript disabled",
  );
  await noScript.close();
  console.log(
    "Keyboard, reduced-motion, no-JavaScript and supporting-page checks passed",
  );
} finally {
  await writeFile(
    path.join(output, "report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
