// Quick shot: first scene of each ep_041..044 RU live, mobile viewport.
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({ headless: true });
for (const n of [41, 42, 43, 44]) {
  const epPad = String(n).padStart(3, "0");
  const ctx = await browser.newContext({
    viewport: { width: 412, height: 915 },
    isMobile: true,
    hasTouch: true,
    locale: "ru-RU",
  });
  const page = await ctx.newPage();
  await page.goto(`https://episodes-zymk.onrender.com/game/ru/ep_${epPad}.html`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  const shot = path.join(__dirname, "screenshots", "ru-day11", `ep_${epPad}_first.png`);
  await page.screenshot({ path: shot, fullPage: false });
  console.log(`ep_${epPad} → ${shot}`);
  await ctx.close();
}
await browser.close();
