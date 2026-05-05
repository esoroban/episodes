// Native-flow walk through ep_037 — clicks #btnNext exactly like a real
// user would. Resolves each scene state before clicking:
//   • quiz with .quiz-options (no .chosen) → click first option, then Next
//   • story-choice not yet revealed → click Next (reveals), then click first option, then Next
//   • chat scene that's still animating → wait until btnNext re-enables
//   • plain author-text → click Next when btnNext is enabled
//
// Records, per scene: scene-id, what action was taken, whether story-choice
// reveal worked (the specific thing that failed under debug-skip).
//
// Usage: node walk_native.mjs <ep>            (default 37, headless)
//        node walk_native.mjs 37 headed       (watch in a real window)

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ep = parseInt(process.argv[2] || "37", 10);
const headless = process.argv[3] !== "headed";
const targetSceneArg = process.argv[4]; // optional: e.g. "ep037_s03" — stop & inspect there

const ts = new Date().toISOString().replace(/[:.]/g, "-").replace("T", "_").slice(0, 19);
const outDir = path.join(__dirname, "reports", `native_ep${String(ep).padStart(3, "0")}_${ts}`);
const shotDir = path.join(outDir, "screenshots");
await fs.mkdir(shotDir, { recursive: true });
const log = (...p) => console.log(...p);
log(`[native] ep=${ep} headless=${headless}`);

const browser = await chromium.launch({ headless, args: ["--autoplay-policy=no-user-gesture-required"] });
const ctx = await browser.newContext({ viewport: VIEWPORT, isMobile: true, hasTouch: true, locale: "uk-UA" });
ctx.on("page", (p) => p.on("dialog", (d) => d.dismiss().catch(() => {})));
const page = await ctx.newPage();

const consoleErrors = [];
const httpErrors = [];
page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));
page.on("response", (r) => { if (r.status() >= 400) httpErrors.push({ status: r.status(), url: r.url() }); });

await page.goto(EPISODE_URL(ep), { waitUntil: "load", timeout: 45000 });
await page.waitForSelector("#btnNext", { timeout: 15000 });
await page.waitForTimeout(800);

// Force text-mode and keep it: the upstream auto-unlock flips body to
// audio-mode on first pointerdown. We strip it back to text-mode every
// 200ms so the user-visible flow matches "🔇 Аудио выключена".
const forceTextMode = process.argv.includes("--text-mode");
if (forceTextMode) {
  log(`[native] forcing text-mode (audio-mode auto-unlock will be stripped on every tick)`);
  await page.evaluate(() => {
    setInterval(() => { document.body.classList.remove("audio-mode"); }, 150);
  });
}

// Helper: read state of the active scene
async function sceneState() {
  return page.evaluate(() => {
    const sc = document.querySelector("section.scene.active");
    if (!sc) return null;
    const sid = sc.dataset.sceneId || sc.id || "?";
    const audioMode = document.body.classList.contains("audio-mode");
    const audioDone = sc.classList.contains("audio-done");
    const hasStoryChoice = !!sc.querySelector(".story-choice");
    const v2Revealed = sc.classList.contains("v2-choice-revealed");
    // In audio-mode the choice is visible once audio-done; in text-mode after v2-choice-revealed.
    const choiceVisible = !!sc.querySelector(".story-choice")
      && (audioMode ? audioDone : v2Revealed);
    const chosenChoice = !!sc.querySelector(".story-choice .choice-option.chosen");
    const hasQuiz = !!sc.querySelector(".quiz-options, .chat-messages .quiz-question");
    const quizAnswered = !!sc.querySelector(".quiz-option.chosen, .quiz-option[disabled]");
    const hasPhone = !!sc.querySelector("[data-chat-messages]");
    const expectedBubbles = (() => {
      const ph = sc.querySelector("[data-chat-messages]");
      if (!ph) return 0;
      try { return JSON.parse(ph.dataset.chatMessages || "[]").length; } catch { return 0; }
    })();
    const renderedBubbles = sc.querySelectorAll(".chat-messages .bubble").length;
    const btnNextDisabled = document.getElementById("btnNext")?.disabled || false;
    return {
      sid, audioMode, audioDone,
      hasStoryChoice, v2Revealed, choiceVisible, chosenChoice,
      hasQuiz, quizAnswered, hasPhone, expectedBubbles, renderedBubbles,
      btnNextDisabled,
    };
  });
}

