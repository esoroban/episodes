#!/usr/bin/env python3
"""
Artifact invariant: HTML text ≡ JSON manifest text.

For each built episode in server/game/ (RU) and server/game/uk/ (UK):
  1. Extract the set of user-visible strings from ep_NNN.html.
  2. Extract the same set from ep_NNN.json (manifest).
  3. Normalize (whitespace, HTML entities, speaker prefixes).
  4. Diff. If anything differs — FAIL with location.

Why this exists:
  Author reviews in HTML. Voice/image pipelines consume JSON. If these
  drift, approved edits are silently lost downstream. This check
  prevents that by construction: both are derived from the same data
  model via build_game.py; this tool is the trip-wire that fires if
  the derivation ever diverges.

Usage:
  python3 tools/validate_artifacts.py              # all built episodes, both langs
  python3 tools/validate_artifacts.py ep_001       # one episode (both langs)
  python3 tools/validate_artifacts.py ep_001 --lang ru
"""

import sys
import re
import json
import html as htmllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_RU = ROOT / "server" / "game" / "ru"
OUTPUT_UK = ROOT / "server" / "game" / "uk"


# ── Normalization ─────────────────────────────────────────────────

SPEAKER_DASH_RE = re.compile(r"^([А-ЯЁа-яё\w]+(?:\s+\d+)?)\s*:\s*—\s*(.*)$", re.DOTALL)
SOFA_QUOTED_RE = re.compile(r"^\U0001f4f1?\s*Софа\s*:\s*«(.*)»\s*$", re.DOTALL)
HEADER_TRASH = {
    "1A.1", "1A.2", "1B.1", "1B.2", "1B.3",
}


def norm(s: str) -> str:
    """Unescape + collapse whitespace + strip."""
    if not s:
        return ""
    s = htmllib.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def strip_html_decoration(s: str) -> str:
    """Strip speaker:— / 📱 Софа: «...» wrappers present in HTML drama blocks."""
    if not s:
        return s
    m = SPEAKER_DASH_RE.match(s)
    if m:
        return m.group(2).strip()
    m = SOFA_QUOTED_RE.match(s)
    if m:
        return m.group(1).strip()
    return s


# ── HTML extractor ────────────────────────────────────────────────

def html_texts(html_path: Path) -> set:
    """Return the set of user-visible strings in the rendered HTML."""
    text = html_path.read_text(encoding="utf-8")
    all_texts = []

    # 1. Embedded chat messages (Telegram scenes)
    for m in re.finditer(r'data-chat-messages="([^"]+)"', text):
        raw = htmllib.unescape(m.group(1))
        try:
            msgs = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for msg in msgs:
            x = msg.get("x")
            if isinstance(x, str):
                all_texts.append(norm(x))
            if msg.get("t") == "quiz":
                all_texts.append(norm(msg.get("q", "")))
                for opt in msg.get("o", []) or []:
                    all_texts.append(norm(opt.get("x", "")))
                if msg.get("fbFail"):
                    all_texts.append(norm(msg["fbFail"]))
            if msg.get("t") == "unlock":
                all_texts.append(norm(msg.get("x", "")))

    # 2. Standard (non-chat) DOM text — strip chrome before pattern matching.
    stripped = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    stripped = re.sub(r"<style[^>]*>.*?</style>", "", stripped, flags=re.DOTALL)
    stripped = re.sub(r'<div class="phone"[^>]*>.*?</div>\s*</section>', "</section>",
                      stripped, flags=re.DOTALL)
    # Debug burger menu — episode titles/scene labels aren't user-facing content.
    stripped = re.sub(r'<nav class="dbg-menu"[^>]*>.*?</nav>', "", stripped, flags=re.DOTALL)
    # Episode header (title, lesson, new terms) — metadata, not scene content.
    stripped = re.sub(r'<header class="episode-header"[^>]*>.*?</header>', "", stripped, flags=re.DOTALL)
    # End-screen (episode finale card with title echo).
    stripped = re.sub(r'<div class="end-screen"[^>]*>.*?</div>\s*</div>', "", stripped, flags=re.DOTALL)
    # Nav spacer / nav bar / previously card — no scene text.
    stripped = re.sub(r'<div class="nav-bar"[^>]*>.*?</div>', "", stripped, flags=re.DOTALL)

    patterns = [
        r"<p[^>]*>(.*?)</p>",
        r'<button class="quiz-option"[^>]*>(.*?)</button>',
        r'<button class="choice-option"[^>]*>(.*?)</button>',
        r'<div class="quiz-feedback[^"]*"[^>]*>(.*?)</div>',
        # NOTE: quiz-explanation (hidden correct_logic) intentionally excluded —
        # it's metadata, not shown to the player; JSON side skips it too.
    ]
    for pat in patterns:
        for m in re.finditer(pat, stripped, flags=re.DOTALL):
            inner = re.sub(r"<[^>]+>", "", m.group(1))
            all_texts.append(norm(inner))

    cleaned = set()
    for tt in all_texts:
        if not tt:
            continue
        stripped_t = strip_html_decoration(tt)
        if not stripped_t:
            continue
        if stripped_t in HEADER_TRASH:
            continue
        if stripped_t.startswith("Новые термины:") or stripped_t.startswith("Нові терміни:"):
            continue
        cleaned.add(stripped_t)
    return cleaned


