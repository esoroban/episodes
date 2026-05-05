// Audio-coverage QA pass for prod v2/uk.
// Two parallel things per episode:
//   (A) Walk every scene with audio-mode visually enabled (click #v2-play)
//       and screenshot — checks the audio-mode UI (text hidden until
//       audio-done, controls visible).
//   (B) Scrape every audio URL out of the page HTML and run a throttled
//       GET probe with retry-on-429 — answers "is every voiceover file
//       actually reachable on R2?"
//
// We do NOT rely on the page running real audio playback, because R2 in
// headless without a media stack is unreliable. Asset availability is the
// signal that matters; UI rendering is the secondary check.
//
// Output: reports/qa_run_audio_<ts>/

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, TOTAL_EPISODES, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseEpisodes(arg) {
  if (!arg || arg === "all") return Array.from({ length: TOTAL_EPISODES }, (_, i) => i + 1);
  if (arg.includes("-")) {
    const [a, b] = arg.split("-").map((n) => parseInt(n, 10));
    return Array.from({ length: b - a + 1 }, (_, i) => a + i);
  }
  return arg.split(",").map((n) => parseInt(n, 10));
}
const eps = parseEpisodes(process.argv[2]);
const headless = process.argv[3] !== "headed";

const ts = new Date().toISOString().replace(/[:.]/g, "-").replace("T", "_").slice(0, 19);
const runDir = path.join(__dirname, "reports", `qa_run_audio_${ts}`);
const shotsRoot = path.join(runDir, "screenshots");
const logPath = path.join(runDir, "log.txt");
await fs.mkdir(shotsRoot, { recursive: true });
const logStream = await fs.open(logPath, "w");
function log(...parts) {
  const line = parts.map((p) => (typeof p === "string" ? p : JSON.stringify(p))).join(" ");
  console.log(line);
  logStream.write(line + "\n");
}
log(`[run_audio] start ts=${ts} eps=${eps.join(",")} headless=${headless}`);

const PER_EP_TIMEOUT_MS = 4 * 60 * 1000;
const TOTAL_TIMEOUT_MS = 90 * 60 * 1000;
const runStarted = Date.now();

