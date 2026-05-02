// Open one episode in a headed browser for manual inspection.
// Usage: node open.mjs <ep>           (mobile viewport, default)
//        node open.mjs <ep> desktop   (desktop viewport)
// The browser stays open until you close it.

import { chromium } from "playwright";
import { EPISODE_URL, VIEWPORT, DESKTOP_VIEWPORT } from "./config.mjs";

const ep = process.argv[2] || "1";
const mode = process.argv[3] || "mobile";
const viewport = mode === "desktop" ? DESKTOP_VIEWPORT : VIEWPORT;

const url = EPISODE_URL(ep);
console.log(`[open] ${url}  (${mode} ${viewport.width}x${viewport.height})`);

const browser = await chromium.launch({ headless: false, devtools: false });
const ctx = await browser.newContext({
  viewport,
  isMobile: mode !== "desktop",
  hasTouch: mode !== "desktop",
  locale: "uk-UA",
});
const page = await ctx.newPage();

page.on("console", (msg) => {
  const t = msg.type();
  if (t === "error" || t === "warning") {
    console.log(`[console.${t}]`, msg.text());
  }
});
page.on("pageerror", (err) => console.log("[pageerror]", err.message));
page.on("requestfailed", (req) => {
  console.log("[404/fail]", req.failure()?.errorText, req.url());
});
page.on("response", (res) => {
  if (res.status() >= 400) {
    console.log(`[http ${res.status()}]`, res.url());
  }
});

await page.goto(url, { waitUntil: "domcontentloaded" });
console.log("[open] loaded — interact manually. Close the window to exit.");

// Keep the script alive until the browser is closed by the user.
await new Promise((resolve) => browser.on("disconnected", resolve));
