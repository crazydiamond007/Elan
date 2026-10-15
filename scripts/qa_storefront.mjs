/* Optional browser checks for the campaign storefront and native navigation system. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
const require = createRequire(
  path.join(
    process.env.MAISON_QA_DIR || "/tmp/maison-elan-browser",
    "package.json",
  ),
);
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const base = process.env.MAISON_BASE_URL || "http://127.0.0.1:8000";
const output = path.resolve(".qa/dior-direction/chromium");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { browser: browser.version(), checks: [] };
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto(base, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  assert.match(
    await page
      .locator("body")
      .evaluate((el) => getComputedStyle(el).fontFamily),
    /Jost/,
  );
  await page.locator(".nav-disclosure").first().locator("summary").hover();
  await page.waitForFunction(
    () => document.querySelector(".nav-disclosure").open,
  );
  await page.mouse.move(5, 800);
  await page.waitForFunction(
    () => !document.querySelector(".nav-disclosure").open,
  );
  report.checks.push(
    "Fine-pointer hover opens the desktop panel; leaving it dismisses the panel.",
  );
  for (const label of ["Women", "Men", "Accessories"]) {
    const menu = page
      .locator(".nav-disclosure")
      .filter({ has: page.getByText(label, { exact: true }) });
    await menu.locator("summary").focus();
    await page.keyboard.press("Enter");
    await page.waitForFunction(
      () => document.querySelectorAll(".nav-disclosure[open]").length === 1,
    );
    await menu.locator("img").scrollIntoViewIfNeeded();
    await page.waitForFunction(() =>
      [...document.querySelectorAll(".nav-disclosure[open] img")].every(
        (img) => img.complete && img.naturalWidth > 0,
      ),
    );
    const scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    assert.deepEqual(
      scan.violations.map((v) => v.id),
      [],
    );
    await page.screenshot({
      path: path.join(output, `menu-${label.toLowerCase()}.png`),
    });
    await page.keyboard.press("Escape");
    assert.equal(await menu.evaluate((el) => el.open), false);
    assert.ok(
      await menu
        .locator("summary")
        .evaluate((el) => el === document.activeElement),
    );
  }
  report.checks.push(
    "Desktop panels: keyboard open, one panel at a time, real images, zero axe violations, Escape/focus return.",
  );
  await page.locator(".nav-disclosure").first().locator("summary").click();
  await page.locator(".campaign-caption").click();
  assert.equal(await page.locator(".nav-disclosure[open]").count(), 0);
  await page.locator(".nav-disclosure").first().locator("summary").click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForFunction(
    () => document.querySelectorAll(".nav-disclosure[open]").length === 0,
  );
  // Pending desktop hover timers must not reopen the panel after the breakpoint change.
  await page.waitForTimeout(250);
  assert.equal(await page.locator(".nav-disclosure[open]").count(), 0);
  report.checks.push(
    "Outside click and viewport changes dismiss desktop menus.",
  );

  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(base);
    const menu = page.locator(".mobile-nav");
    await menu.locator("summary").click();
    const scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    assert.deepEqual(
      scan.violations.map((v) => v.id),
      [],
    );
    await page.screenshot({
      path: path.join(output, `menu-mobile-${width}.png`),
    });
    await page.keyboard.press("Escape");
    assert.equal(await menu.evaluate((el) => el.open), false);
    const group = page.locator(".footer-group").first();
    assert.equal(await group.evaluate((el) => el.open), false);
    await group.locator("summary").click();
    assert.ok(
      await group.getByRole("link", { name: "Women", exact: true }).isVisible(),
    );
    await page.locator(".site-footer").scrollIntoViewIfNeeded();
    await page.screenshot({
      path: path.join(output, `footer-${width}.png`),
      fullPage: false,
    });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    );
  }
  report.checks.push(
    "320/390px mobile menu and footer accordions are operable and do not overflow.",
  );
  assert.deepEqual(errors, []);
  await context.close();

  const noJs = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 1000 },
  });
  const native = await noJs.newPage();
  await native.goto(base);
  const women = native.locator(".nav-disclosure").first();
  await women.locator("summary").click();
  await women.getByRole("link", { name: "Explore Women", exact: true }).click();
  await native.waitForURL("**/shop/women/");
  assert.equal(await native.locator("h1").innerText(), "Women");
  await native.goto(new URL("/collections/", base).href);
  assert.ok((await native.locator(".collection-cover img").count()) > 0);
  await native.locator(".collection-entry").first().click();
  assert.equal((await native.request.get(native.url())).status(), 200);
  report.checks.push(
    "Without JavaScript: desktop disclosure navigation and visual collections reach working catalog pages.",
  );
  await noJs.close();
  console.log(report.checks.join("\n"));
} finally {
  await writeFile(
    path.join(output, "storefront-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
