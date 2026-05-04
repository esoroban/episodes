// Walk RU episodes on the live Render server (Day 11 constructor check).
// Targets /game/ru/ep_NNN.html (NOT v2/uk).
//
// Differences vs auto_walk.mjs:
//   • Picks the CORRECT option in chat quizzes (data-c="true") — otherwise
//     constructor scenes loop forever waiting for the right pick.
//   • Detects hangs: no scene_id change AND no quiz pick for N consecutive
//     ticks → dump screenshot + console + last seen DOM, stop.
//   • Reports per scene: kind, quizzes-clicked, time-spent, errors-on-scene.
//
// Usage:
//   node walk_ru.mjs                 # ep 41..44, headless
//   node walk_ru.mjs 42              # one episode
//   node walk_ru.mjs 41-44 headed    # show browser

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROD = "https://episodes-zymk.onrender.com/game/ru";
const URL_FOR = (n) => `${PROD}/ep_${String(n).padStart(3, "0")}.html`;

const arg1 = process.argv[2] || "41-44";
const headless = process.argv[3] !== "headed";

let episodes;
if (arg1.includes("-")) {
  const [a, b] = arg1.split("-").map((x) => parseInt(x, 10));
  episodes = Array.from({ length: b - a + 1 }, (_, i) => a + i);
} else {
  episodes = [parseInt(arg1, 10)];
}

const STUCK_LIMIT = 30; // ticks of zero progress before declaring hang (chat scenes can take time)
const TICK_MS = 300;
const MAX_STEPS = 500;

const reportsDir = path.join(__dirname, "reports", "ru-day11");
await fs.mkdir(reportsDir, { recursive: true });
const shotsDir = path.join(__dirname, "screenshots", "ru-day11");
await fs.mkdir(shotsDir, { recursive: true });

const browser = await chromium.launch({ headless });

const summary = [];