# ── JSON extractor ────────────────────────────────────────────────

def json_texts(json_path: Path) -> set:
    """Return the set of user-visible strings from the per-episode manifest."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    out = set()
    for scene in data.get("scenes", []) or []:
        # Linear text blocks (author + dialogue)
        for t in scene.get("text", []) or []:
            line = norm(t.get("line", ""))
            if line:
                out.add(line)
        # Quizzes — compare only fields that RENDER in HTML.
        # correct_logic is metadata for downstream (image/voice) — NOT shown in chat
        # quizzes (per rule), shown only as hidden .quiz-explanation div in standard
        # quizzes. Drift-wise it's inherently uneven between two render paths; exclude
        # from invariant to keep the check meaningful.
        for q in scene.get("quizzes", []) or []:
            for k in ("question", "feedback_success", "feedback_soft_fail"):
                v = norm(q.get(k, ""))
                if v:
                    out.add(v)
            for opt in q.get("options", []) or []:
                t = norm(opt.get("text", ""))
                if t:
                    out.add(t)
        # Choice
        ch = scene.get("choice")
        if isinstance(ch, dict):
            q = norm(ch.get("question", ""))
            if q:
                out.add(q)
            for opt in ch.get("options", []) or []:
                t = norm(opt.get("text", ""))
                if t:
                    out.add(t)
        # Unlock
        un = scene.get("unlock")
        if isinstance(un, dict):
            t = norm(un.get("button_text", ""))
            if t:
                out.add(t)
            rev = un.get("reveals", {}) or {}
            line = norm(rev.get("line", ""))
            if line:
                out.add(line)
    return out


# ── Comparison ────────────────────────────────────────────────────

def compare_episode(html_path: Path, json_path: Path) -> tuple:
    """Return (ok, json_only, html_only) — both are sets."""
    h = html_texts(html_path)
    j = json_texts(json_path)
    return (h == j, j - h, h - j)


def audit_dir(output_dir: Path, label: str, only_eps: list = None) -> bool:
    """Validate all ep_*.html in output_dir against paired ep_*.json."""
    if not output_dir.exists():
        return True
    ok = True
    htmls = sorted(output_dir.glob("ep_*.html"))
    if only_eps:
        htmls = [p for p in htmls if p.stem in only_eps]
    if not htmls:
        return True
    print(f"\n[{label}]")
    for html_path in htmls:
        json_path = html_path.with_suffix(".json")
        if not json_path.exists():
            print(f"  ! {html_path.name}: no paired JSON (skip)")
            continue
        passed, json_only, html_only = compare_episode(html_path, json_path)
        status = "OK" if passed else "DRIFT"
        print(f"  {html_path.stem}: {status}")
        if not passed:
            ok = False
            if json_only:
                print(f"    JSON → not in HTML ({len(json_only)}):")
                for s in sorted(json_only)[:10]:
                    print(f"      - {s[:120]}")
                if len(json_only) > 10:
                    print(f"      ... +{len(json_only) - 10} more")
            if html_only:
                print(f"    HTML → not in JSON ({len(html_only)}):")
                for s in sorted(html_only)[:10]:
                    print(f"      + {s[:120]}")
                if len(html_only) > 10:
                    print(f"      ... +{len(html_only) - 10} more")
    return ok


def main():
    args = sys.argv[1:]
    lang_filter = None
    if "--lang" in args:
        i = args.index("--lang")
        lang_filter = args[i + 1] if i + 1 < len(args) else None
        args = args[:i] + args[i + 2:]
    only_eps = args or None

    ok = True
    if lang_filter in (None, "ru"):
        ok = audit_dir(OUTPUT_RU, "RU", only_eps) and ok
    if lang_filter in (None, "uk"):
        ok = audit_dir(OUTPUT_UK, "UK", only_eps) and ok

    if ok:
        print("\nAll artifacts in sync.")
        sys.exit(0)
    else:
        print("\nDRIFT DETECTED — HTML and JSON do not match. See diff above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
