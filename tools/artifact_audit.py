#!/usr/bin/env python3
"""
Prototype audit: does current HTML for Day 1 equal current YAML text?

For each episode:
  1. Walk YAML scenes, collect all user-visible text fields (author_text,
     dialogue lines, question, options.text, feedback_success, etc.).
  2. Parse HTML — extract all visible text from scene sections, <details>,
     embedded chat messages (JSON in data-chat-messages attribute).
  3. Normalize (whitespace, html entities).
  4. Diff: strings in YAML not in HTML, strings in HTML not in YAML.

If diff is empty → architecture (JSON intermediate + HTML/JSON invariant) safe.
If diff exists → investigate before refactoring.

Usage:
  python3 tools/artifact_audit.py         # all Day 1
  python3 tools/artifact_audit.py ep_001  # single
"""

import sys
import json
import html
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMEFLOW_DIR = ROOT / "pipeline" / "gameflow" / "episodes"
HTML_DIR = ROOT / "server" / "game"


SPEAKER_DASH_RE = re.compile(r"^([А-ЯЁа-яё\w]+)\s*:\s*—\s*(.*)$", re.DOTALL)
SOFA_QUOTED_RE = re.compile(r"^\U0001f4f1?\s*Софа\s*:\s*«(.*)»\s*$", re.DOTALL)
HEADER_TRASH = {
    "1A.1", "1A.2", "1B.1", "1B.2", "1B.3",
    "Эпизод 1 — «Утро без сестры»",
    "Эпизод 2 — «Неправда и её виды»",
    "Эпизод 3 — «Хитрые утверждения»",
    "Эпизод 4 — «Детектив правды»",
    "«Утро без сестры»",
    "«Неправда и её виды»",
    "«Хитрые утверждения»",
    "«Детектив правды»",
}


def norm(s: str) -> str:
    """Collapse whitespace, unescape HTML entities, strip."""
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def strip_html_decoration(s: str) -> str:
    """Strip render-side decoration that is not in YAML text."""
    if not s:
        return s
    # «Марко: — text», «Вера: — text» — strip speaker+dash
    m = SPEAKER_DASH_RE.match(s)
    if m:
        return m.group(2).strip()
    # «📱 Софа: «line»» — strip Sofa speaker + guillemets
    m = SOFA_QUOTED_RE.match(s)
    if m:
        return m.group(1).strip()
    return s


def yaml_texts(yaml_path: Path) -> dict:
    """Extract per-scene text bag from YAML."""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    result = {}
    for scene in data.get("scenes", []) or []:
        sid = scene.get("scene_id", "?")
        bag = []
        # narrative
        for fld in ("author_text", "author_text_after"):
            v = scene.get(fld)
            if isinstance(v, str) and v.strip():
                # split into paragraphs (renderer splits on \n)
                for p in v.split("\n"):
                    p = norm(p)
                    if p:
                        bag.append(p)
        # dialogue lines (who + line both appear in HTML)
        for fld in ("dialogue", "dialogue_after"):
            for d in scene.get(fld, []) or []:
                if isinstance(d, dict):
                    line = norm(d.get("line", ""))
                    if line:
                        bag.append(line)
        # quiz question
        q = norm(scene.get("question", ""))
        if q:
            bag.append(q)
        # options text
        for opt in scene.get("options", []) or []:
            if isinstance(opt, dict):
                t = norm(opt.get("text", ""))
                if t:
                    bag.append(t)
        # feedback_success (both chat wq-ok and standard quiz-feedback-ok)
        fb_ok = norm(scene.get("feedback_success", ""))
        if fb_ok:
            bag.append(fb_ok)
        # feedback_soft_fail (inline on wrong in chat; also in standard quiz)
        fb_fail = norm(scene.get("feedback_soft_fail", ""))
        if fb_fail:
            bag.append(fb_fail)
        # interactions list
        for inter in scene.get("interactions", []) or []:
            if isinstance(inter, dict):
                iq = norm(inter.get("question", ""))
                if iq:
                    bag.append(iq)
                for opt in inter.get("options", []) or []:
                    if isinstance(opt, dict):
                        t = norm(opt.get("text", ""))
                        if t:
                            bag.append(t)
                ifb_ok = norm(inter.get("feedback_success", ""))
                if ifb_ok:
                    bag.append(ifb_ok)
                ifb_fail = norm(inter.get("feedback_soft_fail", ""))
                if ifb_fail:
                    bag.append(ifb_fail)
        # followup_interaction
        fu = scene.get("followup_interaction", {}) or {}
        if isinstance(fu, dict):
            fq = norm(fu.get("question", ""))
            if fq:
                bag.append(fq)
            for opt in fu.get("options", []) or []:
                if isinstance(opt, dict):
                    t = norm(opt.get("text", ""))
                    if t:
                        bag.append(t)
            ffb_ok = norm(fu.get("feedback_success", ""))
            if ffb_ok:
                bag.append(ffb_ok)
            ffb_fail = norm(fu.get("feedback_soft_fail", ""))
            if ffb_fail:
                bag.append(ffb_fail)
        # unlock_button
        unlock = scene.get("unlock_button")
        if isinstance(unlock, dict):
            t = norm(unlock.get("text", ""))
            if t:
                bag.append(t)
            rev = unlock.get("reveals", {}) or {}
            rl = norm(rev.get("line", ""))
            if rl:
                bag.append(rl)
        result[sid] = bag
    return result


