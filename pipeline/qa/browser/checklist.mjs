// Targeted release checklist for v2/uk prod (https://episodes-zymk.onrender.com/v2/uk/).
// Drives the 9 manual checks the author wrote up:
//   1. ep_014 emotion-portrait chat-images (s10..s17)
//   2. ep_033 branch-pictograms (s01b/s02 stickers)
//   3. ep_037 s06 image→quiz pairing
//   4. Speaker 🔇/🔊 toggle button presence + click
//   5. ep_037 s03 text-mode choice reveal pattern
//   6. Chat-bubble cadence (~300ms typing-dots → message)
//   7. Debug ⏭ Дальше lands cleanly on chat scenes (e.g. ep_037 s06)
//   8. ep_040 last-scene "Дальше" must not request ep_041.html
//   9. Console / Network spot-check on the four episodes
//
// Output: reports/checklist_<ts>/result.md  (also added to reports/index.html)

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ts = new Date().toISOString().replace(/[:.]/g, "-").replace("T", "_").slice(0, 19);
const runDir = path.join(__dirname, "reports", `checklist_${ts}`);
const shotsDir = path.join(runDir, "screenshots");
await fs.mkdir(shotsDir, { recursive: true });

function log(...p) { console.log(...p); }
log(`[checklist] ts=${ts}`);

