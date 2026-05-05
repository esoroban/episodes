// Fire-and-forget end-to-end QA of prod v2/uk game.
// Walks every episode via the DEBUG ⏭ Дальше button (#v2-debug-next),
// inventories every R2 asset URL (images + audio MANIFEST), HEAD-probes them,
// captures console/page errors and HTTP failures, screenshots every scene.
// Outputs ONE consolidated markdown report you can read when you're back.
//
// Usage:
//   node run_full.mjs                 # all 36 episodes, headless, default
//   node run_full.mjs 1-12            # range
//   node run_full.mjs 1,5,12          # list
//   node run_full.mjs all headed      # headed (slower, watchable)
//
// Output: reports/qa_run_<ts>/
//   summary.md          ← read this first
//   summary.json        ← raw aggregate
//   ep_NNN.json         ← per-episode detail
//   screenshots/ep_NNN/ ← per-scene PNGs
//   log.txt             ← stdout copy
//
// Hard caps: 90min total wall-clock; per-ep 5min. Crashes are caught,
// run continues to next episode. Browser restarted between episodes
// for isolation.

import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_URL, TOTAL_EPISODES, VIEWPORT } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── args ──────────────────────────────────────────────────────────────
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

// ─── output paths ──────────────────────────────────────────────────────
const ts = new Date().toISOString().replace(/[:.]/g, "-").replace("T", "_").slice(0, 19);
const runDir = path.join(__dirname, "reports", `qa_run_${ts}`);
const shotsRoot = path.join(runDir, "screenshots");
const logPath = path.join(runDir, "log.txt");
await fs.mkdir(shotsRoot, { recursive: true });

const logStream = await fs.open(logPath, "w");
function log(...parts) {
  const line = parts.map((p) => (typeof p === "string" ? p : JSON.stringify(p))).join(" ");
  console.log(line);
  logStream.write(line + "\n");
}
log(`[run_full] start ts=${ts} eps=${eps.join(",")} headless=${headless}`);

// ─── per-ep walker ─────────────────────────────────────────────────────
const PER_EP_TIMEOUT_MS = 5 * 60 * 1000;
const TOTAL_TIMEOUT_MS = 90 * 60 * 1000;
const runStarted = Date.now();

