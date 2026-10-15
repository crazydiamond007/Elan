/* Optional local lab measurements. Lighthouse lives outside application dependencies. */
import { createRequire } from "node:module";
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";

const require = createRequire(
  path.join(
    process.env.MAISON_QA_DIR || "/tmp/maison-elan-browser",
    "package.json",
  ),
);
const { chromium } = require("playwright");
const lighthouse = (await import(require.resolve("lighthouse"))).default;
const desktopConfig = (
  await import(require.resolve("lighthouse/core/config/desktop-config.js"))
).default;
const baseUrl = process.env.MAISON_BASE_URL || "http://127.0.0.1:8000";
const output = path.resolve(
  ".qa/phase-6/lighthouse",
  process.env.MAISON_AUDIT_LABEL || "final",
);
await mkdir(output, { recursive: true });
const routes = (
  process.env.MAISON_AUDIT_ROUTES || "/,/shop/,/products/sculpted-coat/"
).split(",");
const summary = [];
async function launchNativeChrome() {
  const profile = await mkdtemp("/tmp/maison-lighthouse-");
  const process = spawn(
    chromium.executablePath(),
    [
      "--headless",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--remote-debugging-port=0",
      "--remote-debugging-address=127.0.0.1",
      `--user-data-dir=${profile}`,
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  const port = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      process.kill();
      reject(new Error("Native Chromium startup timed out"));
    }, 15000);
    process.once("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    process.once("exit", () => {
      clearTimeout(timeout);
      reject(new Error("Native Chromium exited before startup"));
    });
    process.stderr.on("data", (chunk) => {
      const match = chunk
        .toString()
        .match(/DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)/);
      if (match) {
        clearTimeout(timeout);
        resolve(Number(match[1]));
      }
    });
  });
  return {
    port,
    async kill() {
      if (process.exitCode === null) {
        process.kill();
        await once(process, "exit");
      }
    },
  };
}
for (const route of routes) {
  for (const preset of ["mobile", "desktop"]) {
    const chrome = await launchNativeChrome();
    try {
      const options = {
        port: chrome.port,
        output: ["json", "html"],
        logLevel: "error",
        onlyCategories: [
          "performance",
          "accessibility",
          "best-practices",
          "seo",
        ],
      };
      const result = await lighthouse(
        new URL(route, baseUrl).href,
        options,
        preset === "desktop" ? desktopConfig : undefined,
      );
      assert.equal(
        result.lhr.configSettings.formFactor,
        preset,
        "Measured configuration must match the report label",
      );
      const name =
        route === "/" ? "home" : route.split("/").filter(Boolean).join("-");
      await writeFile(
        path.join(output, `${name}-${preset}.json`),
        result.report[0],
      );
      await writeFile(
        path.join(output, `${name}-${preset}.html`),
        result.report[1],
      );
      const { lhr } = result;
      const entry = {
        route,
        preset,
        lighthouse: lhr.lighthouseVersion,
        time: lhr.fetchTime,
        scores: Object.fromEntries(
          Object.entries(lhr.categories).map(([key, value]) => [
            key,
            Math.round(value.score * 100),
          ]),
        ),
        metrics: Object.fromEntries(
          [
            "first-contentful-paint",
            "largest-contentful-paint",
            "total-blocking-time",
            "cumulative-layout-shift",
            "speed-index",
          ].map((key) => [key, lhr.audits[key]?.numericValue]),
        ),
        findings: Object.entries(lhr.audits)
          .filter(([, value]) => value.score !== null && value.score < 1)
          .map(([id, value]) => ({
            id,
            title: value.title,
            score: value.score,
            display: value.displayValue,
          })),
      };
      summary.push(entry);
      console.log(JSON.stringify(entry));
    } finally {
      await chrome.kill();
    }
  }
}
await writeFile(
  path.join(output, "summary.json"),
  JSON.stringify(summary, null, 2) + "\n",
);
