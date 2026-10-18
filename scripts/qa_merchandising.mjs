/* Optional local browser QA; no application dependency or production submissions. */
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
const output = path.resolve(
  process.env.MAISON_QA_OUTPUT || ".qa/merchandising/chromium",
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = { browser: browser.version(), checks: [], accessibility: [] };

async function scan(page, name) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  const violations = result.violations.map(({ id, nodes }) => ({
    id,
    targets: nodes.map(({ target }) => target),
  }));
  report.accessibility.push({ name, violations });
  assert.deepEqual(violations, []);
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
    `Overflow: ${name}`,
  );
}

async function alternateVisible(page, visible) {
  await page.waitForFunction(
    (expected) =>
      Number(
        getComputedStyle(document.querySelector(".product-media-secondary"))
          .opacity,
      ) === Number(expected),
    visible,
  );
}

try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400)
      errors.push(`${response.status()} ${response.url()}`);
  });
  await page.goto(new URL("/shop/?q=coat", base).href);
  await page.locator(".product-link").hover();
  await alternateVisible(page, true);
  await page.mouse.move(0, 0);
  await alternateVisible(page, false);
  await page.locator(".product-link").focus();
  await alternateVisible(page, true);
  await page.keyboard.press("Tab");
  assert.ok(
    await page
      .locator("[data-card-preview]")
      .evaluate((el) => el === document.activeElement),
  );
  await page.keyboard.press("Space");
  assert.equal(
    await page.locator("[data-card-preview]").getAttribute("aria-pressed"),
    "true",
  );
  await scan(page, "Desktop card keyboard preview");
  report.checks.push(
    "Alternate product photograph works on hover, link focus and keyboard toggle.",
  );

  await page.goto(new URL("/collections/", base).href);
  assert.equal(await page.locator(".collection-cover img").count(), 2);
  await page.locator(".collection-entry").first().click();
  assert.equal(await page.locator(".collection-intro-image img").count(), 1);
  await scan(page, "Image-led collection detail desktop");
  await page.screenshot({
    path: path.join(output, "collection-detail-1440.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 320, height: 800 });
  await scan(page, "Image-led collection detail mobile");
  report.checks.push(
    "Managed collection photographs link to image-led collection details at desktop and mobile sizes.",
  );

  for (const slug of [
    "fine-wool-knit",
    "everyday-tote",
    "wool-overshirt",
    "tailored-blazer",
    "merino-cardigan",
    "sculpted-coat",
  ]) {
    await page.goto(new URL(`/products/${slug}/`, base).href);
    assert.equal(
      await page.locator("[data-gallery-thumbnail]:visible").count(),
      4,
    );
    for (const thumbnail of await page
      .locator("[data-gallery-thumbnail]")
      .all()) {
      await thumbnail.click();
      await page
        .locator("[data-gallery-photo]:visible img")
        .evaluate((img) => img.decode());
    }
    await page.locator("[data-gallery-thumbnail]").first().click();
    await scan(page, `${slug} four-view gallery at 320px`);
  }
  report.checks.push(
    "All six signature galleries expose four working photographs.",
  );

  await page.goto(base);
  assert.equal(await page.locator(".footer-group[open]").count(), 0);
  const firstSummary = page.locator(".footer-group > summary").first();
  await firstSummary.focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(".footer-group[open]").count(), 1);
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "New arrivals");
  await scan(page, "Expanded mobile footer");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.waitForFunction(
    () => document.querySelectorAll(".footer-group[open]").length === 4,
  );
  await page.locator(".campaign-editorial").screenshot({
    path: path.join(output, "campaign-1440.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForFunction(
    () => document.querySelectorAll(".footer-group[open]").length === 0,
  );
  assert.ok(await firstSummary.evaluate((el) => el === document.activeElement));
  await page.locator(".campaign-editorial").screenshot({
    path: path.join(output, "campaign-390.png"),
  });
  await page.locator(".site-footer").screenshot({
    path: path.join(output, "footer-390.png"),
  });
  report.checks.push(
    "Mobile footer expands by keyboard; desktop groups open and resizing restores focus safely.",
  );

  await page.goto(new URL("/products/sculpted-coat/", base).href);
  await page.getByRole("radio", { name: "M", exact: true }).check();
  await page.getByLabel("Quantity", { exact: true }).fill("2");
  await page
    .getByRole("button", { name: "Add to demo bag", exact: true })
    .click();
  await page.waitForURL("**/bag/");
  assert.match(
    await page.locator(".bag-added").innerText(),
    /The Sculpted Wool Coat · Charcoal \/ M · Quantity 2/,
  );
  assert.equal(await page.locator(".bag-count").innerText(), "2");
  await scan(page, "Detailed added-item confirmation");
  await page.goto(base);
  assert.equal(await page.locator(".bag-count").innerText(), "2");
  await page.getByRole("link", { name: "Shopping bag", exact: true }).click();
  await page
    .getByRole("button", { name: "Remove The Sculpted Wool Coat", exact: true })
    .click();
  assert.equal(await page.locator(".bag-count").count(), 0);
  report.checks.push(
    "Bag badge persists across navigation and clears on removal; confirmation identifies the chosen product, colour, size and quantity.",
  );
  assert.deepEqual(errors, []);
  await context.close();

  const touch = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  const touchPage = await touch.newPage();
  await touchPage.goto(new URL("/shop/?q=coat", base).href);
  await touchPage.locator("[data-card-preview]").tap();
  assert.equal(
    await touchPage.locator("[data-card-preview]").getAttribute("aria-pressed"),
    "true",
  );
  await alternateVisible(touchPage, true);
  await touchPage.locator("[data-card-preview]").tap();
  assert.equal(
    await touchPage.locator("[data-card-preview]").getAttribute("aria-pressed"),
    "false",
  );
  await alternateVisible(touchPage, false);
  await scan(touchPage, "Touch photo preview");
  report.checks.push(
    "Touch control alternates photos without navigating away from the catalog.",
  );
  await touch.close();

  const noJs = await browser.newContext({
    viewport: { width: 390, height: 844 },
    javaScriptEnabled: false,
  });
  const plain = await noJs.newPage();
  await plain.goto(base);
  assert.equal(await plain.locator(".footer-group[open]").count(), 4);
  assert.equal(await plain.locator("[data-card-preview]:visible").count(), 0);
  assert.equal(await plain.locator(".campaign-editorial img").count(), 1);
  const campaign = await plain
    .locator(".campaign-editorial img")
    .getAttribute("src");
  assert.notEqual(
    campaign,
    await plain.locator(".category-card img").first().getAttribute("src"),
  );
  report.checks.push(
    "Without JavaScript, footer destinations remain visible and cards link normally; the campaign uses a distinct managed photograph.",
  );
  await noJs.close();
  await writeFile(
    path.join(output, "merchandising-report.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser.close();
}