async function walkEpisode(browser, ep) {
  const epPad = String(ep).padStart(3, "0");
  const url = EPISODE_URL(ep);
  const shotDir = path.join(shotsRoot, `ep_${epPad}`);
  await fs.mkdir(shotDir, { recursive: true });

  const result = {
    ep,
    epPad,
    url,
    started: new Date().toISOString(),
    sceneCount: 0,
    scenesWalked: [],
    consoleErrors: [],
    pageErrors: [],
    httpErrors: [],
    assets: { images: [], audio: [] },
    durationMs: 0,
    aborted: null,
  };

  const ctx = await browser.newContext({
    viewport: VIEWPORT,
    isMobile: true,
    hasTouch: true,
    locale: "uk-UA",
  });
  // Auto-dismiss any alerts (e.g. "end of episodes")
  ctx.on("page", (p) => p.on("dialog", (d) => { log(`[ep_${epPad}] dialog: ${d.message()}`); d.dismiss().catch(() => {}); }));

  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") result.consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => result.pageErrors.push(e.message));
  page.on("requestfailed", (req) => {
    result.httpErrors.push({ kind: "requestfailed", url: req.url(), err: req.failure()?.errorText });
  });
  page.on("response", (res) => {
    if (res.status() >= 400) result.httpErrors.push({ kind: "http", status: res.status(), url: res.url() });
  });

  const started = Date.now();
  try {
    await page.goto(url, { waitUntil: "load", timeout: 45000 });
    await page.waitForSelector("#v2-debug-next", { timeout: 15000 });
    await page.waitForTimeout(800);

    // Inventory assets from page
    const inv = await page.evaluate(() => {
      const out = { images: [], audio: [] };
      // Image URLs in HTML attributes
      const html = document.documentElement.outerHTML;
      const imgUrls = html.match(/https:\/\/pub-[a-f0-9]+\.r2\.dev\/[^\s"']+\.(png|jpg|jpeg|webp)/g) || [];
      out.images = Array.from(new Set(imgUrls));
      // Audio URLs from MANIFEST var
      try {
        if (typeof MANIFEST !== "undefined" && MANIFEST.tracks) {
          out.audio = MANIFEST.tracks.map((t) => t.audio_url).filter(Boolean);
        }
      } catch {}
      // Fallback: regex audio urls in HTML
      if (!out.audio.length) {
        const audUrls = html.match(/https:\/\/pub-[a-f0-9]+\.r2\.dev\/[^\s"']+\.(wav|mp3|m4a|ogg)/g) || [];
        out.audio = Array.from(new Set(audUrls));
      }
      return out;
    });
    result.assets = inv;

    // Scene count (excluding the previously / counter-only sections is not needed —
    // the dbgBtn iterates exactly section.scene)
    const sceneCount = await page.evaluate(() => document.querySelectorAll("section.scene").length);
    result.sceneCount = sceneCount;
    log(`[ep_${epPad}] loaded — scenes=${sceneCount} imgs=${inv.images.length} audio=${inv.audio.length}`);

    // Snapshot first active scene
    let activeId = await page.evaluate(() => {
      const a = document.querySelector("section.scene.active");
      return a ? (a.dataset.sceneId || a.id) : null;
    });
    if (activeId) {
      const file = path.join(shotDir, `000_${activeId.replace(/[^a-z0-9_-]/gi, "_")}.png`);
      await page.screenshot({ path: file, fullPage: false }).catch(() => {});
      result.scenesWalked.push({ idx: 0, sceneId: activeId });
    }

    // Click dbgBtn (sceneCount - 1) times — this advances through every scene
    // ignoring quizzes/chats/branches. Hard cap: 60 clicks.
    const maxClicks = Math.min(Math.max(sceneCount - 1, 0), 60);
    for (let i = 1; i <= maxClicks; i++) {
      if (Date.now() - started > PER_EP_TIMEOUT_MS) {
        result.aborted = "per-ep timeout"; break;
      }
      const before = activeId;
      await page.click("#v2-debug-next", { timeout: 5000 }).catch((e) => {
        result.aborted = `click failed: ${e.message}`;
      });
      if (result.aborted) break;
      await page.waitForTimeout(450);
      const after = await page.evaluate(() => {
        const a = document.querySelector("section.scene.active");
        return a ? (a.dataset.sceneId || a.id) : null;
      });
      if (after === before) {
        // dbgBtn didn't advance — maybe last scene tried to navigate to next ep.
        log(`[ep_${epPad}] active unchanged after click ${i} (was ${before}) — stopping`);
        break;
      }
      activeId = after;
      const file = path.join(shotDir, `${String(i).padStart(3, "0")}_${(activeId || "x").replace(/[^a-z0-9_-]/gi, "_")}.png`);
      await page.screenshot({ path: file, fullPage: false }).catch(() => {});
      result.scenesWalked.push({ idx: i, sceneId: activeId });
    }
  } catch (e) {
    result.aborted = `exception: ${e.message}`;
    log(`[ep_${epPad}] ERROR ${e.message}`);
  }
  result.durationMs = Date.now() - started;
  await ctx.close().catch(() => {});

  log(`[ep_${epPad}] done in ${result.durationMs}ms scenes=${result.scenesWalked.length}/${result.sceneCount} cons=${result.consoleErrors.length} pageerr=${result.pageErrors.length} http=${result.httpErrors.length} aborted=${result.aborted || "no"}`);
  await fs.writeFile(path.join(runDir, `ep_${epPad}.json`), JSON.stringify(result, null, 2));
  return result;
}

// ─── HEAD-probe assets ────────────────────────────────────────────────
async function headProbe(urls, concurrency = 16) {
  const results = new Map();
  const queue = [...urls];
  async function worker() {
    while (queue.length) {
      const u = queue.shift();
      try {
        const r = await fetch(u, { method: "HEAD", signal: AbortSignal.timeout(15000) });
        results.set(u, { status: r.status, ok: r.ok });
      } catch (e) {
        results.set(u, { status: 0, ok: false, err: e.message });
      }
    }
  }
  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return results;
}

// ─── main ─────────────────────────────────────────────────────────────
const browser = await chromium.launch({ headless });
const perEp = [];
for (const ep of eps) {
  if (Date.now() - runStarted > TOTAL_TIMEOUT_MS) {
    log(`[run_full] total timeout reached, stopping at ep_${ep}`);
    break;
  }
  try {
    perEp.push(await walkEpisode(browser, ep));
  } catch (e) {
    log(`[run_full] walkEpisode threw for ep_${ep}: ${e.message}`);
    perEp.push({ ep, epPad: String(ep).padStart(3, "0"), aborted: `threw: ${e.message}`, scenesWalked: [], consoleErrors: [], pageErrors: [], httpErrors: [], assets: { images: [], audio: [] } });
  }
}
await browser.close();

// ─── asset probe phase ────────────────────────────────────────────────
const allImages = new Set();
const allAudio = new Set();
for (const r of perEp) {
  for (const u of r.assets?.images || []) allImages.add(u);
  for (const u of r.assets?.audio || []) allAudio.add(u);
}
log(`[probe] HEAD-probing ${allImages.size} unique images + ${allAudio.size} unique audio…`);
const imgProbe = await headProbe(allImages);
const audProbe = await headProbe(allAudio);
const failedImg = [...imgProbe].filter(([_, v]) => !v.ok);
const failedAud = [...audProbe].filter(([_, v]) => !v.ok);
log(`[probe] failed: images=${failedImg.length}/${allImages.size} audio=${failedAud.length}/${allAudio.size}`);

// ─── summary ───────────────────────────────────────────────────────────
function urlToEpScene(url) {
  const m = url.match(/\/ep_(\d{3})\/[^/]+\/(?:ep\d{3}_)?([^/.]+)/);
  return m ? `ep_${m[1]}/${m[2]}` : url;
}

function dedupeBy(arr, keyFn) {
  const seen = new Map();
  for (const item of arr) {
    const k = keyFn(item);
    seen.set(k, (seen.get(k) || 0) + 1);
  }
  return [...seen.entries()].sort((a, b) => b[1] - a[1]);
}

const allConsole = perEp.flatMap((r) => (r.consoleErrors || []).map((t) => ({ ep: r.epPad, t })));
const allPageErr = perEp.flatMap((r) => (r.pageErrors || []).map((t) => ({ ep: r.epPad, t })));
const allHttp = perEp.flatMap((r) => (r.httpErrors || []).map((h) => ({ ep: r.epPad, ...h })));

const summary = {
  ts,
  eps: eps.length,
  totalScenesWalked: perEp.reduce((a, r) => a + (r.scenesWalked?.length || 0), 0),
  totalScenesExpected: perEp.reduce((a, r) => a + (r.sceneCount || 0), 0),
  abortedEpisodes: perEp.filter((r) => r.aborted).map((r) => ({ ep: r.epPad, reason: r.aborted })),
  consoleErrorsTotal: allConsole.length,
  pageErrorsTotal: allPageErr.length,
  httpErrorsTotal: allHttp.length,
  failedImageCount: failedImg.length,
  failedAudioCount: failedAud.length,
};
await fs.writeFile(path.join(runDir, "summary.json"), JSON.stringify({ summary, perEp, failedImg: Object.fromEntries(failedImg), failedAud: Object.fromEntries(failedAud) }, null, 2));

// ─── markdown summary ─────────────────────────────────────────────────
const md = [];
md.push(`# QA Run — v2/uk prod`);
md.push(``);
md.push(`**Start:** ${ts}    **Episodes:** ${eps.join(", ")}    **Mode:** ${headless ? "headless" : "headed"}`);
md.push(``);
md.push(`## TL;DR`);
md.push(``);
md.push(`| Metric | Count |`);
md.push(`|---|---:|`);
md.push(`| Episodes walked | ${perEp.length} / ${eps.length} |`);
md.push(`| Scenes walked / expected | ${summary.totalScenesWalked} / ${summary.totalScenesExpected} |`);
md.push(`| Console errors | ${summary.consoleErrorsTotal} |`);
md.push(`| Page errors | ${summary.pageErrorsTotal} |`);
md.push(`| HTTP failures | ${summary.httpErrorsTotal} |`);
md.push(`| Missing images (HEAD ≠ 200) | **${summary.failedImageCount}** / ${allImages.size} |`);
md.push(`| Missing audio (HEAD ≠ 200) | **${summary.failedAudioCount}** / ${allAudio.size} |`);
md.push(`| Aborted episodes | ${summary.abortedEpisodes.length} |`);
md.push(``);

if (summary.abortedEpisodes.length) {
  md.push(`## Aborted episodes`);
  md.push(``);
  for (const a of summary.abortedEpisodes) md.push(`- ep_${a.ep} — ${a.reason}`);
  md.push(``);
}

if (failedImg.length) {
  md.push(`## Missing images (${failedImg.length})`);
  md.push(``);
  for (const [u, v] of failedImg.slice(0, 200)) md.push(`- \`${urlToEpScene(u)}\` → ${v.status || v.err}  \n  ${u}`);
  if (failedImg.length > 200) md.push(`- … +${failedImg.length - 200} more (see summary.json)`);
  md.push(``);
}

if (failedAud.length) {
  md.push(`## Missing audio (${failedAud.length})`);
  md.push(``);
  for (const [u, v] of failedAud.slice(0, 200)) md.push(`- \`${urlToEpScene(u)}\` → ${v.status || v.err}  \n  ${u}`);
  if (failedAud.length > 200) md.push(`- … +${failedAud.length - 200} more (see summary.json)`);
  md.push(``);
}

if (allHttp.length) {
  md.push(`## HTTP failures by URL (top 30)`);
  md.push(``);
  const grouped = dedupeBy(allHttp, (e) => `${e.status || e.err || e.kind} ${e.url}`);
  for (const [k, n] of grouped.slice(0, 30)) md.push(`- ×${n}  ${k}`);
  md.push(``);
}

if (allConsole.length) {
  md.push(`## Console errors (top 30 by frequency)`);
  md.push(``);
  const grouped = dedupeBy(allConsole, (e) => e.t);
  for (const [k, n] of grouped.slice(0, 30)) md.push(`- ×${n}  ${k.slice(0, 200)}`);
  md.push(``);
}

if (allPageErr.length) {
  md.push(`## Page errors`);
  md.push(``);
  const grouped = dedupeBy(allPageErr, (e) => e.t);
  for (const [k, n] of grouped) md.push(`- ×${n}  ${k.slice(0, 200)}`);
  md.push(``);
}

md.push(`## Per-episode`);
md.push(``);
md.push(`| ep | scenes | cons | http | imgs | audio | aborted |`);
md.push(`|---|---:|---:|---:|---:|---:|---|`);
for (const r of perEp) {
  md.push(`| ep_${r.epPad} | ${r.scenesWalked?.length || 0}/${r.sceneCount || 0} | ${r.consoleErrors?.length || 0} | ${r.httpErrors?.length || 0} | ${r.assets?.images?.length || 0} | ${r.assets?.audio?.length || 0} | ${r.aborted || ""} |`);
}
md.push(``);
md.push(`---`);
md.push(`Screenshots: \`screenshots/ep_NNN/\`. Per-episode raw JSON: \`ep_NNN.json\`. Full aggregate: \`summary.json\`.`);

await fs.writeFile(path.join(runDir, "summary.md"), md.join("\n"));
log(`[run_full] DONE → ${path.relative(process.cwd(), runDir)}/summary.md`);
log(`[run_full] elapsed ${((Date.now() - runStarted) / 1000).toFixed(1)}s`);
await logStream.close();
