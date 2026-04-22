#!/usr/bin/env python3
"""Build v2 (combined) HTML bundle into server/v2/ with CDN-rewritten asset paths.

Reads: pipeline/gameflow/spec/r2_config.yaml (public URL)
Source: /Users/iuriinovosolov/Documents/image_prompts_experiment/combined_output/
        ep_NNN/ep_NNN.html  — HTML with quoted relative paths "audio/..." and "images/..."
        index.html          — episode list (self-contained)
Output: server/v2/ep_NNN/ep_NNN.html, server/v2/index.html

Rewrite rule — per episode NNN:
  "audio/FILE"   →  "<public_url>/ep_NNN/audio/FILE"
  "images/FILE"  →  "<public_url>/ep_NNN/images/FILE"

Usage:
  python3 tools/build_v2.py                     # all 12 episodes
  python3 tools/build_v2.py 1 2 3               # specific
  python3 tools/build_v2.py --src /other/path   # alternate source
"""
import argparse
import pathlib
import re
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SRC = pathlib.Path(
    "/Users/iuriinovosolov/Documents/image_prompts_experiment/combined_output"
)
LANG = "uk"  # combined_output — украинский; если появится RU-сборка, будет "ru"
OUT_DIR = REPO / "server" / "v2" / LANG
CONFIG = REPO / "pipeline" / "gameflow" / "spec" / "r2_config.yaml"


def load_public_url() -> str:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    url = cfg["public_url"].rstrip("/")
    return url


BODY_DEBUG_BUTTON = (
    '<button id="v2-dbg-skip" type="button" title="skip current audio (debug)" aria-label="Skip audio">⏭</button>\n'
)