// ─── audio URL scrape + probe helpers ──────────────────────────────────
const AUDIO_URL_RE = /https:\/\/pub-[a-f0-9]+\.r2\.dev\/ep_\d{3}\/audio\/[^\s"'<>)]+\.(?:wav|mp3|m4a|ogg)/g;
function scrapeAudioUrls(html) {
  return [...new Set(html.match(AUDIO_URL_RE) || [])];
}

async function probeAudio(urls, { concurrency = 5, maxRetries = 4 } = {}) {
  const results = new Map();
  const queue = urls.map((u) => ({ url: u, attempt: 0 }));
  let done = 0;

  async function worker(id) {
    while (queue.length) {
      const job = queue.shift();
      if (!job) break;
      const { url, attempt } = job;
      try {
        // GET with Range:bytes=0-0 to avoid downloading the whole file —
        // R2 honours this and returns 206 with content-length, exposing
        // the same liveness signal as a HEAD without 429-ing as hard.
        const r = await fetch(url, {
          method: "GET",
          headers: { Range: "bytes=0-0" },
          signal: AbortSignal.timeout(20000),
        });
        if (r.status === 429 && attempt < maxRetries) {
          const wait = Math.min(8000, 1000 * Math.pow(2, attempt) + Math.random() * 500);
          await new Promise((res) => setTimeout(res, wait));
          queue.push({ url, attempt: attempt + 1 });
          continue;
        }
        const len = parseInt(r.headers.get("content-range")?.split("/").pop() || r.headers.get("content-length") || "0", 10);
        results.set(url, { status: r.status, ok: r.status === 206 || r.status === 200, len, attempts: attempt + 1 });
        // small jitter to avoid bursting
        if (r.body && typeof r.body.cancel === "function") { try { await r.body.cancel(); } catch {} }
      } catch (e) {
        if (attempt < maxRetries) {
          await new Promise((res) => setTimeout(res, 1500));
          queue.push({ url, attempt: attempt + 1 });
        } else {
          results.set(url, { status: 0, ok: false, err: e.message, attempts: attempt + 1 });
        }
      }
      done++;
      if (done % 200 === 0) log(`[probe] worker${id} progress: ${done} done, queued=${queue.length}, results=${results.size}`);
    }
  }
  await Promise.all(Array.from({ length: concurrency }, (_, i) => worker(i)));
  return results;
}

// ─── browser audio-mode walk per episode ──────────────────────────────
async function walkEpisode(browser, ep) {
  const epPad = String(ep).padStart(3, "0");
  const url = EPISODE_URL(ep);
  const shotDir = path.join(shotsRoot, `ep_${epPad}`);
  await fs.mkdir(shotDir, { recursive: true });

  const result = {
    ep, epPad, url,
    started: new Date().toISOString(),
    sceneCount: 0,
    scenesWalked: [],
    audioModeOn: false,
    audioUrls: [],
    consoleErrors: [],
    pageErrors: [],
    httpErrors: [],
    durationMs: 0,
    aborted: null,
  };

  const ctx = await browser.newContext({
    viewport: VIEWPORT,
    isMobile: true,
    hasTouch: true,
    locale: "uk-UA",
  });
  ctx.on("page", (p) => p.on("dialog", (d) => { d.dismiss().catch(() => {}); }));
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") result.consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => result.pageErrors.push(e.message));
  page.on("requestfailed", (req) => result.httpErrors.push({ kind: "requestfailed", url: req.url(), err: req.failure()?.errorText }));
  page.on("response", (res) => { if (res.status() >= 400) result.httpErrors.push({ kind: "http", status: res.status(), url: res.url() }); });

  const started = Date.now();
  try {
    await page.goto(url, { waitUntil: "load", timeout: 45000 });
    await page.waitForSelector("#v2-debug-next", { timeout: 15000 });
    await page.waitForTimeout(800);

    // Scrape audio URLs from the rendered HTML
    const html = await page.content();
    result.audioUrls = scrapeAudioUrls(html);

    // Try to enable audio-mode via real click first (user gesture). Fall back
    // to forcing the body class — that's enough to test the UI invariants.
    try { await page.click("#v2-play", { timeout: 2000 }); } catch {}
    await page.waitForTimeout(400);
    let audioModeOn = await page.evaluate(() => document.body.classList.contains("audio-mode"));
    if (!audioModeOn) {
      await page.evaluate(() => document.body.classList.add("audio-mode"));
      audioModeOn = true;
    }
    result.audioModeOn = audioModeOn;

    const sceneCount = await page.evaluate(() => document.querySelectorAll("section.scene").length);
    result.sceneCount = sceneCount;
    log(`[ep_${epPad}] loaded — scenes=${sceneCount} audioUrls=${result.audioUrls.length} audioMode=${audioModeOn}`);

    let activeId = await page.evaluate(() => {
      const a = document.querySelector("section.scene.active");
      return a ? (a.dataset.sceneId || a.id) : null;
    });
    if (activeId) {
      await page.screenshot({ path: path.join(shotDir, `000_${activeId.replace(/[^a-z0-9_-]/gi, "_")}.png`) }).catch(() => {});
      result.scenesWalked.push({ idx: 0, sceneId: activeId });
    }

    const maxClicks = Math.min(Math.max(sceneCount - 1, 0), 60);
    for (let i = 1; i <= maxClicks; i++) {
      if (Date.now() - started > PER_EP_TIMEOUT_MS) { result.aborted = "per-ep timeout"; break; }
      const before = activeId;
      await page.click("#v2-debug-next", { timeout: 5000 }).catch((e) => { result.aborted = `click failed: ${e.message}`; });
      if (result.aborted) break;
      await page.waitForTimeout(350);
      const after = await page.evaluate(() => {
        const a = document.querySelector("section.scene.active");
        return a ? (a.dataset.sceneId || a.id) : null;
      });
      if (after === before) break;
      activeId = after;
      await page.screenshot({ path: path.join(shotDir, `${String(i).padStart(3, "0")}_${activeId.replace(/[^a-z0-9_-]/gi, "_")}.png`) }).catch(() => {});
      result.scenesWalked.push({ idx: i, sceneId: activeId });
    }
  } catch (e) {
    result.aborted = `exception: ${e.message}`;
    log(`[ep_${epPad}] ERROR ${e.message}`);
  }
  result.durationMs = Date.now() - started;
  await ctx.close().catch(() => {});

  log(`[ep_${epPad}] walk done in ${result.durationMs}ms scenes=${result.scenesWalked.length}/${result.sceneCount} audioUrls=${result.audioUrls.length} cons=${result.consoleErrors.length} aborted=${result.aborted || "no"}`);
  return result;
}

// ─── main ──────────────────────────────────────────────────────────────
const browser = await chromium.launch({
  headless,
  args: ["--autoplay-policy=no-user-gesture-required"],
});

const perEp = [];
for (const ep of eps) {
  if (Date.now() - runStarted > TOTAL_TIMEOUT_MS) { log(`[run_audio] total timeout, stopping at ep_${ep}`); break; }
  try { perEp.push(await walkEpisode(browser, ep)); }
  catch (e) {
    log(`[run_audio] walkEpisode threw for ep_${ep}: ${e.message}`);
    perEp.push({ ep, epPad: String(ep).padStart(3, "0"), aborted: `threw: ${e.message}`, audioUrls: [], scenesWalked: [], consoleErrors: [], pageErrors: [], httpErrors: [] });
  }
}
await browser.close();

// Probe phase
const allUrls = [...new Set(perEp.flatMap((r) => r.audioUrls || []))];
log(`[probe] starting throttled GET probe of ${allUrls.length} unique audio URLs (concurrency=5, retry-on-429)…`);
const probeStart = Date.now();
const probe = await probeAudio(allUrls, { concurrency: 5, maxRetries: 4 });
log(`[probe] done in ${((Date.now() - probeStart) / 1000).toFixed(1)}s`);

const failed = [...probe].filter(([_, v]) => !v.ok);
log(`[probe] FAILED: ${failed.length}/${allUrls.length}`);

// Aggregate per ep
const epStats = perEp.map((r) => {
  const okN = (r.audioUrls || []).filter((u) => probe.get(u)?.ok).length;
  const failN = (r.audioUrls || []).filter((u) => !probe.get(u)?.ok).length;
  const failedUrls = (r.audioUrls || []).filter((u) => !probe.get(u)?.ok);
  return { ...r, audioOk: okN, audioFail: failN, failedUrls };
});

const summary = {
  ts,
  eps: eps.length,
  totalScenesWalked: epStats.reduce((a, r) => a + (r.scenesWalked?.length || 0), 0),
  totalScenesExpected: epStats.reduce((a, r) => a + (r.sceneCount || 0), 0),
  totalAudioUrls: allUrls.length,
  totalAudioOk: [...probe].filter(([_, v]) => v.ok).length,
  totalAudioFail: failed.length,
  consoleErrorsTotal: epStats.reduce((a, r) => a + (r.consoleErrors?.length || 0), 0),
  pageErrorsTotal: epStats.reduce((a, r) => a + (r.pageErrors?.length || 0), 0),
  abortedEpisodes: epStats.filter((r) => r.aborted).map((r) => ({ ep: r.epPad, reason: r.aborted })),
};

await fs.writeFile(path.join(runDir, "summary.json"),
  JSON.stringify({ summary, perEp: epStats, failedAudio: Object.fromEntries(failed) }, null, 2));

// Markdown
function urlScene(u) {
  const m = u.match(/\/(ep_\d{3})\/audio\/(?:ep\d+_)?(s\d+[a-z]?)/);
  return m ? `${m[1]}/${m[2]}` : u;
}
const md = [];
md.push(`# QA Run — v2/uk prod (AUDIO coverage)`);
md.push(``);
md.push(`**Start:** ${ts}    **Episodes:** ${eps.join(", ")}    **Mode:** audio-mode walk + throttled GET-probe`);
md.push(``);
md.push(`## TL;DR`);
md.push(``);
md.push(`| Metric | Count |`);
md.push(`|---|---:|`);
md.push(`| Episodes walked | ${epStats.length} / ${eps.length} |`);
md.push(`| Scenes walked / expected | ${summary.totalScenesWalked} / ${summary.totalScenesExpected} |`);
md.push(`| Audio URLs found | ${summary.totalAudioUrls} |`);
md.push(`| ✓ reachable (200/206) | **${summary.totalAudioOk}** |`);
md.push(`| ✗ failed | **${summary.totalAudioFail}** |`);
md.push(`| Console errors | ${summary.consoleErrorsTotal} |`);
md.push(`| Aborted episodes | ${summary.abortedEpisodes.length} |`);
md.push(``);

if (failed.length) {
  md.push(`## Audio failures (${failed.length})`);
  md.push(``);
  // Group by status
  const byStatus = new Map();
  for (const [u, v] of failed) {
    const k = String(v.status || v.err || "?");
    (byStatus.get(k) || byStatus.set(k, []).get(k)).push(u);
  }
  for (const [k, urls] of [...byStatus.entries()].sort((a, b) => b[1].length - a[1].length)) {
    md.push(`### Status \`${k}\` — ${urls.length} URLs`);
    md.push(``);
    for (const u of urls.slice(0, 80)) md.push(`- \`${urlScene(u)}\` ← ${u}`);
    if (urls.length > 80) md.push(`- … +${urls.length - 80} more`);
    md.push(``);
  }
}

md.push(`## Per-episode`);
md.push(``);
md.push(`| ep | scenes | audio total | ✓ | ✗ | cons | aborted |`);
md.push(`|---|---:|---:|---:|---:|---:|---|`);
for (const r of epStats) {
  md.push(`| ep_${r.epPad} | ${r.scenesWalked?.length || 0}/${r.sceneCount || 0} | ${r.audioUrls?.length || 0} | ${r.audioOk} | ${r.audioFail} | ${r.consoleErrors?.length || 0} | ${r.aborted || ""} |`);
}
md.push(``);
md.push(`---`);
md.push(`Screenshots (audio-mode UI): \`screenshots/ep_NNN/\`. Full data: \`summary.json\`.`);

await fs.writeFile(path.join(runDir, "summary.md"), md.join("\n"));
log(`[run_audio] DONE → ${path.relative(process.cwd(), runDir)}/summary.md`);
log(`[run_audio] elapsed ${((Date.now() - runStarted) / 1000).toFixed(1)}s`);
await logStream.close();
