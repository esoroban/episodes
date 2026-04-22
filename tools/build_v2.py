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


PROD_OVERRIDES = (
    '<style id="v2-prod-overrides">'
    # Debug-панель из image_prompts_experiment перекрывает #btnNext на мобилках
    # (position:fixed; bottom:16px; right:16px; max-width:280px; z-index:9999).
    # В проде она не нужна — скрываем.
    '.ipe-debug{display:none!important}'
    # iOS Safari: position:fixed внутри .scene с animation+overflow:hidden
    # кидает .story-choice в неправильный containing block → кнопки не видны
    # в audio-mode. Уберём animation у .scene и форсируем story-choice
    # в собственный composition layer + учтём safe-area (bottom bar Safari).
    '.scene{animation:none!important}'
    '.story-choice{'
    'bottom:calc(80px + env(safe-area-inset-bottom,0px))!important;'
    'z-index:100!important;'
    'transform:translateZ(0);'
    '-webkit-transform:translateZ(0);'
    '}'
    '</style>\n'
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
    # Скрыть debug-панель на проде (перекрывает #btnNext на мобилках).
    html = html.replace("</head>", PROD_OVERRIDES + "</head>", 1)
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