PROD_OVERRIDES = (
    '<style id="v2-prod-overrides">'
    # Debug-панель из image_prompts_experiment перекрывает #btnNext на мобилках.
    '.ipe-debug{display:none!important}'
    # Debug skip-audio кнопка — маленькая, слева снизу, чтобы не мешала навигации.
    # Видна только в audio-mode (в text-mode аудио не играет).
    '#v2-dbg-skip{'
    'position:fixed;bottom:16px;left:16px;z-index:220;'
    'background:rgba(0,0,0,0.55);color:#fff;'
    'border:1px solid rgba(255,255,255,0.22);border-radius:6px;'
    'padding:4px 10px;font-size:14px;line-height:1;'
    'font-family:-apple-system,BlinkMacSystemFont,sans-serif;'
    'cursor:pointer;opacity:0.5;display:none;'
    '}'
    'body.audio-mode #v2-dbg-skip{display:block}'
    '#v2-dbg-skip:hover{opacity:1}'
    # iOS Safari: `animation: fadeIn` с transform:translateY() на .scene
    # оставляет element в качестве containing block для position:fixed
    # даже после анимации → .story-choice (fixed;bottom:80px) попадает за
    # overflow:hidden. Убираем анимацию.
    '.scene{animation:none!important}'
    # UX: в audio-mode кнопки выбора бранча должны появляться ТОЛЬКО после
    # того, как автор дочитал текст. Класс `.audio-done` ставится JS-ом
    # (см. <script id="v2-audio-done-tracker"> ниже) когда Audio-очередь
    # для активной сцены опустела. В text-mode класс ставится сразу.
    'body.audio-mode section.scene:not(.audio-done) .story-choice{'
    'display:none!important'
    '}'
    '</style>\n'
    '<script id="v2-audio-done-tracker">\n'
    '(function () {\n'
    '  var playingSet = new Set();\n'
    '  var sceneStates = new WeakMap();\n'
    '\n'
    '  // Patch HTMLAudioElement.prototype.play: на первый play() на каждом\n'
    '  // аудио-элементе навешиваем трекинг. Работает для ЛЮБОГО способа\n'
    '  // создания: new Audio(), document.createElement("audio"), <audio>-тэгов.\n'
    '  var origPlay = HTMLAudioElement.prototype.play;\n'
    '  HTMLAudioElement.prototype.play = function () {\n'
    '    var a = this;\n'
    '    if (!a.__v2Tracked) {\n'
    '      a.__v2Tracked = true;\n'
    '      a.addEventListener("play",  function () { playingSet.add(a); });\n'
    '      a.addEventListener("pause", function () { playingSet.delete(a); });\n'
    '      a.addEventListener("ended", function () { playingSet.delete(a); });\n'
    '      a.addEventListener("error", function () { playingSet.delete(a); });\n'
    '    }\n'
    '    return origPlay.apply(a, arguments);\n'
    '  };\n'
    '\n'
    '  function anyPlaying() {\n'
    '    var r = false;\n'
    '    playingSet.forEach(function (a) { if (!a.paused && !a.ended) r = true; });\n'
    '    return r;\n'
    '  }\n'
    '\n'
    '  function check() {\n'
    '    var active = document.querySelector(".scene.active");\n'
    '    if (!active) return;\n'
    '    if (!document.body.classList.contains("audio-mode")) {\n'
    '      active.classList.add("audio-done");\n'
    '      return;\n'
    '    }\n'
    '    var st = sceneStates.get(active);\n'
    '    if (!st) { st = { enteredAt: Date.now(), hadAudio: false }; sceneStates.set(active, st); }\n'
    '    if (anyPlaying()) {\n'
    '      st.hadAudio = true;\n'
    '      active.classList.remove("audio-done");\n'
    '      return;\n'
    '    }\n'
    '    if (st.hadAudio) { active.classList.add("audio-done"); return; }\n'
    '    // Сцена без аудио → через 3 сек всё равно показать choice.\n'
    '    if (Date.now() - st.enteredAt > 3000) active.classList.add("audio-done");\n'
    '  }\n'
    '\n'
    '  function onSceneActivated(scene) {\n'
    '    sceneStates.set(scene, { enteredAt: Date.now(), hadAudio: false });\n'
    '    scene.classList.remove("audio-done");\n'
    '  }\n'
    '\n'
    '  function init() {\n'
    '    document.querySelectorAll("section.scene").forEach(function (s) {\n'
    '      var wasActive = s.classList.contains("active");\n'
    '      if (wasActive) onSceneActivated(s);\n'
    '      s.__v2WasActive = wasActive;\n'
    '      new MutationObserver(function () {\n'
    '        var nowActive = s.classList.contains("active");\n'
    '        if (nowActive && !s.__v2WasActive) onSceneActivated(s);\n'
    '        s.__v2WasActive = nowActive;\n'
    '      }).observe(s, { attributes: true, attributeFilter: ["class"] });\n'
    '    });\n'
    '    setInterval(check, 300);\n'
    '    // Debug-кнопка: скип текущей аудио-реплики.\n'
    '    var skipBtn = document.getElementById("v2-dbg-skip");\n'
    '    if (skipBtn) {\n'
    '      skipBtn.addEventListener("click", function (e) {\n'
    '        e.stopPropagation();\n'
    '        playingSet.forEach(function (a) {\n'
    '          try { a.currentTime = (a.duration && isFinite(a.duration)) ? a.duration : 9999; } catch (_) {}\n'
    '          try { a.pause(); } catch (_) {}\n'
    '          try { a.dispatchEvent(new Event("ended")); } catch (_) {}\n'
    '        });\n'
    '      });\n'
    '    }\n'
    '  }\n'
    '\n'
    '  if (document.readyState === "loading") {\n'
    '    document.addEventListener("DOMContentLoaded", init);\n'
    '  } else {\n'
    '    init();\n'
    '  }\n'
    '})();\n'
    '</script>\n'
)


