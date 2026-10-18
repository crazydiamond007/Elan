/* Optional browser QA; all submissions use the local fictional demonstration. */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { recordConsole } from "./qa_console.mjs";

const require = createRequire(
  path.join(
    process.env.MAISON_QA_DIR || "/tmp/maison-elan-browser",
    "package.json",
  ),
);
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
  checks: [],
  httpOriginNotices: [],
};

async function inspect(page, name, width) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    for (
      let top = 0;
      top < document.documentElement.scrollHeight;
      top += innerHeight
    ) {
      window.scrollTo({ top, behavior: "instant" });
      await new Promise((resolve) => setTimeout(resolve, 100));
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
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
    `Overflow at ${width}px: ${name}`,
  );
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  report.viewports.push({
    width,
    name,
    violations: result.violations.map(({ id, nodes }) => ({
      id,
      targets: nodes.map((node) => node.target),
    })),
  });
  assert.equal(
    result.violations.length,
    0,
    JSON.stringify(report.viewports.at(-1)),
  );
  await page.screenshot({
    path: path.join(output, `${name}-${width}.png`),
    fullPage: true,
  });
}

try {
  for (const width of [1440, 1024, 768, 390, 320]) {
    const context = await browser.newContext({
      viewport: { width, height: width < 768 ? 844 : 1000 },
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      recordConsole(message, errors, report.httpOriginNotices, baseUrl);
    });
    page.on("response", (response) => {
      if (response.status() >= 400)
        errors.push(`${response.status()} ${response.url()}`);
    });
    page.on("request", (request) => {
      assert.equal(new URL(request.url()).origin, new URL(baseUrl).origin);
    });
    await page.goto(new URL("/bag/", baseUrl).href);
    await inspect(page, "empty-bag", width);
    await page.goto(new URL("/products/sculpted-coat/", baseUrl).href);
    await page.getByRole("radio", { name: "M", exact: true }).check();
    await page.getByLabel("Quantity", { exact: true }).fill("2");
    await page
      .getByRole("button", { name: "Add to demo bag", exact: true })
      .click();
    await page.waitForURL("**/bag/");
    assert.match(await page.locator(".summary-total").innerText(), /€640.00/);
    await inspect(page, "bag", width);
    await page.getByRole("link", { name: "Continue to demo checkout" }).click();
    await page.waitForURL("**/checkout/");
    assert.equal(
      await page.getByRole("heading", { level: 1 }).innerText(),
      "Demo checkout",
    );
    assert.equal(
      await page.locator('main input:not([type="hidden"])').count(),
      1,
    );
    await inspect(page, "checkout", width);
    assert.deepEqual(errors, []);
    await context.close();
    console.log(
      `Empty bag, populated bag and checkout at ${width}px: no overflow, errors or axe violations`,
    );
  }

  const noJs = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 390, height: 844 },
  });
  const page = await noJs.newPage();
  await page.goto(new URL("/shop/", baseUrl).href);
  await page.locator("#catalog-filters > summary").click();
  await page.getByLabel("Search pieces", { exact: true }).fill("coat");
  await page.getByLabel("Size", { exact: true }).selectOption("m");
  await page.getByLabel("Colour", { exact: true }).selectOption("charcoal");
  await page.getByLabel("Sort by", { exact: true }).selectOption("price-asc");
  await page.getByRole("button", { name: "Apply filters" }).click();
  assert.equal(await page.locator(".product-card").count(), 1);
  await page.getByRole("link", { name: /The Sculpted Wool Coat/ }).click();
  await page.getByLabel("Size", { exact: true }).selectOption("m");
  await page.getByLabel("Quantity", { exact: true }).fill("2");
  await page
    .getByRole("button", { name: "Add to demo bag", exact: true })
    .click();
  await page.waitForURL("**/bag/");
  await page
    .getByLabel("Quantity for The Sculpted Wool Coat", { exact: true })
    .fill("1");
  await page
    .getByRole("button", { name: "Update The Sculpted Wool Coat", exact: true })
    .click();
  assert.match(await page.locator(".summary-total").innerText(), /€320.00/);
  await page
    .getByRole("button", { name: "Remove The Sculpted Wool Coat", exact: true })
    .click();
  assert.ok(
    await page
      .getByText("Your demo bag is empty.", { exact: false })
      .isVisible(),
  );
  await page.goto(new URL("/products/pleated-trouser/", baseUrl).href);
  await page.getByLabel("Size", { exact: true }).selectOption("m");
  await page
    .getByRole("button", { name: "Add to demo bag", exact: true })
    .click();
  await page.getByRole("link", { name: "Continue to demo checkout" }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Complete demo checkout" }).click();
  await page.waitForURL("**/checkout/confirmation/**");
  const confirmationUrl = page.url();
  assert.ok(
    await page
      .getByText(/No payment was taken, no real order was placed/)
      .isVisible(),
  );
  assert.match(
    await page.locator(".confirmation-total").innerText(),
    /€160.00/,
  );
  await page.goto(new URL("/bag/", baseUrl).href);
  assert.ok(
    await page
      .getByText("Your demo bag is empty.", { exact: false })
      .isVisible(),
  );
  report.checks.push(
    "No-JavaScript journey: search/filter/sort → product → add → update → remove → sale product → demo checkout → confirmation → empty bag",
  );
  await noJs.close();

  const outsider = await browser.newContext();
  const denied = await (await outsider.newPage()).goto(confirmationUrl);
  assert.equal(denied.status(), 404);
  report.checks.push("Confirmation URL returns 404 in another session");
  await outsider.close();

  const formContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const formPage = await formContext.newPage();
  await formPage.goto(new URL("/newsletter/", baseUrl).href);
  await formPage
    .getByLabel("Demo email address", { exact: true })
    .fill("browser-qa@example.com");
  await formPage.getByRole("button", { name: "Try demo signup" }).click();
  assert.ok(
    await formPage
      .getByText("Your demo signup was saved locally. No email will be sent.")
      .isVisible(),
  );
  await inspect(formPage, "newsletter-success", 390);
  await formPage
    .getByLabel("Demo email address", { exact: true })
    .fill("person@gmail.com");
  const rejected = formPage.waitForResponse(
    (response) =>
      response.url().endsWith("/newsletter/") &&
      response.request().method() === "POST",
  );
  await formPage.getByRole("button", { name: "Try demo signup" }).click();
  assert.equal((await rejected).status(), 400);
  assert.ok(await formPage.getByRole("alert").isVisible());
  await inspect(formPage, "newsletter-error", 390);
  report.checks.push(
    "Fictional newsletter signup succeeds locally; real-address submission returns 400 with feedback",
  );
  await formPage.goto(
    new URL("/shop/?min_price=300&max_price=10", baseUrl).href,
  );
  assert.ok(await formPage.getByRole("alert").isVisible());
  await inspect(formPage, "filter-error", 390);
  await formPage.goto(confirmationUrl);
  assert.equal((await formPage.request.get(confirmationUrl)).status(), 404);
  await formContext.close();
} finally {
  await writeFile(
    path.join(output, "shopping-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