for (const ep of episodes) {
  const epPad = String(ep).padStart(3, "0");
  const url = URL_FOR(ep);
  console.log(`\n=== ep_${epPad} → ${url} ===`);

  const ctx = await browser.newContext({
    viewport: { width: 412, height: 915 },
    isMobile: true,
    hasTouch: true,
    locale: "ru-RU",
  });
  const page = await ctx.newPage();

  const consoleErrs = [];
  const httpErrs = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrs.push(m.text()); });
  page.on("pageerror", (e) => consoleErrs.push("PAGEERR: " + e.message));
  page.on("requestfailed", (r) => httpErrs.push({ url: r.url(), err: r.failure()?.errorText }));
  page.on("response", (r) => { if (r.status() >= 400) httpErrs.push({ url: r.url(), status: r.status() }); });

  // Mute audio
  await page.addInitScript(() => {
    document.addEventListener("play", (e) => { try { e.target.muted = true; } catch {} }, true);
  });

  const t0 = Date.now();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 }).catch((e) => {
    consoleErrs.push("GOTO_FAIL: " + e.message);
  });

  const sceneTrace = [];
  let lastSceneId = null;
  let stuckTicks = 0;
  let stuckScene = null;
  let stuckHtml = null;

  let navigatedAway = false;
  for (let i = 0; i < MAX_STEPS && !navigatedAway; i++) {
    await page.waitForTimeout(TICK_MS);

    // Detect navigation away (cliffhanger jumped to next episode)
    const currentUrl = page.url();
    if (!currentUrl.includes(`ep_${epPad}`)) {
      console.log(`  navigated away: ${currentUrl}`);
      navigatedAway = true;
      sceneTrace.push({ step: i, sceneId: "__nav_away__", url: currentUrl });
      break;
    }

    // End-screen detect
    const ended = await page.evaluate(() => {
      const el = document.getElementById("endScreen");
      if (!el) return false;
      const st = getComputedStyle(el);
      return st.display !== "none" && st.visibility !== "hidden" && el.offsetParent !== null;
    }).catch(() => false);
    if (ended) {
      sceneTrace.push({ step: i, sceneId: "__end__" });
      break;
    }

    // Active scene detect
    const sc = await page.evaluate(() => {
      const a = document.querySelector(".scene.active");
      if (!a) return null;
      return {
        id: a.dataset.sceneId || a.id || null,
        index: a.dataset.index || null,
        hasChat: !!a.querySelector(".phone .chat-messages"),
      };
    }).catch(() => null);

    let acted = false;

    if (sc && sc.id !== lastSceneId) {
      lastSceneId = sc.id;
      sceneTrace.push({ step: i, sceneId: sc.id, idx: sc.index, hasChat: sc.hasChat });
      stuckTicks = 0;
      acted = true;
    }

    // 1) Try clicking correct chat-quiz option
    const clickedQuiz = await page.evaluate(() => {
      const correct = document.querySelector(".scene.active .quiz-btn[data-c=\"true\"]:not(.disabled):not(.correct)");
      if (correct) { correct.click(); return "chat-quiz-correct"; }
      // Standard (non-chat) quiz
      const std = document.querySelector(".scene.active button.quiz-option[data-correct=\"true\"]:not(.disabled)");
      if (std) { std.click(); return "std-quiz-correct"; }
      return null;
    }).catch(() => null);
    if (clickedQuiz) {
      stuckTicks = 0;
      acted = true;
      continue;
    }

    // 1b) Chat is awaiting Marko input — click .send-btn (or .mic-btn for voice)
    const clickedSend = await page.evaluate(() => {
      const sendBtn = document.querySelector(".scene.active .chat-input-bar.imode-text .send-btn");
      if (sendBtn) { sendBtn.click(); return "send"; }
      const micBtn = document.querySelector(".scene.active .chat-input-bar.imode-voice .mic-btn");
      if (micBtn) { micBtn.click(); return "mic"; }
      return false;
    }).catch(() => false);
    if (clickedSend) {
      stuckTicks = 0;
      acted = true;
      continue;
    }

    // 2) Choice scene — first option
    const clickedChoice = await page.evaluate(() => {
      const opt = document.querySelector(".scene.active button.choice-option:not(.disabled)");
      if (opt) { opt.click(); return true; }
      return false;
    }).catch(() => false);
    if (clickedChoice) {
      stuckTicks = 0;
      acted = true;
      continue;
    }

    // 3) Click "Дальше"
    const nextOk = await page.evaluate(() => {
      const b = document.getElementById("btnNext");
      if (b && !b.disabled) { b.click(); return true; }
      return false;
    }).catch(() => false);
    if (nextOk) {
      stuckTicks = 0;
      acted = true;
      continue;
    }

    // Nothing happened this tick
    if (!acted) {
      stuckTicks++;
      if (stuckTicks >= STUCK_LIMIT) {
        stuckScene = sc;
        stuckHtml = await page.evaluate(() => {
          const a = document.querySelector(".scene.active");
          return a ? a.outerHTML.substring(0, 6000) : null;
        });
        const shot = path.join(shotsDir, `ep_${epPad}_STUCK_${(sc?.id || "unknown").replace(/[^a-z0-9_-]/gi, "_")}.png`);
        await page.screenshot({ path: shot, fullPage: true });
        console.log(`  [STUCK] ep_${epPad} at scene ${sc?.id} (idx ${sc?.index}) → ${path.relative(process.cwd(), shot)}`);
        break;
      }
    }
  }

  const elapsedMs = Date.now() - t0;
  const result = {
    episode: epPad,
    url,
    elapsedMs,
    sceneCount: sceneTrace.length,
    finalScene: lastSceneId,
    stuck: stuckScene ? { sceneId: stuckScene.id, idx: stuckScene.index, htmlSnippet: stuckHtml } : null,
    consoleErrors: consoleErrs,
    httpErrors: httpErrs,
    sceneTrace,
  };

  const reportPath = path.join(reportsDir, `ep_${epPad}.json`);
  await fs.writeFile(reportPath, JSON.stringify(result, null, 2));

  console.log(`  scenes traversed: ${sceneTrace.length}`);
  console.log(`  console errors: ${consoleErrs.length}, http errors: ${httpErrs.length}`);
  if (result.stuck) console.log(`  STUCK at: ${result.stuck.sceneId}`);
  else console.log(`  reached: ${lastSceneId}`);

  summary.push({
    ep: epPad,
    scenes: sceneTrace.length,
    final: lastSceneId,
    stuck: result.stuck?.sceneId || null,
    errs: consoleErrs.length,
    httpErrs: httpErrs.length,
  });

  await ctx.close();
}

await browser.close();

console.log("\n=== SUMMARY ===");
for (const r of summary) {
  const status = r.stuck ? `STUCK at ${r.stuck}` : `OK → ${r.final}`;
  console.log(`  ep_${r.ep}: scenes=${r.scenes}  ${status}  console=${r.errs}  http=${r.httpErrs}`);
}
