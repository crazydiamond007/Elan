/* Invoked against pytest's disposable live server; never creates a local/production administrator. */
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
const baseUrl = process.env.MAISON_BASE_URL;
assert.ok(
  baseUrl && process.env.MAISON_ADMIN_USER && process.env.MAISON_ADMIN_PASSWORD,
);
const browser = await chromium.launch({ headless: true });
const output = path.resolve(".qa/phase-6/admin");
await mkdir(output, { recursive: true });
const report = { pages: [], checks: [] };
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  const errors = [];
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (event) => {
      console.error(
        JSON.stringify({
          source: event.sourceFile,
          line: event.lineNumber,
          directive: event.violatedDirective,
        }),
      );
    });
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400)
      errors.push(`${response.status()} ${response.url()}`);
  });
  page.on("request", (request) =>
    assert.equal(new URL(request.url()).origin, new URL(baseUrl).origin),
  );
  await page.goto(new URL("/admin/login/", baseUrl).href);
  await page.locator("#id_username").fill(process.env.MAISON_ADMIN_USER);
  await page.locator("#id_password").fill(process.env.MAISON_ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await page.waitForURL("**/admin/");
  for (const route of [
    "/admin/",
    "/admin/catalog/product/",
    `/admin/catalog/product/${process.env.MAISON_PRODUCT_ID}/change/`,
  ]) {
    await page.goto(new URL(route, baseUrl).href, { waitUntil: "networkidle" });
    // Only axe's audit-created style elements receive the existing response nonce.
    // The application's CSP remains unchanged.
    await page.evaluate(() => {
      const nonce = document.querySelector("link[nonce]").nonce;
      const original = Document.prototype.createElement;
      window.restoreAuditStyles = () => {
        Document.prototype.createElement = original;
      };
      Document.prototype.createElement = function (name, ...args) {
        const element = original.call(this, name, ...args);
        if (String(name).toLowerCase() === "style") element.nonce = nonce;
        return element;
      };
    });
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
      .analyze();
    await page.evaluate(() => {
      window.restoreAuditStyles();
      delete window.restoreAuditStyles;
    });
    report.pages.push({
      route,
      violations: result.violations.map(({ id, nodes }) => ({
        id,
        targets: nodes.map((node) => node.target),
      })),
    });
    assert.equal(
      result.violations.length,
      0,
      JSON.stringify(report.pages.at(-1)),
    );
  }
  await page
    .locator("#id_description")
    .fill("Reviewed by isolated browser QA. Fictional product.");
  await page.locator('input[name="_save"]').click();
  await page.waitForURL("**/admin/catalog/product/");
  assert.ok(await page.locator(".messagelist").isVisible());
  await page.goto(new URL("/admin/catalog/variant/", baseUrl).href);
  const stock = page.locator('input[name^="form-"][name$="-stock"]').first();
  await stock.fill("3");
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await page
    .locator(".messagelist")
    .waitFor({ state: "visible", timeout: 5000 });
  await page.goto(
    new URL(
      `/admin/catalog/product/${process.env.MAISON_PRODUCT_ID}/change/`,
      baseUrl,
    ).href,
  );
  await page
    .locator("#id_images-0-image")
    .setInputFiles(process.env.MAISON_IMAGE_PATH);
  await page.locator('input[name="_save"]').click();
  await page.waitForURL("**/admin/catalog/product/");
  assert.ok(await page.locator(".messagelist").isVisible());
  report.checks.push(
    "Staff login, product editing, inline inventory editing and image replacement succeeded with strict CSP",
  );
  await page.screenshot({
    path: path.join(output, "product-admin.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  assert.ok(
    await page
      .getByRole("heading", { name: "Logged out", exact: true })
      .isVisible(),
  );
  report.checks.push("POST logout succeeded");
  assert.deepEqual(errors, []);
} finally {
  await writeFile(
    path.join(output, "report.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
  await browser.close();
}
