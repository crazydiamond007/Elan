/* Optional browser audit; dependencies stay outside application lockfiles. */
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
const output = path.resolve(".qa/flagship/chromium");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { browser: browser.version(), viewports: [] };
async function scan(page) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  assert.deepEqual(
    result.violations.map(({ id, nodes }) => ({
      id,
      targets: nodes.map((node) => node.target),
    })),
    [],
  );
}
try {
  for (const width of [1440, 1024, 768, 390, 320]) {
    const context = await browser.newContext({
      viewport: { width, height: 950 },
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    await page.goto(new URL("/products/sculpted-coat/", base).href, {
      waitUntil: "networkidle",
    });
    await page.evaluate(() => document.fonts.ready);
    assert.equal(
      await page.locator("[data-gallery-thumbnail]:visible").count(),
      4,
    );
    assert.equal(await page.locator("[data-gallery-photo]:visible").count(), 1);
    await page.getByRole("radio", { name: "M", exact: true }).check();
    assert.match(
      await page.locator("[data-availability]").innerText(),
      /Charcoal \/ M/,
    );
    assert.ok(
      await page
        .getByRole("radio", { name: "L — unavailable", exact: true })
        .isDisabled(),
    );
    await page.getByLabel("Quantity", { exact: true }).fill("99");
    assert.ok(
      await page
        .getByRole("button", { name: "Check quantity", exact: true })
        .isDisabled(),
    );
    await page.getByLabel("Quantity", { exact: true }).fill("1");
    assert.ok(
      await page
        .getByRole("button", { name: "Add to demo bag", exact: true })
        .isEnabled(),
    );
    await page.locator("[data-gallery-thumbnail]").nth(1).click();
    assert.equal(
      await page.locator("[data-gallery-counter]").innerText(),
      "2 / 4",
    );
    await page
      .locator("[data-gallery-photo]:visible img")
      .evaluate((img) => img.decode());
    await page.locator("[data-gallery-photo]:visible").click();
    await page.locator("[data-viewer-image]").evaluate((img) => img.decode());
    const fittedHeight = await page
      .locator("[data-viewer-image]")
      .evaluate((img) => img.height);
    await page
      .getByRole("button", { name: "View full size", exact: true })
      .click();
    assert.equal(
      await page.locator("[data-viewer-zoom]").getAttribute("aria-pressed"),
      "true",
    );
    assert.ok(
      (await page
        .locator("[data-viewer-image]")
        .evaluate((img) => img.height)) > fittedHeight,
    );
    assert.ok(
      await page
        .locator("[data-image-viewer] figure")
        .evaluate((el) => el === document.activeElement),
    );
    await page.keyboard.press("ArrowDown");
    await page.waitForFunction(
      () => document.querySelector("[data-image-viewer] figure").scrollTop > 0,
    );
    await page.keyboard.press("ArrowRight");
    assert.equal(
      await page.locator("[data-viewer-count]").innerText(),
      "2 / 4",
    );
    await scan(page);
    await page
      .getByRole("button", { name: "Fit to screen", exact: true })
      .click();
    if (width === 1440 || width === 390) {
      await page.screenshot({
        path: path.join(output, `enlarged-${width}.png`),
      });
    }
    await scan(page);
    for (let index = 0; index < 10; index++) {
      await page.keyboard.press("Tab");
      assert.ok(
        await page.evaluate(
          () => !!document.activeElement.closest("[data-image-viewer]"),
        ),
      );
    }
    await page.keyboard.press("ArrowRight");
    assert.equal(
      await page.locator("[data-viewer-count]").innerText(),
      "3 / 4",
    );
    await page.keyboard.press("Escape");
    await page.waitForFunction(
      () => !document.querySelector("[data-image-viewer]").open,
    );
    await page.waitForFunction(() =>
      document.activeElement.matches("[data-gallery-photo]:not([hidden])"),
    );
    assert.ok(
      await page
        .locator("[data-gallery-photo]:visible")
        .evaluate((el) => el === document.activeElement),
    );
    // Visit every thumbnail to verify the lazy-loaded images, including the macro detail.
    for (let index = 0; index < 4; index++) {
      await page.locator("[data-gallery-thumbnail]").nth(index).click();
      await page
        .locator("[data-gallery-photo]:visible img")
        .evaluate((img) => img.decode());
    }
    await page.locator("[data-gallery-thumbnail]").first().click();
    for (const thumbnail of await page
      .locator("[data-gallery-thumbnail] img")
      .all()) {
      await thumbnail.scrollIntoViewIfNeeded();
      await thumbnail.evaluate((img) => img.decode());
    }
    await scan(page);
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    );
    await page
      .locator(".product-layout")
      .screenshot({ path: path.join(output, `flagship-${width}.png`) });
    assert.deepEqual(errors, []);
    report.viewports.push({
      width,
      gallery: 4,
      selection: "passed",
      modalKeyboard: "passed",
      axeViolations: 0,
    });
    await context.close();
    console.log(
      `Flagship ${width}px: selection, four images, modal keyboard/focus and axe passed`,
    );
  }
} finally {
  await writeFile(
    path.join(output, "flagship-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