def rewrite_html(html: str, public_url: str, nnn: str) -> tuple[str, int, int]:
    """Return (rewritten_html, n_audio, n_images) counts of rewrites done."""
    base = f"{public_url}/ep_{nnn}"

    # Match "audio/<filename>" or "images/<filename>" in double quotes
    audio_pat = re.compile(r'"audio/([^"]+)"')
    image_pat = re.compile(r'"images/([^"]+)"')

    n_audio = 0
    n_images = 0

    def sub_audio(m: re.Match) -> str:
        nonlocal n_audio
        n_audio += 1
        return f'"{base}/audio/{m.group(1)}"'

    def sub_image(m: re.Match) -> str:
        nonlocal n_images
        n_images += 1
        return f'"{base}/images/{m.group(1)}"'

    html = audio_pat.sub(sub_audio, html)
    html = image_pat.sub(sub_image, html)
    # Инжекция prod-overrides (CSS + audio-done tracker) в <head>
    # и debug-skip-кнопки сразу после <body>.
    html = html.replace("</head>", PROD_OVERRIDES + "</head>", 1)
    html = html.replace("<body>", "<body>\n" + BODY_DEBUG_BUTTON, 1)
    return html, n_audio, n_images


def build_episode(src: pathlib.Path, nnn: str, public_url: str) -> dict:
    src_html = src / f"ep_{nnn}" / f"ep_{nnn}.html"
    if not src_html.exists():
        return {"nnn": nnn, "skipped": True, "reason": f"missing {src_html}"}

    html = src_html.read_text(encoding="utf-8")
    rewritten, n_audio, n_images = rewrite_html(html, public_url, nnn)

    out_html = OUT_DIR / f"ep_{nnn}" / f"ep_{nnn}.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(rewritten, encoding="utf-8")

    return {
        "nnn": nnn,
        "skipped": False,
        "audio": n_audio,
        "images": n_images,
        "out": out_html,
    }


BACK_LINK = (
    '<a href="/" style="display:inline-block;margin:0 auto 1rem;'
    'max-width:720px;width:100%;color:#8a8a8a;font-size:0.85rem;'
    'text-decoration:none;font-family:ui-monospace,SFMono-Regular,Menlo,monospace">'
    '← Главное меню</a>\n'
)


def build_index(src: pathlib.Path) -> pathlib.Path:
    src_idx = src / "index.html"
    out_idx = OUT_DIR / "index.html"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html = src_idx.read_text(encoding="utf-8")
    html = html.replace("<body>", "<body>\n" + BACK_LINK, 1)
    out_idx.write_text(html, encoding="utf-8")
    return out_idx


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "episodes",
        nargs="*",
        help="Episode numbers (e.g. 1 2 5). Default — all 1..12",
    )
    p.add_argument("--src", default=str(DEFAULT_SRC))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    src = pathlib.Path(args.src).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        return 2

    public_url = load_public_url()
    print(f"public_url = {public_url}")
    print(f"source     = {src}")
    print(f"target     = {OUT_DIR}")

    if args.episodes:
        nums = [int(x) for x in args.episodes]
    else:
        nums = list(range(1, 13))
    nnns = [f"{n:03d}" for n in nums]

    idx_out = build_index(src)
    print(f"index      → {idx_out.relative_to(REPO)}")

    total_audio = 0
    total_images = 0
    built = 0
    skipped = []
    for nnn in nnns:
        r = build_episode(src, nnn, public_url)
        if r["skipped"]:
            skipped.append((nnn, r["reason"]))
            print(f"ep_{nnn}     — SKIP ({r['reason']})")
            continue
        built += 1
        total_audio += r["audio"]
        total_images += r["images"]
        print(f"ep_{nnn}     → {r['out'].relative_to(REPO)}  "
              f"(audio: {r['audio']}, images: {r['images']})")

    print()
    print(f"built {built}/{len(nnns)} episodes")
    print(f"rewrites — audio: {total_audio}, images: {total_images}")
    if skipped:
        print(f"skipped {len(skipped)}:")
        for nnn, reason in skipped:
            print(f"  ep_{nnn}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