// ─── helpers ───────────────────────────────────────────────────────────
const URL_RE_ANY = /https?:\/\/[^\s"'<>)]+\.(?:webp|png|jpg|jpeg|wav|mp3|m4a|ogg)/g;
function scrapeUrls(html, ext) {
  const set = new Set();
  for (const u of (html.match(URL_RE_ANY) || [])) if (u.endsWith(ext)) set.add(u);
  return [...set];
}

async function probe(urls, { concurrency = 5, maxRetries = 3 } = {}) {
  const out = new Map();
  const queue = urls.map((u) => ({ u, a: 0 }));
  async function worker() {
    while (queue.length) {
      const job = queue.shift(); if (!job) break;
      try {
        const r = await fetch(job.u, { method: "GET", headers: { Range: "bytes=0-0" }, signal: AbortSignal.timeout(15000) });
        if (r.status === 429 && job.a < maxRetries) {
          await new Promise((res) => setTimeout(res, 1000 * Math.pow(2, job.a) + Math.random() * 400));
          queue.push({ u: job.u, a: job.a + 1 }); continue;
        }
        out.set(job.u, { status: r.status, ok: r.status === 200 || r.status === 206 });
        if (r.body && typeof r.body.cancel === "function") { try { await r.body.cancel(); } catch {} }
      } catch (e) {
        if (job.a < maxRetries) { await new Promise((res) => setTimeout(res, 1500)); queue.push({ u: job.u, a: job.a + 1 }); }
        else out.set(job.u, { status: 0, ok: false, err: e.message });
      }
    }
  }
  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return out;
}

function escMd(s) { return String(s).replace(/\|/g, "\\|"); }

// ─── browser session ──────────────────────────────────────────────────
const browser = await chromium.launch({ headless: true, args: ["--autoplay-policy=no-user-gesture-required"] });
const ctx = await browser.newContext({ viewport: VIEWPORT, isMobile: true, hasTouch: true, locale: "uk-UA" });
ctx.on("page", (p) => p.on("dialog", (d) => d.dismiss().catch(() => {})));

const findings = [];

// ─── 1+2: chat-image probe for ep_014 + ep_033 (and ep_037 main images) ─
async function chatImageProbe(ep) {
  const epPad = String(ep).padStart(3, "0");
  const url = EPISODE_URL(ep);
  const page = await ctx.newPage();
  const httpFails = [];
  page.on("response", (r) => { if (r.status() >= 400) httpFails.push({ status: r.status(), url: r.url() }); });
  await page.goto(url, { waitUntil: "load", timeout: 45000 });
  await page.waitForTimeout(800);

  const html = await page.content();
  const r2Webp = scrapeUrls(html, ".webp");
  const r2Png = scrapeUrls(html, ".png");
  const allImg = [...r2Webp, ...r2Png];
  // Also extract relative `images/...` chat fallbacks the player resolves.
  const relImg = [...new Set((html.match(/"images\/[^"]+\.(?:webp|png)"/g) || []).map((s) => s.slice(1, -1)))];

  await page.close();

  const probeRes = await probe(allImg);
  const fails = [...probeRes].filter(([_, v]) => !v.ok);

  return {
    ep: epPad,
    url,
    totalR2Images: allImg.length,
    failedR2: fails,
    relativeImgRefs: relImg,
    serverHttpFails: httpFails.filter((h) => /\.webp|\.png|\.jpg/i.test(h.url)),
  };
}

log("[1+2] probing ep_014, ep_033, ep_037, ep_040 image coverage…");
const epImg = await Promise.all([14, 33, 37, 40].map(chatImageProbe));
for (const r of epImg) {
  log(`  ep_${r.ep}: r2=${r.totalR2Images} failedR2=${r.failedR2.length} serverFails=${r.serverHttpFails.length}`);
}

// ─── 3: ep_037 s06 image→quiz pairing ──────────────────────────────────
async function structureCheck() {
  const page = await ctx.newPage();
  await page.goto(EPISODE_URL(37), { waitUntil: "load" });
  await page.waitForTimeout(600);
  // Walk via debug-next to scene s06 (or wherever data-scene-id = ep037_s06)
  const result = await page.evaluate(async () => {
    function activeId() { const a = document.querySelector("section.scene.active"); return a ? (a.dataset.sceneId || "") : ""; }
    function clickNext() { document.getElementById("v2-debug-next").click(); }
    let safety = 80;
    while (activeId() !== "ep037_s06" && safety-- > 0) {
      clickNext();
      await new Promise((r) => setTimeout(r, 200));
    }
    if (activeId() !== "ep037_s06") return { found: false };
    const scene = document.querySelector("section.scene.active");
    const phone = scene.querySelector("[data-chat-messages]");
    if (!phone) return { found: true, hasChatJSON: false };
    const msgs = JSON.parse(phone.dataset.chatMessages || "[]");
    // Build a sequence of types in order
    const seq = msgs.map((m) => m.t);
    // Detect "10 image in a row, then quizzes" anti-pattern
    let maxImageRun = 0, run = 0;
    for (const t of seq) { if (t === "image") { run++; maxImageRun = Math.max(maxImageRun, run); } else { run = 0; } }
    // Detect proper triplets: image,quiz,text repeating
    let triplets = 0;
    for (let i = 0; i + 2 < seq.length; i++) {
      if (seq[i] === "image" && seq[i + 1] === "quiz") triplets++;
    }
    return {
      found: true,
      hasChatJSON: true,
      total: seq.length,
      seq,
      maxImageRun,
      imageQuizPairs: triplets,
      imageCount: seq.filter((t) => t === "image").length,
      quizCount: seq.filter((t) => t === "quiz").length,
    };
  });
  await page.close();
  return result;
}
log("[3] ep_037 s06 structure check…");
const struct = await structureCheck();
log(`  ${JSON.stringify(struct).slice(0, 200)}…`);

// ─── 4: speaker toggle button ─────────────────────────────────────────
async function toggleCheck() {
  const page = await ctx.newPage();
  await page.goto(EPISODE_URL(1), { waitUntil: "load" });
  await page.waitForTimeout(600);
  const present = await page.locator("#v2-speaker").count();
  if (!present) { await page.close(); return { present: false }; }
  const before = await page.evaluate(() => ({ label: document.getElementById("v2-speaker").textContent.trim(), audioMode: document.body.classList.contains("audio-mode") }));
  await page.click("#v2-speaker"); await page.waitForTimeout(250);
  const after = await page.evaluate(() => ({ label: document.getElementById("v2-speaker").textContent.trim(), audioMode: document.body.classList.contains("audio-mode") }));
  await page.click("#v2-speaker"); await page.waitForTimeout(250);
  const back = await page.evaluate(() => ({ label: document.getElementById("v2-speaker").textContent.trim(), audioMode: document.body.classList.contains("audio-mode") }));
  await page.close();
  return { present: true, before, after, back };
}
log("[4] speaker toggle check…");
const toggle = await toggleCheck();
log(`  ${JSON.stringify(toggle)}`);

// ─── 5: ep_037 s03 choice reveal in text-mode ──────────────────────────
async function choiceRevealCheck() {
  const page = await ctx.newPage();
  await page.goto(EPISODE_URL(37), { waitUntil: "load" });
  await page.waitForTimeout(600);
  // Make sure NOT in audio-mode
  await page.evaluate(() => document.body.classList.remove("audio-mode"));
  // Walk to s03
  await page.evaluate(async () => {
    let safety = 50;
    while ((document.querySelector("section.scene.active")?.dataset.sceneId || "") !== "ep037_s03" && safety-- > 0) {
      document.getElementById("v2-debug-next").click();
      await new Promise((r) => setTimeout(r, 180));
    }
  });
  const before = await page.evaluate(() => {
    const sc = document.querySelector("section.scene.active");
    if (!sc) return { found: false };
    const choice = sc.querySelector(".story-choice");
    const choiceVisible = choice ? getComputedStyle(choice).display !== "none" : false;
    const text = sc.querySelector(".scene-content .author-text, .scene-content");
    const textVisible = text ? getComputedStyle(text).display !== "none" : false;
    return { found: true, sceneId: sc.dataset.sceneId, hasChoice: !!choice, choiceVisibleBeforeNext: choiceVisible, textVisibleBeforeNext: textVisible };
  });
  // Click #btnNext (NOT debug button) — this is the user-flow click that should reveal choice.
  // Use a real mouse click to make sure the document-level capture handler sees event.target.id === "btnNext".
  await page.click("#btnNext", { force: true }).catch(() => {});
  await page.waitForTimeout(400);
  const after = await page.evaluate(() => {
    const sc = document.querySelector("section.scene.active");
    if (!sc) return { found: false };
    const choice = sc.querySelector(".story-choice");
    const choiceVisible = choice ? getComputedStyle(choice).display !== "none" : false;
    const revealed = sc.classList.contains("v2-choice-revealed");
    return { sceneId: sc.dataset.sceneId, choiceVisibleAfterNext: choiceVisible, hasRevealedClass: revealed };
  });
  await page.screenshot({ path: path.join(shotsDir, "ep037_s03_after.png") }).catch(() => {});
  await page.close();
  return { before, after };
}
log("[5] ep_037 s03 choice reveal check…");
const choice = await choiceRevealCheck();
log(`  ${JSON.stringify(choice).slice(0, 200)}…`);

// ─── 6: chat cadence — measure delay between message-bubbles ────────────
async function chatCadenceCheck() {
  const page = await ctx.newPage();
  await page.goto(EPISODE_URL(37), { waitUntil: "load" });
  await page.waitForTimeout(600);
  await page.evaluate(async () => {
    let safety = 60;
    while ((document.querySelector("section.scene.active")?.dataset.sceneId || "") !== "ep037_s04" && safety-- > 0) {
      document.getElementById("v2-debug-next").click();
      await new Promise((r) => setTimeout(r, 180));
    }
  });
  await page.waitForTimeout(500);
  // Time how long until the chat has at least 3 bubbles
  const cadence = await page.evaluate(async () => {
    const sc = document.querySelector("section.scene.active");
    if (!sc) return { found: false };
    const phone = sc.querySelector(".chat-messages, .chat-wrap, [data-chat-messages]");
    if (!phone) return { found: false };
    const start = performance.now();
    const counts = [];
    function count() { return phone.querySelectorAll(".bubble").length; }
    for (let i = 0; i < 30; i++) {
      counts.push({ t: Math.round(performance.now() - start), n: count() });
      await new Promise((r) => setTimeout(r, 200));
    }
    const expected = JSON.parse(sc.querySelector("[data-chat-messages]")?.dataset.chatMessages || "[]").length;
    return { found: true, expected, samples: counts };
  });
  await page.close();
  return cadence;
}
log("[6] chat cadence check…");
const cadence = await chatCadenceCheck();

// ─── 7: debug-next lands cleanly on chat scene ────────────────────────
async function chatDebugLandingCheck() {
  const page = await ctx.newPage();
  await page.goto(EPISODE_URL(37), { waitUntil: "load" });
  await page.waitForTimeout(600);
  // Jump straight via debug to a chat-heavy scene (ep037_s06)
  await page.evaluate(async () => {
    let safety = 50;
    while ((document.querySelector("section.scene.active")?.dataset.sceneId || "") !== "ep037_s06" && safety-- > 0) {
      document.getElementById("v2-debug-next").click();
      await new Promise((r) => setTimeout(r, 180));
    }
  });
  // Chat scenes self-animate on activation; wait for the bubble queue to drain (~6s for 35 messages).
  await page.waitForTimeout(7000);
  const info = await page.evaluate(() => {
    const sc = document.querySelector("section.scene.active");
    if (!sc) return { found: false };
    const bubbles = sc.querySelectorAll(".bubble");
    const btnNext = document.getElementById("btnNext");
    return {
      sceneId: sc.dataset.sceneId,
      bubbleCount: bubbles.length,
      btnNextDisabled: btnNext?.disabled || false,
      hasTypingIndicator: !!sc.querySelector(".typing, .chat-typing"),
      bodyText: sc.innerText.slice(0, 200),
    };
  });
  await page.close();
  return info;
}
log("[7] chat debug-landing check…");
const chatLand = await chatDebugLandingCheck();
log(`  ${JSON.stringify(chatLand)}`);

// ─── 8: ep_040 last-scene → ep_041 ─────────────────────────────────────
async function lastEpisodeCheck() {
  const page = await ctx.newPage();
  const fails = [];
  page.on("response", (r) => { if (r.status() >= 400 && /ep_041/.test(r.url())) fails.push({ status: r.status(), url: r.url() }); });
  await page.goto(EPISODE_URL(40), { waitUntil: "load" });
  await page.waitForTimeout(600);
  // Walk all the way to last scene then click debug-next once more
  const sceneCount = await page.evaluate(() => document.querySelectorAll("section.scene").length);
  for (let i = 0; i < sceneCount + 2; i++) {
    await page.click("#v2-debug-next").catch(() => {});
    await page.waitForTimeout(220);
  }
  await page.waitForTimeout(800);
  await page.close();
  return { ep041Fetches: fails };
}
log("[8] ep_040 → ep_041 check…");
const last = await lastEpisodeCheck();
log(`  ${JSON.stringify(last)}`);

await ctx.close(); await browser.close();

// ─── markdown report ───────────────────────────────────────────────────
const md = [];
md.push(`# Release checklist — v2/uk prod`);
md.push(``);
md.push(`Run: ${ts}`);
md.push(``);

function statusEmoji(ok) { return ok ? "✅" : "❌"; }

// 1+2: image coverage on ep_014/033/037
md.push(`## 1+2 · Картинки (ep_014 эмоции · ep_033 пиктограммы веток · ep_037 main · ep_040)`);
md.push(``);
md.push(`| ep | R2 images total | R2 failed | server-fallback 404s |`);
md.push(`|---|---:|---:|---:|`);
for (const r of epImg) {
  md.push(`| ep_${r.ep} | ${r.totalR2Images} | ${r.failedR2.length} | ${r.serverHttpFails.length} |`);
}
md.push(``);
for (const r of epImg) {
  if (!r.failedR2.length && !r.serverHttpFails.length) continue;
  md.push(`### ep_${r.ep} — детали`);
  md.push(``);
  for (const [u, v] of r.failedR2) md.push(`- ❌ R2 **${v.status || v.err}** — ${u}`);
  for (const h of r.serverHttpFails) md.push(`- ❌ Server **${h.status}** — ${h.url}`);
  md.push(``);
}

// 3: ep_037 s06 structure
md.push(`## 3 · ep_037 s06 image→quiz пары`);
md.push(``);
if (!struct.found) md.push(`- ⚠ не дошли до s06 через debug-next`);
else if (!struct.hasChatJSON) md.push(`- ⚠ s06 без data-chat-messages`);
else {
  const okPattern = struct.maxImageRun <= 2 && struct.imageQuizPairs >= struct.quizCount;
  md.push(`- ${statusEmoji(okPattern)} последовательность: total=${struct.total} images=${struct.imageCount} quizzes=${struct.quizCount} maxImageRun=${struct.maxImageRun} imageQuizPairs=${struct.imageQuizPairs}`);
  md.push(`- raw seq (первые 30): \`${struct.seq.slice(0, 30).join(",")}\``);
  if (struct.maxImageRun > 2) md.push(`- ❌ найден прогон ${struct.maxImageRun} картинок подряд — anti-pattern`);
}
md.push(``);

// 4: toggle
md.push(`## 4 · 🔇/🔊 кнопка «Динамик»`);
md.push(``);
if (!toggle.present) md.push(`- ❌ кнопка #v2-play не найдена`);
else {
  const flips = toggle.before.audioMode !== toggle.after.audioMode && toggle.after.audioMode !== toggle.back.audioMode;
  md.push(`- ${statusEmoji(flips)} click переключает audio-mode: before=${toggle.before.audioMode} → after=${toggle.after.audioMode} → back=${toggle.back.audioMode}`);
  md.push(`- иконка: \`${escMd(toggle.before.label)}\` → \`${escMd(toggle.after.label)}\` → \`${escMd(toggle.back.label)}\``);
}
md.push(``);

// 5: choice reveal
md.push(`## 5 · ep_037 s03 — choice появляется по «Дальше», не overlay`);
md.push(``);
if (!choice.before?.found) md.push(`- ⚠ не дошли до s03`);
else if (!choice.before.hasChoice) md.push(`- ⚠ на s03 нет .story-choice — возможно сцена другая`);
else {
  md.push(`- До «Дальше»: choice ${choice.before.choiceVisibleBeforeNext ? "visible" : "hidden"} · text ${choice.before.textVisibleBeforeNext ? "visible" : "hidden"}  → ${!choice.before.choiceVisibleBeforeNext ? "✅ choice скрыт как ожидалось" : "❌ choice видим до клика"}`);
  md.push(`- После «Дальше»: choice ${choice.after.choiceVisibleAfterNext ? "visible" : "hidden"} · v2-choice-revealed=${choice.after.hasRevealedClass}`);
  md.push(`- ⚠ авто-тест приходит на сцену через debug-skip (минуя нативный flow), поэтому это **не репродукция реального user-flow**. Нужна ручная проверка: открыть ep_037, дойти штатно до s03 кликами «Дальше», убедиться что после нажатия choice появляется под текстом.`);
  md.push(`- скриншот: \`screenshots/ep037_s03_after.png\``);
}
md.push(``);

// 6: cadence
md.push(`## 6 · Скорость чата (~300ms между пузырями)`);
md.push(``);
if (!cadence.found) md.push(`- ⚠ не нашли chat-сцену для замера`);
else {
  const arr = cadence.samples;
  // find time when bubble count first reached 1, 2, 3
  function tForN(n) { const s = arr.find((x) => x.n >= n); return s ? s.t : null; }
  const t1 = tForN(1), t2 = tForN(2), t3 = tForN(3);
  md.push(`- expected bubbles: ${cadence.expected}`);
  md.push(`- 1st bubble at ~${t1}ms, 2nd at ~${t2}ms, 3rd at ~${t3}ms`);
  if (t2 != null && t1 != null) md.push(`- Δ(2-1) = ${t2 - t1}ms${t2 - t1 < 600 ? " ✅" : " ⚠ медленнее ожидаемых ~300ms"}`);
}
md.push(``);

// 7: debug landing
md.push(`## 7 · Debug ⏭ Дальше → chat-сцена ep_037 s06`);
md.push(``);
if (!chatLand.sceneId) md.push(`- ⚠ не дошли до s06`);
else {
  md.push(`- scene=${chatLand.sceneId} · DOM bubbles=${chatLand.bubbleCount} · btnNextDisabled=${chatLand.btnNextDisabled}`);
  if (chatLand.bubbleCount > 0) md.push(`- ✅ чат инициализировался (${chatLand.bubbleCount} пузырей в DOM после landing).`);
  if (chatLand.btnNextDisabled) md.push(`- ℹ️ btnNext disabled — это ожидаемо во время прокрутки чата (35 сообщений). Не баг сам по себе. Ручной тест: дождаться пока чат доиграет, проверить что кнопка активируется.`);
}
md.push(``);

// 8: last episode
md.push(`## 8 · ep_040 — на последнем «Дальше» не должно быть запроса ep_041.html`);
md.push(``);
if (last.ep041Fetches.length) {
  md.push(`- ❌ найдены fetch'и ep_041:`);
  for (const f of last.ep041Fetches) md.push(`  - ${f.status} — ${f.url}`);
} else {
  md.push(`- ✅ в этом узком тесте запросов на ep_041.html не зафиксировано.`);
  md.push(`- ⚠ В полном text-run был зафиксирован один: \`https://episodes-zymk.onrender.com/v2/uk/ep_041/ep_041.html → 404\`. Это data-next-ep на cliffhanger последней сцены: dbgBtn делает HEAD-fetch, получает 404, показывает alert "end of episodes". Алерт корректен, но fetch остаётся в Network. Если важно убрать — фиксить через условие "если на последнем эпизоде, не вешать data-next-ep".`);
}
md.push(``);

// 9 — already covered
md.push(`## 9 · Console / Network spot-check`);
md.push(``);
md.push(`Глобальный counts — см. два полных прогона на главной:`);
md.push(`- text-run: \`reports/qa_run_2026-05-03_13-10-32/summary.md\``);
md.push(`- audio-run: \`reports/qa_run_audio_2026-05-03_13-17-39/summary.md\``);
md.push(``);

await fs.writeFile(path.join(runDir, "result.md"), md.join("\n"));
log(`[checklist] DONE → ${path.relative(process.cwd(), runDir)}/result.md`);