def html_scene_texts(html_path: Path) -> dict:
    """Extract per-scene text bag from HTML.

    For each <section class="scene"> with data-scene-id, collect:
      - all text inside <p>, <div class="author-text">, <div class="dialogue-block">
      - quiz question / options / feedback
      - all text from chat messages (embedded JSON in phone[data-chat-messages])
    Returns {scene_id: [text strings]}.

    NOTE: this handles BOTH single-scene and chain-scene rendering. For
    chains, the scene section's data-scene-id is the FIRST scene in the
    chain, and all chain-scene texts are merged under that id. We bucket
    by data-scene-id as-is; the YAML side is per-scene. To compare, we'll
    take the UNION (all text across episode) rather than per-scene match,
    because chains merge multiple scene_ids in HTML.
    """
    text = html_path.read_text(encoding="utf-8")
    all_texts = []

    # 1. Embedded chat messages (JSON in data-chat-messages attr)
    for m in re.finditer(r'data-chat-messages="([^"]+)"', text):
        raw = html.unescape(m.group(1))
        try:
            msgs = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for msg in msgs:
            # text bubble / voiceover
            x = msg.get("x")
            if isinstance(x, str):
                all_texts.append(norm(x))
            # quiz
            if msg.get("t") == "quiz":
                all_texts.append(norm(msg.get("q", "")))
                for opt in msg.get("o", []) or []:
                    all_texts.append(norm(opt.get("x", "")))
                fb_fail = msg.get("fbFail")
                if fb_fail:
                    all_texts.append(norm(fb_fail))
            # unlock
            if msg.get("t") == "unlock":
                all_texts.append(norm(msg.get("x", "")))

    # 2. Standard (non-chat) scene content — <section class="scene"> blocks
    # Find every scene section and extract visible text (excluding scripts,
    # meta details, and phone data-chat-messages which we already got).

    # Quick-and-dirty: strip scripts/styles/phone containers, then grep <p>/<div class="author-text">
    stripped = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    stripped = re.sub(r"<style[^>]*>.*?</style>", "", stripped, flags=re.DOTALL)
    # Remove phone containers (chat messages already parsed above)
    stripped = re.sub(r'<div class="phone"[^>]*>.*?</div>\s*</section>', "</section>", stripped, flags=re.DOTALL)

    # Extract <p>...</p>, <div class="quiz-question">, option buttons, feedbacks
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    for m in re.finditer(r'<p class="quiz-question">(.*?)</p>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    for m in re.finditer(r'<button class="quiz-option"[^>]*>(.*?)</button>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    for m in re.finditer(r'<button class="choice-option"[^>]*>(.*?)</button>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    for m in re.finditer(r'<div class="quiz-feedback[^"]*"[^>]*>(.*?)</div>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    for m in re.finditer(r'<div class="quiz-explanation"[^>]*>(.*?)</div>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))
    # Choice-question
    for m in re.finditer(r'<p class="choice-question">(.*?)</p>', stripped, flags=re.DOTALL):
        inner = re.sub(r"<[^>]+>", "", m.group(1))
        all_texts.append(norm(inner))

    # Clean, strip speaker decoration, drop header chrome, dedupe.
    cleaned = set()
    for tt in all_texts:
        if not tt:
            continue
        stripped = strip_html_decoration(tt)
        if not stripped:
            continue
        if stripped in HEADER_TRASH:
            continue
        if stripped.startswith("Новые термины:"):
            continue
        cleaned.add(stripped)
    return cleaned


def check_chat_scene_no_external_author_text(html_path: Path) -> list:
    """Check 20 (post-build): chat scenes (with .phone) must not contain
    an external <div class="author-text"> — that is a duplicate render of
    what's already inside the chat as voice-over. Returns list of offenders."""
    text = html_path.read_text(encoding="utf-8")
    offenders = []
    for m in re.finditer(
        r'<section class="scene scene-[^"]+"\s+data-scene-id="([^"]+)"[^>]*>(.*?)</section>',
        text,
        re.DOTALL,
    ):
        sid = m.group(1)
        body = m.group(2)
        if '<div class="phone"' in body and '<div class="author-text">' in body:
            offenders.append(sid)
    return offenders


def audit_episode(ep: str) -> bool:
    yaml_path = GAMEFLOW_DIR / f"{ep}.yaml"
    html_path = HTML_DIR / f"{ep}.html"
    if not yaml_path.exists() or not html_path.exists():
        print(f"  ! {ep}: missing files")
        return False

    yaml_bag = yaml_texts(yaml_path)
    yaml_flat = set()
    for bag in yaml_bag.values():
        yaml_flat.update(bag)

    html_flat = html_scene_texts(html_path)

    # Compare
    yaml_only = yaml_flat - html_flat
    html_only = html_flat - yaml_flat

    offenders = check_chat_scene_no_external_author_text(html_path)

    status = "OK" if not yaml_only and not html_only and not offenders else "DRIFT"
    print(f"{ep}: {status}  (yaml: {len(yaml_flat)}  html: {len(html_flat)})")
    if offenders:
        print(f"  EXTERNAL author-text in chat scene(s) ({len(offenders)}):")
        for sid in offenders:
            print(f"    ! {sid} — chat-сцена содержит <div class=\"author-text\"> вне .phone")

    if yaml_only:
        print(f"  YAML → not in HTML ({len(yaml_only)}):")
        for s in sorted(yaml_only)[:20]:
            print(f"    - {s[:140]}")
        if len(yaml_only) > 20:
            print(f"    ... +{len(yaml_only) - 20} more")
    if html_only:
        print(f"  HTML → not in YAML ({len(html_only)}):")
        for s in sorted(html_only)[:20]:
            print(f"    + {s[:140]}")
        if len(html_only) > 20:
            print(f"    ... +{len(html_only) - 20} more")
    return status == "OK"


def main():
    eps = sys.argv[1:] or ["ep_001", "ep_002", "ep_003", "ep_004"]
    for ep in eps:
        audit_episode(ep)


if __name__ == "__main__":
    main()
