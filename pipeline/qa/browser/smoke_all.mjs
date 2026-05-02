// Smoke-load every episode in headless: just open the page and collect 4xx/5xx
// responses + console errors. No walking. Fast pre-flight before manual QA.
//
// Usage: node smoke_all.mjs                  (all 36)
//        node smoke_all.mjs 1-12             (range)
//        node smoke_all.mjs 1,5,12           (list)

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, TOTAL_EPISODES, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const reportsDir = path.join(__dirname, "reports");
await fs.mkdir(reportsDir, { recursive: true });

function parseEpisodes(arg) {
  if (!arg) return Array.from({ length: TOTAL_EPISODES }, (_, i) => i + 1);
  if (arg.includes("-")) {
    const [a, b] = arg.split("-").map((n) => parseInt(n, 10));
    return Array.from({ length: b - a + 1 }, (_, i) => a + i);
  }
  return arg.split(",").map((n) => parseInt(n, 10));
}

const eps = parseEpisodes(process.argv[2]);
console.log(`[smoke] checking ${eps.length} episodes: ${eps.join(",")}`);

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: VIEWPORT, locale: "uk-UA" });

const summary = [];
for (const ep of eps) {
  const url = EPISODE_URL(ep);
  const page = await ctx.newPage();
  const httpErrors = [];
  const consoleErrors = [];

  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));
  page.on("requestfailed", (req) => httpErrors.push({ url: req.url(), err: req.failure()?.errorText }));
  page.on("response", (res) => {
    if (res.status() >= 400) httpErrors.push({ status: res.status(), url: res.url() });
  });

  const started = Date.now();
  try {
    await page.goto(url, { waitUntil: "load", timeout: 45000 });
    await page.waitForTimeout(2000); // let lazy assets fire
  } catch (e) {
    consoleErrors.push(`goto failed: ${e.message}`);
  }
  const ms = Date.now() - started;

  const result = { ep, url, ms, httpErrors: httpErrors.length, consoleErrors: consoleErrors.length, details: { httpErrors, consoleErrors } };
  summary.push(result);
  await page.close();

  const flag = (httpErrors.length || consoleErrors.length) ? "FAIL" : "ok";
  console.log(`  ep_${String(ep).padStart(3, "0")} ${flag.padEnd(4)} ${ms}ms  http=${httpErrors.length} cons=${consoleErrors.length}`);
}

await browser.close();
const reportPath = path.join(reportsDir, `smoke_${new Date().toISOString().replace(/[:.]/g, "-")}.json`);
await fs.writeFile(reportPath, JSON.stringify(summary, null, 2));
console.log(`[smoke] report → ${path.relative(process.cwd(), reportPath)}`);
