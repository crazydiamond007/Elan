/* Optional QA for the screenshot-led header, native dialog drawers and footer. */
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
  process.env.MAISON_QA_OUTPUT || ".qa/search-panel/chromium",
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = {
  browser: browser.version(),
  viewports: [],
  contextualSearch: [],
  checks: [],
};
try {
  for (const [width, height] of [
    [1920, 1080],
    [1912, 840],
    [1440, 900],
    [1366, 768],
    [1280, 600],
    [1024, 768],
    [768, 1024],
    [390, 844],
    [375, 667],
    [320, 568],
    [844, 390],
    [667, 375],
    [560, 420],
    [480, 360],
    [430, 400],
    [320, 480],
  ]) {
    const context = await browser.newContext({
      viewport: { width, height },
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    await page.goto(base, { waitUntil: "networkidle" });
    const logo = await page.locator(".wordmark").boundingBox();
    const utilities = await page.locator(".header-utilities").boundingBox();
    assert.ok(
      Math.abs(logo.x + logo.width / 2 - width / 2) < 1,
      "Centered wordmark",
    );
    assert.ok(
      logo.x + logo.width <= utilities.x - 4,
      "Logo and controls do not overlap",
    );
    const menu = page.locator(".mobile-nav > summary");
    await menu.click();
    await page.waitForFunction(
      () => document.getElementById("navigation-dialog")?.open,
    );
    for (let tab = 0; tab < 15; tab++) {
      await page.keyboard.press("Tab");
      assert.ok(
        await page.evaluate(
          () => !!document.activeElement.closest("#navigation-dialog"),
        ),
        "Menu focus must stay in its modal.",
      );
    }
    let scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    assert.deepEqual(
      scan.violations.map((v) => ({
        id: v.id,
        targets: v.nodes.map((n) => n.target),
      })),
      [],
    );
    await page.screenshot({
      path: path.join(output, `navigation-${width}.png`),
    });
    await page.keyboard.press("Escape");
    await page.waitForFunction(
      () => !document.getElementById("navigation-dialog").open,
    );
    assert.ok(await menu.evaluate((el) => document.activeElement === el));

    const searchLink = page.locator(".header-utilities .search-link");
    await searchLink.click();
    await page.waitForFunction(
      () => document.getElementById("search-dialog").open,
    );
    assert.equal(
      await page.locator(":focus").getAttribute("id"),
      "drawer-query",
    );
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(() =>
      [...document.querySelectorAll("#search-dialog img")].every(
        (img) => img.complete && img.naturalWidth > 0,
      ),
    );
    const geometry = await page.locator("#search-dialog").evaluate((dialog) => {
      const bounds = dialog.getBoundingClientRect();
      const sections = [
        ".drawer-search-form",
        ".search-suggestions",
        ".search-discover",
      ].map((selector) =>
        dialog.querySelector(selector).getBoundingClientRect(),
      );
      return {
        scrollHeight: dialog.scrollHeight,
        clientHeight: dialog.clientHeight,
        scrollWidth: dialog.scrollWidth,
        clientWidth: dialog.clientWidth,
        top: bounds.top,
        bottom: bounds.bottom,
        rightGap: innerWidth - bounds.right,
        cornerRadius: parseFloat(getComputedStyle(dialog).borderTopRightRadius),
        sharedLeftEdge: sections.every(
          (box) => Math.abs(box.left - sections[0].left) < 1,
        ),
        stacked:
          sections[1].top > sections[0].bottom &&
          sections[2].top > sections[1].bottom,
        contentVisible: [
          ...dialog.querySelectorAll(
            ".drawer-search-form, .search-suggestions a, .search-recommendations a",
          ),
        ].every((element) => {
          const box = element.getBoundingClientRect();
          return box.top >= bounds.top && box.bottom <= bounds.bottom;
        }),
      };
    });
    assert.ok(
      geometry.scrollHeight <= geometry.clientHeight + 1,
      `Search requires scrolling at ${width}×${height}: ${JSON.stringify(geometry)}`,
    );
    assert.ok(geometry.scrollWidth <= geometry.clientWidth + 1);
    assert.ok(geometry.top > 0 && geometry.bottom < height);
    assert.ok(
      geometry.rightGap > 0 && geometry.cornerRadius === 8,
      "Search must have visible outer spacing and rounded corners.",
    );
    assert.ok(
      geometry.sharedLeftEdge && geometry.stacked,
      "Search, suggestions and recommendations must stack with a shared left edge.",
    );
    assert.ok(
      geometry.contentVisible,
      `All search content must be visible at ${width}×${height}`,
    );
    for (let tab = 0; tab < 15; tab++) {
      await page.keyboard.press("Tab");
      assert.ok(
        await page.evaluate(
          () => !!document.activeElement.closest("#search-dialog"),
        ),
        "Search focus must stay in its modal.",
      );
    }
    await page.locator("#drawer-query").focus();
    scan = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    assert.deepEqual(
      scan.violations.map((v) => ({
        id: v.id,
        targets: v.nodes.map((n) => n.target),
      })),
      [],
    );
    await page.screenshot({ path: path.join(output, `search-${width}.png`) });
    await page.locator("#search-dialog [data-close-drawer]").click();
    await page.waitForFunction(
      () => !document.getElementById("search-dialog").open,
    );
    assert.ok(await searchLink.evaluate((el) => document.activeElement === el));
    await searchLink.click();
    await page
      .getByRole("searchbox", { name: "Search the collection", exact: true })
      .fill("coat");
    await page.getByRole("button", { name: "Submit search" }).click();
    await page.waitForURL("**/shop/?q=coat");
    assert.equal(
      await page.locator(".catalog-grid > .product-card").count(),
      1,
    );
    await page.goto(base);
    assert.equal(await page.locator(".footer-wordmark").count(), 0);
    assert.equal(await page.locator(".maison-link").count(), 0);
    assert.equal(await page.locator(".site-footer form").count(), 1);
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    );
    await page
      .locator(".site-footer")
      .screenshot({ path: path.join(output, `footer-${width}.png`) });
    assert.deepEqual(errors, []);
    report.viewports.push({
      width,
      height,
      geometry,
      navigation: "passed",
      search: "passed",
      focus: "passed",
      axeViolations: 0,
    });
    await context.close();
    console.log(
      `${width}×${height}: search fits without scrolling; menu/search focus, images, results, footer and axe passed.`,
    );
  }
  const contextual = await browser.newContext();
  const contextualPage = await contextual.newPage();
  for (const [width, height] of [
    [1440, 900],
    [1280, 600],
    [390, 844],
    [320, 568],
    [667, 375],
  ]) {
    await contextualPage.setViewportSize({ width, height });
    for (const route of [
      "/products/sculpted-coat/",
      "/our-story/",
      "/shop/?q=nonexistent",
    ]) {
      await contextualPage.goto(new URL(route, base).href);
      await contextualPage.locator(".header-utilities .search-link").click();
      await contextualPage.evaluate(() => document.fonts.ready);
      await contextualPage.waitForFunction(() =>
        [...document.querySelectorAll("#search-dialog img")].every(
          (img) => img.complete && img.naturalWidth > 0,
        ),
      );
      assert.ok(
        await contextualPage
          .locator("#search-dialog")
          .evaluate((dialog) => dialog.scrollHeight <= dialog.clientHeight + 1),
        `Contextual search requires scrolling at ${width}×${height} on ${route}`,
      );
      report.contextualSearch.push({ width, height, route, fits: true });
    }
  }
  await contextual.close();
  const reflow = await browser.newContext({
    viewport: { width: 320, height: 256 },
  });
  const reflowPage = await reflow.newPage();
  await reflowPage.goto(base);
  await reflowPage.locator(".header-utilities .search-link").click();
  const last = reflowPage.locator(".search-recommendations a").last();
  for (let tab = 0; tab < 12; tab++) {
    if (await last.evaluate((element) => element === document.activeElement))
      break;
    await reflowPage.keyboard.press("Tab");
  }
  assert.ok(
    await last.evaluate((element) => element === document.activeElement),
  );
  assert.ok(
    await reflowPage
      .locator("#search-dialog")
      .evaluate((dialog) => dialog.scrollTop > 0),
  );
  assert.ok(
    await reflowPage.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  );
  await reflowPage.keyboard.press("Escape");
  await reflowPage.waitForFunction(
    () => !document.getElementById("search-dialog").open,
  );
  report.checks.push(
    "At a 320×256px reflow viewport, internal scrolling keeps every control reachable by keyboard and Escape closes the search.",
  );
  await reflow.close();
  const noJs = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 950 },
  });
  const page = await noJs.newPage();
  await page.goto(base);
  await page.locator(".mobile-nav > summary").click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Women", exact: true })
    .click();
  await page.waitForURL("**/shop/women/");
  await page.locator(".header-utilities .search-link").click();
  assert.ok(
    await page.getByLabel("Search pieces", { exact: true }).isVisible(),
  );
  report.checks.push(
    "Without JavaScript, native menu and search link navigate to functional server-rendered pages.",
  );
  await noJs.close();
} finally {
  await writeFile(
    path.join(output, "drawer-report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
