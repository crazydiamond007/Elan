/* Optional browser QA; tooling is installed outside the application. */
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
const report = { browser: browser.version(), pages: [], checks: [] };
try {
  for (const width of [1440, 1024, 768, 390, 320]) {
    const context = await browser.newContext({
      viewport: { width, height: width < 768 ? 844 : 1000 },
    });
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
      assert.equal(new URL(request.url()).origin, new URL(baseUrl).origin);
    });
    for (const route of [
      "/shop/",
      "/products/sculpted-coat/",
      "/collections/",
    ]) {
      const response = await page.goto(new URL(route, baseUrl).href, {
        waitUntil: "networkidle",
      });
      assert.equal(response.status(), 200);
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
        `Overflow at ${width}px on ${route}`,
      );
      const result = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze();
      report.pages.push({
        width,
        route,
        violations: result.violations.map(({ id, nodes }) => ({
          id,
          targets: nodes.map((node) => node.target),
        })),
      });
      assert.equal(
        result.violations.length,
        0,
        `Accessibility violations at ${width}px on ${route}`,
      );
      await page.screenshot({
        path: path.join(output, `${route.split("/")[1]}-${width}.png`),
        fullPage: true,
      });
    }
    assert.deepEqual(errors, []);
    await context.close();
    console.log(
      `Catalog, product and collections at ${width}px: images loaded, no overflow or axe violations`,
    );
  }
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  await page.goto(new URL("/shop/?q=coat", baseUrl).href);
  await page.getByRole("link", { name: /The Sculpted Wool Coat/ }).click();
  await page.waitForURL("**/products/sculpted-coat/");
  assert.ok(
    await page.getByRole("button", { name: "Add to demo bag" }).isEnabled(),
  );
  await page.getByLabel("Size", { exact: true }).selectOption("l");
  await page.getByRole("button", { name: "Update selection" }).click();
  await page.waitForURL("**/products/sculpted-coat/");
  assert.match(
    await page.locator(".availability").innerText(),
    /currently unavailable/,
  );
  await page.getByLabel("Size", { exact: true }).selectOption("m");
  await page.getByLabel("Quantity", { exact: true }).fill("2");
  await page.getByRole("button", { name: "Update selection" }).click();
  assert.match(
    await page.locator(".availability").innerText(),
    /Available in the demo catalog/,
  );
  assert.match(await page.locator(".detail-price").innerText(), /€320.00/);
  await page
    .locator(".product-disclosures summary")
    .filter({ hasText: "Care" })
    .click();
  assert.ok(
    await page
      .locator(".product-disclosures")
      .getByText(/follow the care label/)
      .isVisible(),
  );
  report.checks.push(
    "No-JavaScript journey: catalog → detail → unavailable size → available size and quantity → native care disclosure; demo bag is enabled only for available selections",
  );
  await context.close();
  const errorContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const errorPage = await errorContext.newPage();
  const invalid = await errorPage.goto(
    new URL(
      "/products/sculpted-coat/?color=charcoal&size=m&quantity=99",
      baseUrl,
    ).href,
  );
  assert.equal(invalid.status(), 400);
  assert.ok(await errorPage.getByRole("alert").isVisible());
  const errorAxe = await new AxeBuilder({ page: errorPage })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  assert.equal(
    errorAxe.violations.length,
    0,
    JSON.stringify(errorAxe.violations.map(({ id }) => id)),
  );
  await errorPage.screenshot({
    path: path.join(output, "selection-error-390.png"),
    fullPage: true,
  });
  report.checks.push(
    "Invalid selection: HTTP 400, visible error summary and no axe violations",
  );
  await errorContext.close();
} finally {
  await writeFile(
    path.join(output, "catalog-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