// Helper: wait until btnNext is enabled or timeout
async function waitBtnReady(maxMs = 60000) {
  const t0 = Date.now();
  let lastReport = 0;
  while (Date.now() - t0 < maxMs) {
    const s = await sceneState();
    if (!s) return false;
    if (!s.btnNextDisabled) return true;
    if (Date.now() - lastReport > 5000) {
      const ad = await page.evaluate(() => ({
        audioDone: document.querySelector("section.scene.active")?.classList.contains("audio-done"),
        audioMode: document.body.classList.contains("audio-mode"),
        domAudios: document.querySelectorAll("section.scene.active audio").length,
        // count any media element that's currently emitting
      }));
      console.log(`  ⏳ waitBtnReady ${Math.round((Date.now()-t0)/1000)}s sid=${s.sid} bubbles=${s.renderedBubbles}/${s.expectedBubbles} audioMode=${ad.audioMode} audioDone=${ad.audioDone} sceneAudios=${ad.domAudios}`);
      lastReport = Date.now();
    }
    await page.waitForTimeout(300);
  }
  return false;
}

const trace = [];
const SAFETY_STEPS = 80;
let lastSid = null;

for (let step = 0; step < SAFETY_STEPS; step++) {
  // End of episode?
  const endVisible = await page.evaluate(() => {
    const e = document.getElementById("endScreen");
    return e && getComputedStyle(e).display !== "none" && e.offsetParent !== null;
  });
  if (endVisible) { trace.push({ step, action: "end" }); break; }

  let s = await sceneState();
  if (!s) break;

  // Take a snapshot when scene changes
  if (s.sid !== lastSid) {
    const file = path.join(shotDir, `${String(step).padStart(3, "0")}_${s.sid}_pre.png`);
    await page.screenshot({ path: file, fullPage: false }).catch(() => {});
    lastSid = s.sid;
  }

  // Decision
  if (s.hasStoryChoice && !s.choiceVisible && !s.chosenChoice && !s.audioMode) {
    // Text-mode: click Next once to set v2-choice-revealed
    log(`[step ${step}] ${s.sid} text-mode story-choice → click Next to reveal`);
    const ready = await waitBtnReady();
    if (!ready) {
      const dump = await page.evaluate(() => {
        const sc = document.querySelector("section.scene.active");
        if (!sc) return null;
        const cs = (el) => { const s = getComputedStyle(el); return { display: s.display, visibility: s.visibility, opacity: s.opacity }; };
        return {
          sid: sc.dataset.sceneId,
          bodyClasses: document.body.className,
          sceneClasses: sc.className,
          sceneStyle: cs(sc),
          contentSnippet: sc.innerText.slice(0, 300),
          authorText: (() => { const a = sc.querySelector(".author-text"); return a ? { style: cs(a), len: a.innerHTML.length } : null; })(),
          sceneContent: (() => { const a = sc.querySelector(".scene-content"); return a ? { style: cs(a), len: a.innerHTML.length } : null; })(),
          storyChoice: (() => { const a = sc.querySelector(".story-choice"); return a ? { style: cs(a), len: a.innerHTML.length } : null; })(),
          audioDone: sc.classList.contains("audio-done"),
          v2ChoiceRevealed: sc.classList.contains("v2-choice-revealed"),
          audioElemSrcs: Array.from(sc.querySelectorAll("audio")).map((a) => a.currentSrc || a.src),
        };
      });
      trace.push({ step, sid: s.sid, action: "btn-stuck-storychoice", dump });
      log(`  DUMP: ${JSON.stringify(dump, null, 2).slice(0, 1500)}`);
      break;
    }
    await page.click("#btnNext");
    await page.waitForTimeout(450);
    const after = await sceneState();
    const revealed = after?.v2Revealed || after?.choiceVisible || false;
    await page.screenshot({ path: path.join(shotDir, `${String(step).padStart(3, "0")}_${s.sid}_after_next.png`), fullPage: false }).catch(() => {});
    trace.push({ step, sid: s.sid, action: "click-next-to-reveal-choice", revealed });
    if (!revealed) { log(`  ❌ choice did NOT reveal on ${s.sid}`); }
    else log(`  ✅ choice revealed on ${s.sid}`);
    continue;
  }

  if (s.hasStoryChoice && s.choiceVisible && !s.chosenChoice) {
    // Stage B (both modes): click first choice option
    log(`[step ${step}] ${s.sid} click first choice-option`);
    const clicked = await page.evaluate(() => {
      const opt = document.querySelector("section.scene.active .story-choice .choice-option");
      if (!opt) return false;
      opt.click(); return true;
    });
    await page.waitForTimeout(400);
    trace.push({ step, sid: s.sid, action: "click-choice-option", clicked });
    continue;
  }

  if (s.hasQuiz && !s.quizAnswered) {
    log(`[step ${step}] ${s.sid} answer quiz (first option)`);
    const clicked = await page.evaluate(() => {
      const o = document.querySelector("section.scene.active .quiz-option:not(.chosen):not([disabled])");
      if (!o) return false;
      o.click(); return true;
    });
    await page.waitForTimeout(700);
    trace.push({ step, sid: s.sid, action: "answer-quiz", clicked });
    continue;
  }

  // Plain advance — wait btn enabled then click Next
  const ready = await waitBtnReady();
  if (!ready) {
    const dump = await page.evaluate(() => {
      const sc = document.querySelector("section.scene.active");
      if (!sc) return null;
      const cs = (el) => { const s = getComputedStyle(el); return { display: s.display, visibility: s.visibility, opacity: s.opacity, height: s.height }; };
      return {
        sid: sc.dataset.sceneId,
        bodyClasses: document.body.className,
        sceneClasses: sc.className,
        sceneStyle: cs(sc),
        innerHTMLLen: sc.innerHTML.length,
        children: Array.from(sc.children).map((c) => ({ tag: c.tagName, cls: c.className, style: cs(c), childCount: c.children.length })),
        contentSnippet: sc.innerText.slice(0, 300),
        // story-choice details
        storyChoice: (() => {
          const ch = sc.querySelector(".story-choice");
          if (!ch) return null;
          return { style: cs(ch), html: ch.innerHTML.slice(0, 500) };
        })(),
        authorText: (() => {
          const at = sc.querySelector(".author-text, .scene-content");
          if (!at) return null;
          return { tag: at.tagName, cls: at.className, style: cs(at), len: at.innerHTML.length };
        })(),
        // pending audio queue?
        audioElems: Array.from(sc.querySelectorAll("audio")).length,
        audioDoneClass: sc.classList.contains("audio-done"),
      };
    });
    trace.push({ step, sid: s.sid, action: "btn-stuck", state: s, dump });
    log(`[step ${step}] ${s.sid} btnNext stuck disabled — bubbles=${s.renderedBubbles}/${s.expectedBubbles}`);
    log(`  DUMP: ${JSON.stringify(dump, null, 2).slice(0, 1500)}`);
    break;
  }
  await page.click("#btnNext");
  await page.waitForTimeout(350);
  trace.push({ step, sid: s.sid, action: "next" });

  // If a target scene was specified — stop there and grab a final screenshot
  if (targetSceneArg && s.sid === targetSceneArg) {
    await page.screenshot({ path: path.join(shotDir, `target_${targetSceneArg}_state.png`), fullPage: true }).catch(() => {});
    break;
  }
}

