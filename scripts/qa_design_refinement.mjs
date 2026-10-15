/* Optional checks for the image expansion and the refined storefront controls. */
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
const baseUrl = process.env.MAISON_BASE_URL || "http://127.0.0.1:8000";
const output = path.resolve(
  process.env.MAISON_QA_OUTPUT || ".qa/design-refinement/chromium",
);
const browser = await chromium.launch({ headless: true });
const report = { checks: [] };
await mkdir(output, { recursive: true });
try {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  await page.goto(new URL("/shop/", baseUrl).href);
  assert.match(
    await page.locator(".catalog-count").textContent(),
    /Fictional products/,
  );
  assert.equal(await page.locator(".product-card").count(), 12);
  assert.equal(await page.locator(".catalog-story").count(), 1);
  await page.getByRole("link", { name: "Next page", exact: true }).click();
  assert.equal(await page.locator(".product-card").count(), 2);
  assert.equal(await page.locator(".catalog-story").count(), 0);
  report.checks.push(
    "Expanded catalog paginates 12/2; editorial feature appears only on the unfiltered first page.",
  );

  const slugs = [
    "wool-overshirt",
    "linen-shirt",
    "tailored-blazer",
    "merino-cardigan",
    "silk-midi-dress",
    "straight-wool-trouser",
    "twill-blouson",
    "pleated-midi-skirt",
    "merino-turtleneck",
    "brushed-wool-scarf",
  ];
  const photographs = new Set();
  for (const slug of slugs) {
    const response = await page.goto(
      new URL(`/products/${slug}/`, baseUrl).href,
    );
    assert.equal(response.status(), 200);
    const photo = page.locator(".product-gallery img").first();
    photographs.add(await photo.getAttribute("src"));
    await photo.scrollIntoViewIfNeeded();
    await page.waitForFunction(
      () => document.querySelector(".product-gallery img").naturalWidth > 0,
    );
    assert.ok(
      await page
        .getByRole("button", { name: "Add to demo bag", exact: true })
        .isEnabled(),
    );
  }
  assert.equal(photographs.size, 10);
  report.checks.push(
    "All ten new products have distinct loaded managed photographs and available demo variants.",
  );

  await page.goto(baseUrl);
  await page
    .getByRole("link", { name: "Search the collection", exact: true })
    .first()
    .click();
  assert.ok(
    await page.getByLabel("Search pieces", { exact: true }).isVisible(),
  );
  await page.getByLabel("Search pieces", { exact: true }).fill("merino");
  await page.getByRole("button", { name: "Apply filters" }).click();
  assert.equal(await page.locator(".product-card").count(), 2);
  assert.equal(await page.locator(".catalog-story").count(), 0);
  report.checks.push(
    "Search icon opens the functional form without JavaScript; new merino products are searchable.",
  );
  await page.getByRole("link", { name: "Shopping bag", exact: true }).click();
  assert.ok(
    await page
      .getByText("Your demo bag is empty.", { exact: false })
      .isVisible(),
  );
  await page
    .getByRole("navigation", { name: "Wardrobe guidance" })
    .getByRole("link", { name: /Find your fit/ })
    .click();
  await page.waitForURL("**/size-guide/");
  assert.equal(await page.locator("h1").innerText(), "Finding your fit.");
  report.checks.push(
    "Bag icon and footer guidance links reach real pages with JavaScript disabled.",
  );
  await context.close();

  const visual = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const preview = await visual.newPage();
  await preview.goto(new URL("/shop/", baseUrl).href);
  for (const width of [1440, 768, 390, 320]) {
    await preview.setViewportSize({ width, height: 1000 });
    const wordmark = await preview.locator(".wordmark").boundingBox();
    const controls = await preview.locator(".header-utilities").boundingBox();
    assert.ok(Math.abs(wordmark.x + wordmark.width / 2 - width / 2) < 1);
    assert.ok(wordmark.x + wordmark.width <= controls.x - 4);
  }
  report.checks.push(
    "Wordmark is visually centered at 1440/768/390/320px with no utility overlap.",
  );
  await preview.setViewportSize({ width: 1440, height: 1000 });
  await preview.locator(".site-footer").scrollIntoViewIfNeeded();
  await preview.screenshot({ path: path.join(output, "footer-desktop.png") });
  await visual.close();
  console.log(report.checks.join("\n"));
} finally {
  await writeFile(
    path.join(output, "refinement-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
