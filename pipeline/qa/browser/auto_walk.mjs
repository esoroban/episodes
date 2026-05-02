// Auto-walk an episode by clicking "Дальше" until the end screen.
// Captures: console errors, pageerrors, HTTP 4xx/5xx, requestfailed.
// Saves: screenshots/<ep>/scene_<n>.png + reports/<ep>.json
//
// Usage: node auto_walk.mjs <ep>             (default: 1, headed)
//        node auto_walk.mjs <ep> headless    (run without window)
//
// Notes:
//  • Clicks #btnNext repeatedly. Quizzes block #btnNext until answered —
//    the walker auto-clicks the first quiz option in that case (just to
//    progress; this is not answer-correctness QA).
//  • Stops when #endScreen is visible OR after MAX_STEPS safety cap.

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ep = process.argv[2] || "1";
const headless = process.argv[3] === "headless";
const epPad = String(ep).padStart(3, "0");
const MAX_STEPS = 200;

const shotsDir = path.join(__dirname, "screenshots", `ep_${epPad}`);
const reportsDir = path.join(__dirname, "reports");
await fs.mkdir(shotsDir, { recursive: true });
await fs.mkdir(reportsDir, { recursive: true });

const url = EPISODE_URL(ep);
console.log(`[walk] ep_${epPad} → ${url}  headless=${headless}`);

const browser = await chromium.launch({ headless });
const ctx = await browser.newContext({
  viewport: VIEWPORT,
  isMobile: true,
  hasTouch: true,
  locale: "uk-UA",
});
const page = await ctx.newPage();

const errors = [];
const httpErrors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push({ kind: "console", text: msg.text() });
});
page.on("pageerror", (e) => errors.push({ kind: "pageerror", text: e.message }));
page.on("requestfailed", (req) => {
  httpErrors.push({ kind: "requestfailed", url: req.url(), err: req.failure()?.errorText });
});
page.on("response", async (res) => {
  if (res.status() >= 400) httpErrors.push({ kind: "http", status: res.status(), url: res.url() });
});

await page.goto(url, { waitUntil: "domcontentloaded" });

// Mute audio so headed runs don't blast TTS.
await page.addInitScript(() => {
  document.addEventListener("play", (e) => {
    try { e.target.muted = true; } catch {}
  }, true);
});

const steps = [];
let lastSceneId = null;

for (let i = 0; i < MAX_STEPS; i++) {
  await page.waitForTimeout(250);

  const ended = await page.locator("#endScreen.active, #endScreen[style*='display: block'], #endScreen:visible").count();
  const endedVisible = await page.evaluate(() => {
    const el = document.getElementById("endScreen");
    if (!el) return false;
    const st = getComputedStyle(el);
    return st.display !== "none" && st.visibility !== "hidden" && el.offsetParent !== null;
  });
  if (endedVisible) {
    console.log(`[walk] reached endScreen at step ${i}`);
    await page.screenshot({ path: path.join(shotsDir, `end.png`), fullPage: true });
    steps.push({ step: i, sceneId: "__end__" });
    break;
  }

  const sceneInfo = await page.evaluate(() => {
    const active = document.querySelector(".scene.active");
    if (!active) return null;
    return {
      id: active.dataset.sceneId || active.id || null,
      index: active.dataset.index || null,
    };
  });

  if (sceneInfo && sceneInfo.id !== lastSceneId) {
    lastSceneId = sceneInfo.id;
    const file = path.join(shotsDir, `${String(i).padStart(3, "0")}_${(sceneInfo.id || "n").replace(/[^a-z0-9_-]/gi, "_")}.png`);
    await page.screenshot({ path: file, fullPage: false });
    steps.push({ step: i, sceneId: sceneInfo.id, sceneIndex: sceneInfo.index });
  }

  // If quiz options are blocking #btnNext, click the first one.
  const nextDisabled = await page.evaluate(() => {
    const b = document.getElementById("btnNext");
    return !b || b.disabled;
  });

  if (nextDisabled) {
    const clicked = await page.evaluate(() => {
      const opt = document.querySelector(".scene.active .quiz-option:not(.disabled), .scene.active button.quiz-option");
      if (opt) { opt.click(); return true; }
      const chatOpt = document.querySelector(".scene.active .chat-option:not(.disabled)");
      if (chatOpt) { chatOpt.click(); return true; }
      return false;
    });
    if (!clicked) {
      console.log(`[walk] btnNext disabled and no clickable option at step ${i}, breaking`);
      break;
    }
    await page.waitForTimeout(300);
    continue;
  }

  await page.click("#btnNext").catch(() => {});
}

const report = {
  episode: epPad,
  url,
  finishedAt: new Date().toISOString(),
  stepsCount: steps.length,
  steps,
  consoleErrors: errors,
  httpErrors,
};
const reportPath = path.join(reportsDir, `ep_${epPad}.json`);
await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
console.log(`[walk] report → ${path.relative(process.cwd(), reportPath)}`);
console.log(`[walk] errors: console=${errors.length} http=${httpErrors.length}`);

await browser.close();