await page.waitForTimeout(500);

// Summary
const summary = {
  ep, ts, totalSteps: trace.length,
  storyChoiceScenes: trace.filter((t) => t.action === "click-next-to-reveal-choice"),
  brokenChoiceReveals: trace.filter((t) => t.action === "click-next-to-reveal-choice" && !t.revealed),
  stuck: trace.filter((t) => t.action === "btn-stuck" || t.action === "btn-stuck-storychoice"),
  consoleErrors,
  httpErrors,
};
await fs.writeFile(path.join(outDir, "trace.json"), JSON.stringify({ summary, trace }, null, 2));

log(`\n[native] ep_${String(ep).padStart(3, "0")} done`);
log(`  steps=${trace.length}`);
log(`  story-choice scenes encountered = ${summary.storyChoiceScenes.length}`);
log(`  story-choice reveals OK = ${summary.storyChoiceScenes.length - summary.brokenChoiceReveals.length}`);
log(`  story-choice reveals BROKEN = ${summary.brokenChoiceReveals.length}`);
if (summary.brokenChoiceReveals.length) {
  for (const b of summary.brokenChoiceReveals) log(`    ❌ ${b.sid} (step ${b.step})`);
}
log(`  stuck btnNext = ${summary.stuck.length}`);
if (summary.stuck.length) for (const s of summary.stuck) log(`    ⚠ ${s.sid}`);
log(`  console errors = ${consoleErrors.length}`);
log(`  http 4xx/5xx = ${httpErrors.length}`);
log(`  → ${path.relative(process.cwd(), outDir)}/trace.json`);

await ctx.close();
await browser.close();
