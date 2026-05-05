// Walk to the chained sofa-section in each ep and screenshot.
// Section index where chain lives: ep_041=9 (s09), ep_042=8, ep_043=8, ep_044=7.
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({ headless: true });

const TARGETS = [
  { ep: 41, targetIdx: 9 },   // chain s09→s15_sofa starts here
  { ep: 42, targetIdx: 8 },
  { ep: 43, targetIdx: 8 },
  { ep: 44, targetIdx: 7 },
];

for (const { ep, targetIdx } of TARGETS) {
  const epPad = String(ep).padStart(3, "0");
  const ctx = await browser.newContext({
    viewport: { width: 412, height: 915 },
    isMobile: true, hasTouch: true, locale: "ru-RU",
  });
  const page = await ctx.newPage();
  await page.goto(`https://episodes-zymk.onrender.com/game/ru/ep_${epPad}.html`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);

  // Use debug burger to jump directly to scene by index (it has scene picker).
  // Faster fallback: keep clicking #btnNext until current scene index >= targetIdx.
  for (let i = 0; i < 60; i++) {
    const idxNow = await page.evaluate(() => {
      const a = document.querySelector(".scene.active");
      return a ? parseInt(a.dataset.index || "0", 10) : -1;
    }).catch(() => -1);
    if (idxNow >= targetIdx) break;
    const ok = await page.evaluate(() => {
      const b = document.getElementById("btnNext");
      if (b && !b.disabled) { b.click(); return true; }
      return false;
    }).catch(() => false);
    if (!ok) {
      // try choice-option (first), or send-btn for chat-input scenes
      await page.evaluate(() => {
        const c = document.querySelector(".scene.active button.choice-option:not(.disabled)");
        if (c) { c.click(); return; }
        const s = document.querySelector(".scene.active .chat-input-bar.imode-text .send-btn");
        if (s) s.click();
      }).catch(() => {});
    }
    await page.waitForTimeout(250);
  }

  // Now screenshot — full page so we see if chain spills above the phone.
  const shot = path.join(__dirname, "screenshots", "ru-day11", `ep_${epPad}_chain.png`);
  await page.screenshot({ path: shot, fullPage: true });
  console.log(`ep_${epPad} idx=${targetIdx} → ${shot}`);

  // Also viewport-only (what user actually sees)
  const shot2 = path.join(__dirname, "screenshots", "ru-day11", `ep_${epPad}_chain_viewport.png`);
  await page.screenshot({ path: shot2, fullPage: false });

  await ctx.close();
}
await browser.close();
