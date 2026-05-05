// Generates a single index.html that links to the latest text-mode and
// audio-mode QA runs side-by-side. Each linked report becomes a
// browser-friendly HTML page with the markdown rendered inline.
//
// Usage:
//   node build_html_reports.mjs
//
// Output: reports/index.html  (open this in a browser)

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const reportsDir = path.join(__dirname, "reports");

async function listRuns(prefix) {
  const entries = await fs.readdir(reportsDir).catch(() => []);
  return entries
    .filter((e) => e.startsWith(prefix))
    .sort()
    .reverse();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Tiny markdown → HTML (just enough for our summaries: headers, tables, lists, code, bold).
function md2html(md) {
  const lines = md.split("\n");
  const out = [];
  let inTable = false;
  let tableHeaderEmitted = false;
  let inList = false;

  function closeBlocks() {
    if (inTable) { out.push("</tbody></table>"); inTable = false; tableHeaderEmitted = false; }
    if (inList) { out.push("</ul>"); inList = false; }
  }

  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    if (/^\s*$/.test(ln)) { closeBlocks(); continue; }

    // Table row
    if (/^\s*\|.*\|\s*$/.test(ln)) {
      const cells = ln.trim().slice(1, -1).split("|").map((c) => c.trim());
      const isSep = cells.every((c) => /^[-:]+$/.test(c));
      if (isSep) { tableHeaderEmitted = true; continue; }
      if (!inTable) {
        if (inList) { out.push("</ul>"); inList = false; }
        out.push("<table><thead>");
        inTable = true;
        tableHeaderEmitted = false;
      }
      const tag = !tableHeaderEmitted ? "th" : "td";
      if (!tableHeaderEmitted) {
        out.push("<tr>" + cells.map((c) => `<${tag}>${inlineMd(c)}</${tag}>`).join("") + "</tr>");
        // peek next line: if separator follows, close thead
        const nextIsSep = lines[i + 1] && /^\s*\|[-:\s|]+\|\s*$/.test(lines[i + 1]);
        if (nextIsSep) { out.push("</thead><tbody>"); }
      } else {
        out.push("<tr>" + cells.map((c) => `<td>${inlineMd(c)}</td>`).join("") + "</tr>");
      }
      continue;
    }

    if (/^### /.test(ln)) { closeBlocks(); out.push(`<h3>${inlineMd(ln.slice(4))}</h3>`); continue; }
    if (/^## /.test(ln))  { closeBlocks(); out.push(`<h2>${inlineMd(ln.slice(3))}</h2>`); continue; }
    if (/^# /.test(ln))   { closeBlocks(); out.push(`<h1>${inlineMd(ln.slice(2))}</h1>`); continue; }
    if (/^---\s*$/.test(ln)) { closeBlocks(); out.push("<hr>"); continue; }

    if (/^- /.test(ln)) {
      if (!inList) { closeBlocks(); out.push("<ul>"); inList = true; }
      out.push(`<li>${inlineMd(ln.slice(2))}</li>`);
      continue;
    }

    closeBlocks();
    out.push(`<p>${inlineMd(ln)}</p>`);
  }
  closeBlocks();
  return out.join("\n");
}

function inlineMd(s) {
  let out = escapeHtml(s);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return out;
}

const PAGE_CSS = `
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1.5rem; background: #0d0d12; color: #e8e6e3;
       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.55; }
.wrap { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.75rem; margin: 0 0 1rem; }
h2 { font-size: 1.2rem; margin: 2rem 0 0.6rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a2a35; color: #c7b8e8; }
h3 { font-size: 1rem; margin: 1.4rem 0 0.4rem; color: #d8a657; }
a { color: #c7b8e8; }
code { background: #1c1c28; padding: 0.1rem 0.35rem; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.88em; }
table { border-collapse: collapse; margin: 0.6rem 0 1.2rem; font-size: 0.92rem; width: 100%; }
th, td { padding: 0.4rem 0.7rem; border: 1px solid #2a2a35; text-align: left; vertical-align: top; }
th { background: #16161e; color: #c7b8e8; font-weight: 600; letter-spacing: 0.02em; }
tbody tr:nth-child(odd) { background: #11111a; }
ul { padding-left: 1.4rem; }
li { margin: 0.15rem 0; }
hr { border: none; border-top: 1px solid #2a2a35; margin: 2rem 0; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }
.card { background: #16161e; border: 1px solid #2a2a35; border-radius: 12px; padding: 1.2rem 1.4rem; text-decoration: none; color: #e8e6e3; }
.card:hover { border-color: #c7b8e8; }
.card h2 { border: none; padding: 0; margin: 0 0 0.4rem; font-size: 1.05rem; color: #c7b8e8; }
.card .meta { color: #8a8a8a; font-size: 0.85rem; margin-bottom: 0.6rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.card .stat { font-size: 0.92rem; }
.fail { color: #ff7b7b; font-weight: 600; }
.ok { color: #7fb069; font-weight: 600; }
.subtle { color: #8a8a8a; font-size: 0.82rem; }
.toolbar { font-size: 0.85rem; margin-bottom: 1rem; color: #8a8a8a; }
`;

function pageWrap(title, body) {
  return `<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${PAGE_CSS}</style></head><body><div class="wrap">${body}</div></body></html>`;
}

async function buildRunPage(runFolder, headline) {
  const runPath = path.join(reportsDir, runFolder);
  let summaryMd = await fs.readFile(path.join(runPath, "summary.md"), "utf-8").catch(() => null);
  if (!summaryMd) return null;

  let banner = "";
  // The text-mode run had a rate-limited HEAD probe (R2 returned 429).
  // Strip those sections from the rendered HTML and show a banner instead.
  if (runFolder.startsWith("qa_run_2")) {
    const audioFailRe = /\n## Missing audio \(\d+\)[\s\S]*?(?=\n## |\n---|$)/;
    const tldrAudioRe = /\n\| Missing audio.*\|.*\|/;
    if (audioFailRe.test(summaryMd) || tldrAudioRe.test(summaryMd)) {
      banner = `<div style="background:#3a2010;border:1px solid #ff7b30;padding:0.8rem 1rem;border-radius:8px;margin:0 0 1.5rem;color:#ffc69a;font-size:0.92rem">
        ⚠ HEAD-проба audio в этом прогоне получила массовые <code>429 Too Many Requests</code> от R2 (rate-limit, не реальные пропажи).
        Точная картина по озвучке — в карточке <strong>Audio coverage</strong>.
      </div>`;
      summaryMd = summaryMd.replace(audioFailRe, "");
      summaryMd = summaryMd.replace(tldrAudioRe, "");
    }
  }

  const html = pageWrap(`${headline} — ${runFolder}`,
    `<div class="toolbar">← <a href="../index.html">все прогоны</a> · raw: <a href="summary.md">summary.md</a> · <a href="summary.json">summary.json</a></div>` +
    banner +
    md2html(summaryMd)
  );
  const outPath = path.join(runPath, "summary.html");
  await fs.writeFile(outPath, html);
  return outPath;
}

async function loadSummaryStats(runFolder) {
  try {
    const j = JSON.parse(await fs.readFile(path.join(reportsDir, runFolder, "summary.json"), "utf-8"));
    return j.summary || {};
  } catch { return {}; }
}

const textRuns = await listRuns("qa_run_2");
const audioRuns = await listRuns("qa_run_audio_");
const checklistRuns = await listRuns("checklist_");
const latestText = textRuns[0];
const latestAudio = audioRuns[0];
const latestChecklist = checklistRuns[0];

let textCard = "<div class='card'><h2>Text-mode run</h2><div class='meta'>(нет прогонов)</div></div>";
let audioCard = "<div class='card'><h2>Audio-mode run</h2><div class='meta'>(нет прогонов)</div></div>";

if (latestText) {
  await buildRunPage(latestText, "Text-mode QA");
  const s = await loadSummaryStats(latestText);
  const renderClean = !(s.consoleErrorsTotal || s.pageErrorsTotal || s.abortedEpisodes?.length);
  textCard = `
<a class="card" href="${latestText}/summary.html">
  <h2>Text-mode run · автор-текст</h2>
  <div class="meta">${latestText}</div>
  <div class="stat">Episodes: ${s.eps ?? "?"} · Scenes: ${s.totalScenesWalked ?? "?"}/${s.totalScenesExpected ?? "?"}</div>
  <div class="stat">Console errors: <span class="${(s.consoleErrorsTotal || 0) ? "fail" : "ok"}">${s.consoleErrorsTotal ?? "?"}</span> · Page errors: <span class="${(s.pageErrorsTotal || 0) ? "fail" : "ok"}">${s.pageErrorsTotal ?? "?"}</span></div>
  <div class="stat">Missing images: <span class="${(s.failedImageCount || 0) ? "fail" : "ok"}">${s.failedImageCount ?? "?"}</span></div>
  <div class="subtle">Audio coverage → отдельная карточка справа.${renderClean ? " · render clean ✓" : ""} · Aborted: ${s.abortedEpisodes?.length ?? 0}</div>
</a>`;
}
if (latestAudio) {
  await buildRunPage(latestAudio, "Audio-coverage QA");
  const s = await loadSummaryStats(latestAudio);
  const audioClean = !(s.totalAudioFail || s.abortedEpisodes?.length);
  audioCard = `
<a class="card" href="${latestAudio}/summary.html">
  <h2>Audio coverage · озвучка</h2>
  <div class="meta">${latestAudio}</div>
  <div class="stat">Episodes: ${s.eps ?? "?"} · Scenes: ${s.totalScenesWalked ?? "?"}/${s.totalScenesExpected ?? "?"}</div>
  <div class="stat">Audio URLs: ${s.totalAudioUrls ?? "?"} · ✓ <span class="ok">${s.totalAudioOk ?? "?"}</span> · <span class="${(s.totalAudioFail || 0) ? "fail" : "ok"}">✗ ${s.totalAudioFail ?? "?"}</span></div>
  <div class="stat">Console: <span class="${(s.consoleErrorsTotal || 0) ? "fail" : "ok"}">${s.consoleErrorsTotal ?? "?"}</span> · Page: <span class="${(s.pageErrorsTotal || 0) ? "fail" : "ok"}">${s.pageErrorsTotal ?? "?"}</span></div>
  <div class="subtle">${audioClean ? "audio coverage clean ✓ · " : ""}Aborted: ${s.abortedEpisodes?.length ?? 0}</div>
</a>`;
}

const allRunsList = [...textRuns.map((r) => ({ folder: r, kind: "text" })), ...audioRuns.map((r) => ({ folder: r, kind: "audio" }))]
  .sort((a, b) => b.folder.localeCompare(a.folder));

const archive = allRunsList.length > 2
  ? `<h2>История прогонов</h2><ul>${allRunsList.slice(2).map((r) => `<li>[${r.kind}] <a href="${r.folder}/summary.html">${r.folder}</a></li>`).join("")}</ul>`
  : "";

// Checklist card
let checklistCard = "";
if (latestChecklist) {
  // Build a minimal HTML page for the checklist
  const cl = path.join(reportsDir, latestChecklist);
  const md = await fs.readFile(path.join(cl, "result.md"), "utf-8").catch(() => null);
  if (md) {
    await fs.writeFile(path.join(cl, "result.html"),
      pageWrap(`Release checklist — ${latestChecklist}`,
        `<div class="toolbar">← <a href="../index.html">все прогоны</a> · raw: <a href="result.md">result.md</a></div>` +
        md2html(md)
      ));
    // count failures
    const fails = (md.match(/^- ❌/gm) || []).length;
    const warns = (md.match(/^- ⚠/gm) || []).length;
    const okN = (md.match(/^- ✅/gm) || []).length;
    checklistCard = `
<a class="card" href="${latestChecklist}/result.html" style="grid-column: 1/-1">
  <h2>Release checklist · 9 пунктов</h2>
  <div class="meta">${latestChecklist}</div>
  <div class="stat">✅ ${okN} · <span class="${warns ? "fail" : "ok"}">⚠ ${warns}</span> · <span class="${fails ? "fail" : "ok"}">❌ ${fails}</span></div>
  <div class="subtle">Точечные проверки: chat-images ep_014/033 · ep_037 s03/s06 · 🔇/🔊 toggle · ep_040 endpoint</div>
</a>`;
  }
}

const indexBody = `
<h1>QA — v2/uk prod (episodes-zymk.onrender.com)</h1>
<p class="subtle">Сгенерировано ${new Date().toISOString()}.</p>
<div class="cards">
${textCard}
${audioCard}
${checklistCard}
</div>
<p>📂 raw отчёты и скриншоты лежат в <code>pipeline/qa/browser/reports/&lt;run&gt;/</code>.</p>
${archive}
`;

const indexPath = path.join(reportsDir, "index.html");
await fs.writeFile(indexPath, pageWrap("Сила Слова — QA reports", indexBody));
console.log(`[reports] index → ${indexPath}`);
console.log(`[reports] open: file://${indexPath}`);
