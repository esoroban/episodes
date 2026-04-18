#!/usr/bin/env python3
"""
Gameflow → HTML renderer.

Reads YAML scene-flow files from pipeline/gameflow/episodes/
and generates interactive HTML game pages directly into server/game/
(the directory served by server/server.js on Render).

Usage:
    python tools/build_game.py                  # all episodes
    python tools/build_game.py ep_001           # single episode
    python tools/build_game.py ep_001 ep_002    # multiple
"""

import re
import sys
import yaml
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMEFLOW_DIR = ROOT / "pipeline" / "gameflow" / "episodes"
EPISODES_DIR = ROOT / "pipeline" / "source" / "episodes"
OUTPUT_DIR = ROOT / "server" / "game"


def load_episode(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def esc(text) -> str:
    """Escape HTML entities."""
    if not text:
        return ""
    return html.escape(str(text).strip())


def render_visual_brief(vb: dict) -> str:
    """Render visual brief as a subtle info panel."""
    if not vb:
        return ""
    parts = []
    if vb.get("background"):
        parts.append(f'<span class="vb-label">Фон:</span> {esc(vb["background"])}')
    if vb.get("atmosphere"):
        parts.append(f'<span class="vb-label">Атмосфера:</span> {esc(vb["atmosphere"])}')
    if vb.get("camera"):
        parts.append(f'<span class="vb-label">Камера:</span> {esc(vb["camera"])}')
    if vb.get("focus_object"):
        parts.append(f'<span class="vb-label">Фокус:</span> {esc(vb["focus_object"])}')
    chars = vb.get("characters", [])
    for ch in chars:
        who = esc(ch.get("who", ""))
        expr = esc(ch.get("expression", ""))
        pose = esc(ch.get("pose", ""))
        parts.append(f'<span class="vb-label">{who}:</span> {expr}, {pose}')
    props = vb.get("props", [])
    if props:
        parts.append(f'<span class="vb-label">Предметы:</span> {", ".join(esc(p) for p in props)}')
    return '<div class="visual-brief">' + "<br>".join(parts) + "</div>"


def render_dialogue(dialogue_list: list) -> str:
    """Render dialogue lines."""
    if not dialogue_list:
        return ""
    lines = []
    for d in dialogue_list:
        if not isinstance(d, dict):
            continue
        who = esc(d.get("who", ""))
        line_text = esc(d.get("line", ""))
        if who.lower() in ("автор", "author"):
            lines.append(f'<p class="dl-narrator"><em>{line_text}</em></p>')
        elif who.lower() in ("софа", "sofa"):
            lines.append(f'<p class="dl-sofa"><span class="dl-who">\U0001f4f1 {who}:</span> <em>\u00ab{line_text}\u00bb</em></p>')
        else:
            lines.append(f'<p class="dl-char"><span class="dl-who">{who}:</span> \u2014 {line_text}</p>')
    return "\n".join(lines)


def render_author_text(text) -> str:
    """Render author text paragraphs."""
    if not text:
        return ""
    text = str(text).strip()
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return "\n".join(f"<p>{esc(p)}</p>" for p in paragraphs)


def is_sofa_chat_scene(scene: dict) -> bool:
    """True if this scene should render as an iPhone Telegram chat."""
    chars = scene.get("characters_present", [])
    if not any(c.lower() in ("\u0441\u043e\u0444\u0430", "sofa") for c in chars):
        return False
    return bool(
        scene.get("dialogue")
        or scene.get("unlock_button")
        or any("correct" in o for o in scene.get("options", []))
    )


def build_chat_messages(scene: dict) -> list:
    """Build list of chat message dicts for one scene.

    Chat bubble rules (WHO speaks in chat vs voice-over):
      - Софа         → chat bubble (she's the only character who TEXTS)
      - Марко        → chat bubble (player input: send/mic)
      - автор и все  → voice-over strip in timeline (живой голос за кадром)
        остальные     — остаётся на своей позиции, не в плашке
    """
    msgs = []

    at = scene.get("author_text", "")
    if at:
        for p in str(at).strip().split("\n"):
            p = p.strip()
            if p:
                msgs.append({"t": "voiceover", "s": "author", "name": "\u0410\u0432\u0442\u043e\u0440", "x": p})

    for d in scene.get("dialogue", []):
        if not isinstance(d, dict):
            continue
        who = d.get("who", "")
        line = str(d.get("line", "")).strip()
        w = who.lower()
        if w in ("\u0430\u0432\u0442\u043e\u0440", "author"):
            msgs.append({"t": "voiceover", "s": "author", "name": "\u0410\u0432\u0442\u043e\u0440", "x": line})
        elif w in ("\u0441\u043e\u0444\u0430", "sofa"):
            msgs.append({"t": "text", "s": "sofa", "x": line})
        elif w in ("\u043c\u0430\u0440\u043a\u043e", "marko"):
            msgs.append({"t": "text", "s": "marko", "x": line, "im": "text"})
        else:
            msgs.append({"t": "voiceover", "s": w, "name": who, "x": line})

    quiz_opts = [o for o in scene.get("options", []) if "correct" in o]
    if quiz_opts:
        q = scene.get("question", "")
        opts = [{"x": o.get("text", ""), "c": bool(o.get("correct"))} for o in quiz_opts]
        msgs.append({"t": "quiz", "s": "sofa", "q": q, "o": opts})
        fb_ok = str(scene.get("feedback_success", "")).strip()
        fb_fail = str(scene.get("feedback_soft_fail", "")).strip()
        # correct_logic is shown only in the hidden quiz-explanation div,
        # NOT as a chat message — to avoid duplicating feedback_success
        if fb_ok:
            msgs.append({"t": "text", "s": "sofa", "x": fb_ok, "wq": True, "ok": True})
        if fb_fail:
            msgs.append({"t": "text", "s": "sofa", "x": fb_fail, "wq": True, "ok": False})

    unlock = scene.get("unlock_button")
    if unlock:
        msgs.append({"t": "unlock", "x": unlock.get("text", "\U0001f513 \u0420\u0430\u0437\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u0442\u044c")})
        rev = unlock.get("reveals", {})
        if rev:
            ds = str(rev.get("duration", "3"))
            dur = int(ds.split(":")[-1]) if ":" in ds else int(ds)
            msgs.append({"t": "voice", "s": "sofia", "d": dur, "x": rev.get("line", "")})

    return msgs


def group_phone_chains(scenes: list) -> list:
    """
    Group consecutive main-line Sofa scenes into phone chains.
    Branch scenes (soft_fail_loop etc.) are skipped — their content is
    already embedded in quiz JSON as wq:true feedback messages.
    Returns list of units: {"type": "single"|"chain", "scene"|"scenes": ...}
    """
    units = []
    absorbed = set()  # scene_ids absorbed into chains

    i = 0
    while i < len(scenes):
        s = scenes[i]
        sid = s.get("scene_id", "")

        if s.get("branch_type"):
            # Branch scenes: if absorbed into a chain, skip; else render standalone
            if sid not in absorbed:
                units.append({"type": "single", "scene": s})
            i += 1
            continue

        if is_sofa_chat_scene(s):
            chain = [s]
            chain_loc = s.get("location", "")
            j = i + 1
            while j < len(scenes):
                ns = scenes[j]
                if ns.get("branch_type"):
                    # Mark branch scenes as absorbed (skip their standalone render)
                    absorbed.add(ns.get("scene_id", ""))
                    j += 1
                    continue
                # Only merge consecutive Sofa scenes at THE SAME location
                if is_sofa_chat_scene(ns) and ns.get("location", "") == chain_loc:
                    chain.append(ns)
                    j += 1
                else:
                    break
            if len(chain) > 1:
                units.append({"type": "chain", "scenes": chain})
            else:
                units.append({"type": "single", "scene": chain[0]})
            i = j
        else:
            units.append({"type": "single", "scene": s})
            i += 1

    return units


def _phone_html(msg_attr: str) -> str:
    """Build the iPhone frame HTML around a chat."""
    crack = (
        '<svg viewBox="0 0 375 812" fill="none">'
        '<path d="M310 0L305 35L292 72L278 120L262 170L248 218L232 268L218 315'
        'L202 362L188 412L172 460L158 510L140 560L122 612L102 665L80 720L55 780'
        'L45 812" stroke="rgba(0,0,0,0.12)" stroke-width="1.2"/>'
        '<path d="M312 0L301 55L288 100L274 152L256 202L243 248L228 295L214 342"'
        ' stroke="rgba(0,0,0,0.06)" stroke-width="0.6"/>'
        '<path d="M248 218L268 245L295 262" stroke="rgba(0,0,0,0.09)" stroke-width="0.8"/>'
        '<path d="M195 388L172 402L158 408" stroke="rgba(0,0,0,0.08)" stroke-width="0.7"/>'
        '<path d="M308 2L296 60L283 97L268 150L251 200L238 247L223 292L208 342'
        'L193 390L178 437L163 490L146 540L130 587L110 642L90 692L66 752L43 812"'
        ' stroke="rgba(255,255,255,0.15)" stroke-width="0.8"/></svg>'
    )
    return (
        f'<div class="phone" data-chat-messages="{msg_attr}" data-chat-live="true">'
        '<div class="phone-notch"></div><div class="phone-home"></div>'
        f'<div class="crack-overlay">{crack}</div>'
        '<div class="chat-wrap">'
        '<div class="status-bar"><span class="sb-time">9:41</span>'
        '<span class="sb-icons">\u26a1 5G \U0001f50b</span></div>'
        '<div class="chat-header">'
        '<span class="ch-back">\u2039</span>'
        '<div class="ch-avatar">\U0001f4f1</div>'
        '<div class="ch-info"><div class="ch-name">\u0421\u043e\u0444\u0430</div>'
        '<div class="ch-status">\u043e\u043d\u043b\u0430\u0439\u043d</div></div></div>'
        '<div class="chat-messages"></div>'
        '<div class="chat-input-bar imode-disabled">'
        '<div class="ti-group">'
        '<input type="text" class="chat-input" readonly placeholder="\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435...">'
        '<button class="send-btn">\u27a4</button></div>'
        '<div class="vi-group"><button class="mic-btn">\U0001f3a4</button>'
        '<span class="mic-label">\u0413\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435</span></div>'
        '<span class="disabled-label">\u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435...</span>'
        '</div></div></div>'
    )


def render_scene_chain(chain: list, index: int, total: int) -> str:
    """Render a merged phone chain (multiple Sofa scenes) as one scene section."""
    import json as _json

    first = chain[0]
    last = chain[-1]

    sid = first.get("scene_id", f"chain_{index}")
    chars = first.get("characters_present", [])
    location = first.get("location", "")
    time_str = first.get("time", "")
    mood = first.get("mood", "")
    vb = first.get("visual_brief", {})

    # Collect all messages from all scenes in chain
    all_msgs = []
    for s in chain:
        all_msgs.extend(build_chat_messages(s))

    # Blocking if any scene has quiz or unlock
    has_blocking = any(
        s.get("unlock_button") or any("correct" in o for o in s.get("options", []))
        for s in chain
    )
    blocking_attr = ' data-blocking="true"' if has_blocking else ""

    # Navigation from last main-line scene
    next_default = last.get("next_default", "")
    next_success = last.get("next_success", "")
    next_fail = last.get("next_fail", "")
    merge_to = last.get("merge_to", "")

    nav_attrs = ""
    if next_default:
        nav_attrs += f' data-next="{esc(next_default)}"'
    if next_success:
        nav_attrs += f' data-next-success="{esc(next_success)}"'
    if next_fail:
        nav_attrs += f' data-next-fail="{esc(next_fail)}"'
    if merge_to:
        nav_attrs += f' data-merge-to="{esc(merge_to)}"'

    ep_prefix = f"ep{int(first.get('episode_id', 0)):03d}_"
    for target in (next_default, next_success):
        if target and not target.startswith(ep_prefix):
            m = re.match(r"ep(\d+)_", target)
            if m:
                nav_attrs += f' data-next-ep="ep_{int(m.group(1)):03d}.html"'
                break

    msg_attr = html.escape(_json.dumps(all_msgs, ensure_ascii=False), quote=True)
    phone = _phone_html(msg_attr)
    vb_html = render_visual_brief(vb)

    loc_time = ""
    if location or time_str:
        parts = []
        if location:
            parts.append(esc(location))
        if time_str:
            parts.append(esc(time_str))
        loc_time = f'<div class="scene-location">{" \u00b7 ".join(parts)}</div>'
    chars_html = f'<div class="scene-chars">{", ".join(esc(c) for c in chars)}</div>' if chars else ""
    mood_html = f'<div class="scene-mood">{esc(mood)}</div>' if mood else ""
    meta_parts = [p for p in [loc_time, chars_html, mood_html] if p]
    meta_html = ""
    if meta_parts:
        meta_html = (
            '<details class="scene-meta"><summary>\u2139\ufe0f</summary>'
            + "".join(meta_parts)
            + "</details>"
        )

    return f"""
  <section class="scene scene-dialogue" data-scene-id="{esc(sid)}" data-index="{index}"{blocking_attr}{nav_attrs}>
    <div class="scene-header">
      <span class="scene-counter">{index + 1} / {total}</span>
      {meta_html}
    </div>
    <div class="scene-content">
      {vb_html}{phone}
    </div>
  </section>"""


def render_chat(scene: dict) -> str:
    """Render scene as iPhone Telegram chat with cracked screen."""
    import json as _json

    msgs = build_chat_messages(scene)
    msg_attr = html.escape(_json.dumps(msgs, ensure_ascii=False), quote=True)
    return _phone_html(msg_attr)

def render_quiz(scene: dict, scene_id: str) -> str:
    """Render quiz interaction."""
    question = scene.get("question", "")
    options = scene.get("options", [])
    if not question or not options:
        return ""

    quiz_options = [o for o in options if "correct" in o]
    if not quiz_options:
        return ""

    feedback_ok = esc(scene.get("feedback_success", ""))
    feedback_fail = esc(scene.get("feedback_soft_fail", ""))
    correct_logic = esc(scene.get("correct_logic", ""))

    opts_html = []
    for i, opt in enumerate(quiz_options):
        correct = "true" if opt.get("correct") else "false"
        text = esc(opt.get("text", ""))
        opts_html.append(
            f'<button class="quiz-option" data-correct="{correct}" data-index="{i}">{text}</button>'
        )

    return f"""
    <div class="quiz" data-quiz-id="{esc(scene_id)}">
      <p class="quiz-question">{esc(question)}</p>
      <div class="quiz-options">
        {"".join(opts_html)}
      </div>
      <div class="quiz-feedback quiz-feedback-ok" hidden>{feedback_ok}</div>
      <div class="quiz-feedback quiz-feedback-fail" hidden>{feedback_fail}</div>
      <div class="quiz-explanation" hidden>{correct_logic}</div>
    </div>"""


def render_choice(scene: dict) -> str:
    """Render story choice (not quiz)."""
    options = scene.get("options", [])
    if not options:
        return ""

    choice_options = [o for o in options if "next" in o and "correct" not in o]
    if not choice_options:
        return ""

    question = esc(scene.get("question", ""))
    opts_html = []
    for opt in choice_options:
        text = esc(opt.get("text", ""))
        target = esc(opt.get("next", ""))
        opts_html.append(
            f'<button class="choice-option" data-target="{target}">{text}</button>'
        )

    q_html = f'<p class="choice-question">{question}</p>' if question else ""
    return f"""
    <div class="story-choice">
      {q_html}
      <div class="choice-options">
        {"".join(opts_html)}
      </div>
    </div>"""


def render_scene(scene: dict, index: int, total: int) -> str:
    """Render a single scene as a game card."""
    sid = scene.get("scene_id", f"scene_{index}")
    stype = scene.get("scene_type", "narrative")
    location = scene.get("location", "")
    time_str = scene.get("time", "")
    mood = scene.get("mood", "")
    chars = scene.get("characters_present", [])
    branch_type = scene.get("branch_type", "")
    vb = scene.get("visual_brief", {})

    loc_time = ""
    if location or time_str:
        parts = []
        if location:
            parts.append(esc(location))
        if time_str:
            parts.append(esc(time_str))
        loc_time = f'<div class="scene-location">{" \u00b7 ".join(parts)}</div>'

    chars_html = ""
    if chars:
        chars_html = f'<div class="scene-chars">{", ".join(esc(c) for c in chars)}</div>'

    mood_html = ""
    if mood:
        mood_html = f'<div class="scene-mood">{esc(mood)}</div>'

    branch_html = ""
    if branch_type:
        labels = {
            "soft_fail_loop": "\U0001f504 \u041c\u044f\u0433\u043a\u0438\u0439 \u0442\u0443\u043f\u0438\u043a",
            "flavor_detour": "\U0001f33f \u0411\u043e\u043d\u0443\u0441\u043d\u0430\u044f \u0441\u0446\u0435\u043d\u0430",
            "gated_response": "\U0001f511 \u0423\u0441\u043b\u043e\u0432\u043d\u0430\u044f \u0440\u0435\u0430\u043a\u0446\u0438\u044f",
            "cosmetic_branch": "\U0001f3a8 \u0414\u0435\u043a\u043e\u0440\u0430\u0442\u0438\u0432\u043d\u0430\u044f \u0432\u0435\u0442\u043a\u0430",
        }
        branch_html = f'<div class="scene-branch">{labels.get(branch_type, branch_type)}</div>'

    content_parts = []

    vb_html = render_visual_brief(vb)
    if vb_html:
        content_parts.append(vb_html)

    dialogue = scene.get("dialogue", [])
    author_text = scene.get("author_text", "")
    author_text_after = scene.get("author_text_after", "")

    # Sofa scenes render as Telegram-style chat (dialogue, quiz, unlock)
    is_sofa_chat = (
        any(c.lower() in ("\u0441\u043e\u0444\u0430", "sofa") for c in chars)
        and (
            dialogue
            or scene.get("unlock_button")
            or (scene.get("options") and any("correct" in o for o in scene.get("options", [])))
        )
    )

    if is_sofa_chat:
        content_parts.append(render_chat(scene))
        # author_text_after renders OUTSIDE chat (narrative reflection)
        if author_text_after:
            content_parts.append(f'<div class="author-text">{render_author_text(author_text_after)}</div>')
    else:
        if author_text:
            content_parts.append(f'<div class="author-text">{render_author_text(author_text)}</div>')
        if dialogue:
            content_parts.append(f'<div class="dialogue-block">{render_dialogue(dialogue)}</div>')
        if author_text_after:
            content_parts.append(f'<div class="author-text">{render_author_text(author_text_after)}</div>')

        # Standard options (quiz or choice) — only in non-chat mode
        if scene.get("options") and any("correct" in o for o in scene.get("options", [])):
            content_parts.append(render_quiz(scene, sid))

        if scene.get("options") and any(
            "next" in o and "correct" not in o for o in scene.get("options", [])
        ):
            content_parts.append(render_choice(scene))

        # interactions list (ep_004 style)
        for idx, inter in enumerate(scene.get("interactions", [])):
            inter_id = f"{sid}_i{idx}"
            if inter.get("interaction_type") == "vote" or any("correct" in o for o in inter.get("options", [])):
                content_parts.append(render_quiz(inter, inter_id))
            elif inter.get("interaction_type") == "choice" or any("next" in o and "correct" not in o for o in inter.get("options", [])):
                content_parts.append(render_choice(inter))

        # followup_interaction (ep_002 style)
        followup = scene.get("followup_interaction", {})
        if followup and followup.get("options"):
            if any("correct" in o for o in followup["options"]):
                content_parts.append(render_quiz(followup, f"{sid}_followup"))
            elif any("next" in o for o in followup["options"]):
                content_parts.append(render_choice(followup))

    flags_set = scene.get("set_flags", [])

    extra_class = f" scene-{stype}"
    if branch_type:
        extra_class += " scene-branch-card"
    if stype == "cliffhanger":
        extra_class += " scene-cliffhanger"

    has_blocking_quiz = bool(
        (scene.get("options") and any("correct" in o for o in scene.get("options", [])))
        or any(any("correct" in o for o in inter.get("options", [])) for inter in scene.get("interactions", []))
        or scene.get("unlock_button")
    )
    blocking_attr = ' data-blocking="true"' if has_blocking_quiz else ""

    # Navigation data attributes for graph-based navigation
    nav_attrs = ""
    next_default = scene.get("next_default", "")
    next_success = scene.get("next_success", "")
    next_fail = scene.get("next_fail", "")
    merge_to = scene.get("merge_to", "")
    if next_default:
        nav_attrs += f' data-next="{esc(next_default)}"'
    if next_success:
        nav_attrs += f' data-next-success="{esc(next_success)}"'
    if next_fail:
        nav_attrs += f' data-next-fail="{esc(next_fail)}"'
    if merge_to:
        nav_attrs += f' data-merge-to="{esc(merge_to)}"'

    # Cross-episode link: next_default points to another episode's scene
    ep_prefix = f"ep{int(scene.get('episode_id', 0)):03d}_"
    for target in (next_default, next_success):
        if target and not target.startswith(ep_prefix):
            m = re.match(r"ep(\d+)_", target)
            if m:
                nav_attrs += f' data-next-ep="ep_{int(m.group(1)):03d}.html"'
                break

    # Build collapsible metadata
    meta_parts = []
    if loc_time:
        meta_parts.append(loc_time)
    if chars_html:
        meta_parts.append(chars_html)
    if mood_html:
        meta_parts.append(mood_html)
    if branch_html:
        meta_parts.append(branch_html)
    if flags_set:
        meta_parts.append(f'<div class="scene-flags-inner">\U0001f3c1 {", ".join(esc(f) for f in flags_set)}</div>')

    meta_html = ""
    if meta_parts:
        meta_html = (
            '<details class="scene-meta">'
            '<summary>\u2139\ufe0f</summary>'
            f'{"".join(meta_parts)}'
            '</details>'
        )

    return f"""
  <section class="scene{extra_class}" data-scene-id="{esc(sid)}" data-index="{index}"{blocking_attr}{nav_attrs}>
    <div class="scene-header">
      <span class="scene-counter">{index + 1} / {total}</span>
      {meta_html}
    </div>
    <div class="scene-content">
      {"".join(content_parts)}
    </div>
  </section>"""


CSS = """:root {
  --bg: #0d0d12;
  --bg-card: #16161e;
  --bg-card-hover: #1c1c28;
  --text: #e8e6e3;
  --text-muted: #8b8a88;
  --accent: #7c9fd4;
  --accent-soft: #4a6fa520;
  --correct: #4caf50;
  --correct-bg: #1b3a1b;
  --wrong: #ef5350;
  --wrong-bg: #3a1b1b;
  --sofa: #b39ddb;
  --cliffhanger: #7c4dff;
  --branch: #ff9800;
  --border: #2a2a35;
  --radius: 14px;
  --shadow: 0 4px 20px rgba(0,0,0,0.3);
  --font-main: 'Georgia', 'Times New Roman', serif;
  --font-ui: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font-main);
  background: var(--bg);
  color: var(--text);
  line-height: 1.75;
  max-width: 760px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
}
.episode-header {
  text-align: center;
  padding: 1.2rem 1rem 0.8rem;
  background: linear-gradient(180deg, #1a1a2e 0%, var(--bg) 100%);
}
.episode-header h1 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  letter-spacing: -0.02em;
}
.ep-lesson {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
}
.ep-terms {
  font-size: 0.75rem;
  color: var(--accent);
  font-family: var(--font-ui);
  margin-top: 0.3rem;
}
.scene {
  margin: 0 1rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  display: none;
  animation: fadeIn 0.4s ease;
}
.scene.active { display: block; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.scene-header {
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-ui);
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.scene-counter { font-weight: 600; color: var(--text-muted); font-size: 0.75rem; }
.scene-meta { font-size: 0.75rem; }
.scene-meta summary {
  cursor: pointer; color: var(--text-muted); list-style: none;
  font-size: 0.85rem; user-select: none;
}
.scene-meta summary::-webkit-details-marker { display: none; }
.scene-meta[open] { padding-bottom: 0.3rem; }
.scene-location { color: var(--text-muted); margin-top: 0.3rem; }
.scene-chars { color: var(--text-muted); font-size: 0.75rem; }
.scene-mood { color: var(--text-muted); font-size: 0.75rem; font-style: italic; margin-top: 0.15rem; }
.scene-branch { color: var(--branch); font-size: 0.75rem; font-weight: 600; margin-top: 0.2rem; }
.scene-flags-inner { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.15rem; }
.scene-content { padding: 1.25rem; }
.author-text p { margin-bottom: 0.75rem; font-style: italic; }
.dialogue-block { margin: 0.75rem 0; }
.dl-char, .dl-sofa, .dl-narrator {
  margin-bottom: 0.5rem;
  padding-left: 1rem;
  border-left: 3px solid var(--border);
}
.dl-who { font-weight: 600; font-family: var(--font-ui); font-size: 0.9rem; }
.dl-sofa { border-left-color: var(--sofa); }
.dl-sofa .dl-who { color: var(--sofa); }
.dl-narrator { border-left-color: transparent; color: var(--text-muted); font-style: italic; padding-left: 0; }
.visual-brief {
  font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-ui);
  background: #12121a; padding: 0.75rem 1rem; border-radius: 8px;
  margin-bottom: 1rem; line-height: 1.5; display: none;
}
.visual-brief.open { display: block; }
.vb-label { color: var(--accent); font-weight: 600; }
.vb-toggle {
  font-size: 0.75rem; color: var(--text-muted); cursor: pointer;
  font-family: var(--font-ui); margin-bottom: 0.5rem; display: inline-block;
}
.vb-toggle:hover { color: var(--accent); }
.quiz {
  background: #1a1a28; border: 1px solid var(--border); border-radius: 10px;
  padding: 1.25rem; margin: 1rem 0;
}
.quiz-question {
  font-weight: 600; font-size: 1.05rem; margin-bottom: 1rem;
  font-family: var(--font-ui); color: var(--text);
}
.quiz-options { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.quiz-option {
  flex: 1 1 auto; min-width: 120px; padding: 0.7rem 1rem;
  border: 2px solid var(--border); border-radius: 8px;
  background: var(--bg-card); color: var(--text); font-size: 0.95rem;
  cursor: pointer; transition: all 0.2s; font-family: var(--font-ui);
}
.quiz-option:hover { border-color: var(--accent); background: var(--accent-soft); }
.quiz-option.selected-correct { border-color: var(--correct); background: var(--correct-bg); color: var(--correct); font-weight: 600; }
.quiz-option.selected-wrong { border-color: var(--wrong); background: var(--wrong-bg); color: var(--wrong); text-decoration: line-through; }
.quiz-option.reveal-correct { border-color: var(--correct); background: var(--correct-bg); }
.quiz-option:disabled { cursor: default; opacity: 0.8; }
.quiz-feedback {
  margin-top: 0.8rem; padding: 0.75rem 1rem; border-radius: 8px;
  font-size: 0.9rem; font-family: var(--font-ui);
}
.quiz-feedback-ok { background: var(--correct-bg); color: var(--correct); border: 1px solid #2e7d3240; }
.quiz-feedback-fail { background: var(--wrong-bg); color: var(--wrong); border: 1px solid #c6282840; }
.quiz-explanation {
  margin-top: 0.5rem; padding: 0.6rem 1rem; font-size: 0.85rem;
  color: var(--text-muted); font-style: italic;
}
.story-choice { margin: 1rem 0; }
.choice-question { font-weight: 600; font-family: var(--font-ui); margin-bottom: 0.75rem; }
.choice-options { display: flex; flex-direction: column; gap: 0.5rem; }
.choice-option {
  padding: 0.8rem 1.2rem; border: 2px solid var(--accent); border-radius: 10px;
  background: transparent; color: var(--accent); font-size: 1rem;
  cursor: pointer; transition: all 0.2s; font-family: var(--font-ui); text-align: left;
}
.choice-option:hover { background: var(--accent-soft); }
.choice-option.chosen { background: var(--accent-soft); border-color: var(--accent); font-weight: 600; }
.scene-flags { padding: 0.5rem 1.25rem 0.75rem; font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-ui); }
.scene-cliffhanger { border-color: var(--cliffhanger); background: linear-gradient(135deg, #1a1528 0%, var(--bg-card) 100%); }
.scene-cliffhanger .scene-counter { color: var(--cliffhanger); }
.scene-branch-card { border-color: var(--branch); border-style: dashed; }
.scene-previously { border-color: #5c6bc0; background: linear-gradient(135deg, #1a1a2e 0%, var(--bg-card) 100%); }
.scene-previously .scene-counter { color: #9fa8da; }
.nav-bar {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #0d0d12ee; backdrop-filter: blur(12px);
  border-top: 1px solid var(--border); padding: 0.75rem 1rem;
  display: flex; justify-content: center; gap: 0.75rem; z-index: 100;
}
.nav-btn {
  padding: 0.6rem 2rem; border: 2px solid var(--accent); border-radius: 10px;
  background: transparent; color: var(--accent); font-size: 1rem;
  cursor: pointer; font-family: var(--font-ui); transition: all 0.2s;
}
.nav-btn:hover { background: var(--accent-soft); }
.nav-btn:disabled { opacity: 0.3; cursor: default; }
.nav-btn.primary { background: var(--accent); color: var(--bg); font-weight: 600; }
.nav-btn.primary:hover { background: #8ab0e0; }
.nav-btn.primary:disabled { background: var(--accent); opacity: 0.3; }
.progress-bar { position: fixed; top: 0; left: 0; height: 3px; background: var(--accent); transition: width 0.3s ease; z-index: 100; }
.end-screen { text-align: center; padding: 3rem 1.5rem; display: none; }
.end-screen.active { display: block; }
.end-screen h2 { font-size: 1.4rem; margin-bottom: 1rem; color: var(--accent); }
.end-screen p { color: var(--text-muted); font-family: var(--font-ui); }
.end-screen .stats { margin-top: 1.5rem; font-family: var(--font-ui); font-size: 0.9rem; color: var(--text-muted); }
/* ====== iPhone Telegram Chat ====== */
.phone {
  width: 340px; height: 680px;
  border-radius: 42px; border: 4px solid #2a2a2a;
  background: #fff; position: relative; overflow: hidden;
  margin: 0.5rem auto;
  box-shadow: 0 0 0 2px #1a1a1a, 0 12px 40px rgba(0,0,0,0.4), inset 0 0 0 1px #333;
}
.phone-notch {
  position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  width: 140px; height: 28px; background: #000;
  border-radius: 0 0 18px 18px; z-index: 50;
}
.phone-notch::after {
  content: ''; position: absolute; top: 8px; left: 50%; transform: translateX(-50%);
  width: 50px; height: 5px; background: #1a1a1a; border-radius: 3px;
}
.phone-home {
  position: absolute; bottom: 6px; left: 50%; transform: translateX(-50%);
  width: 110px; height: 4px; background: rgba(0,0,0,0.2); border-radius: 3px; z-index: 50;
}
.crack-overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  z-index: 100; pointer-events: none;
}
.crack-overlay svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.chat-wrap {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  display: flex; flex-direction: column;
}
.status-bar {
  height: 44px; flex-shrink: 0; background: #517da2;
  display: flex; align-items: flex-end; justify-content: space-between;
  padding: 0 20px 4px; font-size: 11px; color: #fff; z-index: 40;
}
.sb-time { font-weight: 600; }
.sb-icons { font-size: 10px; }
.chat-header {
  flex-shrink: 0; background: #517da2; border-bottom: 1px solid #4a7393;
  padding: 6px 14px 8px; display: flex; align-items: center; gap: 8px; z-index: 30;
}
.ch-back { color: #fff; font-size: 18px; }
.ch-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #7cb8e4, #4a90c4);
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0;
}
.ch-info { display: flex; flex-direction: column; }
.ch-name { font-size: 14px; font-weight: 600; color: #fff; }
.ch-status { font-size: 11px; color: #d4e8f7; }
.chat-messages {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  padding: 8px 7px; display: flex; flex-direction: column; gap: 2px;
  background: #c8d9e6;
  background-image: radial-gradient(ellipse at 20% 50%, rgba(255,255,255,0.3) 0%, transparent 70%),
    radial-gradient(ellipse at 80% 20%, rgba(255,255,255,0.2) 0%, transparent 60%);
}
.chat-messages::-webkit-scrollbar { width: 0; }
/* Bubbles — light theme */
.msg-row { display: flex; max-width: 82%; animation: fadeIn 0.25s ease-out; }
.msg-row.incoming { align-self: flex-start; }
.msg-row.outgoing { align-self: flex-end; }
.bubble {
  padding: 5px 9px; border-radius: 12px; font-size: 13px;
  line-height: 1.4; color: #000; word-wrap: break-word;
}
.msg-row.incoming .bubble { border-top-left-radius: 4px; }
.msg-row.outgoing .bubble { border-top-right-radius: 4px; }
.bubble.sofa, .bubble.sofia { background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.bubble.author {
  background: #f0f0f5; border-left: 3px solid #9e9e9e;
  font-style: italic; box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}
.bubble.marko { background: #eeffde; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
.sender-name { font-size: 11px; font-weight: 600; margin-bottom: 1px; }
.sender-name.sofa, .sender-name.sofia { color: #3390ec; }
.sender-name.author { color: #7a7a7a; }
.sender-name.marko { color: #4fae3b; }
.msg-time { font-size: 9px; color: rgba(0,0,0,0.35); text-align: right; margin-top: 1px; }
/* Voice-over strip — живой голос за кадром внутри чата
   (автор, мама, Вера и т.д. — всё, кроме Софы и Марко).
   Потом каждый такой блок заменяется на <audio> в озвучке. */
.voice-row {
  align-self: stretch; display: flex; flex-direction: column;
  margin: 4px 4px; padding: 7px 10px 8px;
  background: rgba(35, 40, 55, 0.88);
  border-radius: 10px; color: #e8e6e3;
  font-family: var(--font-main);
  box-shadow: 0 1px 3px rgba(0,0,0,0.18);
  animation: fadeIn 0.25s ease-out;
}
.voice-row .vo-head {
  display: flex; align-items: center; gap: 5px;
  font-family: var(--font-ui); font-size: 10px;
  color: #9db4d6; text-transform: uppercase; letter-spacing: 0.05em;
  margin-bottom: 3px;
}
.voice-row .vo-icon { font-size: 11px; opacity: 0.85; }
.voice-row .vo-name { font-weight: 600; }
.voice-row .vo-body {
  font-size: 13px; line-height: 1.5; font-style: italic; color: #f0eee9;
}
.voice-row.vo-author .vo-head { color: #c7b8e8; }
/* Typing */
.typing-row { display: flex; align-self: flex-start; animation: fadeIn 0.2s ease-out; }
.typing-bubble {
  background: #fff; padding: 9px 14px; border-radius: 12px;
  border-top-left-radius: 4px; display: flex; align-items: center; gap: 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.typing-dot {
  width: 5px; height: 5px; background: #3390ec; border-radius: 50%;
  animation: tBounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes tBounce {
  0%,60%,100% { transform: translateY(0); opacity: 0.35; }
  30% { transform: translateY(-4px); opacity: 1; }
}
/* Voice messages */
.voice-msg { display: flex; align-items: center; gap: 6px; min-width: 160px; }
.voice-play {
  width: 28px; height: 28px; border-radius: 50%; background: #3390ec;
  border: none; color: #fff; font-size: 11px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.voice-play:hover { background: #4aa0f0; }
.voice-waveform {
  flex: 1; display: flex; align-items: center; gap: 1.5px; height: 20px;
}
.voice-bar {
  width: 2px; background: rgba(0,0,0,0.15); border-radius: 2px;
  transition: background 0.08s;
}
.voice-bar.played { background: #3390ec; }
.voice-duration { font-size: 10px; color: rgba(0,0,0,0.4); flex-shrink: 0; }
.voice-subtitle {
  margin-top: 6px; padding: 5px 7px; font-size: 11px; line-height: 1.35;
  color: rgba(0,0,0,0.55); font-style: italic; background: rgba(51,144,236,0.08);
  border-left: 2px solid #3390ec; border-radius: 3px;
}
.voice-subtitle::before {
  content: "\U0001f3a7 "; font-style: normal; opacity: 0.6;
}
body.debug-off .voice-subtitle { display: none; }
/* Quiz buttons */
.quiz-question { margin-bottom: 5px; font-size: 13px; line-height: 1.4; color: #000; }
.quiz-options { display: flex; flex-direction: column; gap: 4px; }
.quiz-btn {
  background: #3390ec; color: #fff; border: none; border-radius: 7px;
  padding: 8px 10px; font-size: 12px; cursor: pointer;
  transition: all 0.2s; text-align: center;
}
.quiz-btn:hover { background: #4aa0f0; }
.quiz-btn.correct { background: #4caf50 !important; cursor: default; }
.quiz-btn.wrong { background: #e53935 !important; cursor: default; }
.quiz-btn.disabled { opacity: 0.45; cursor: default; pointer-events: none; }
/* Unlock */
.unlock-row { display: flex; justify-content: center; padding: 5px 0; animation: fadeIn 0.25s ease-out; }
.unlock-btn {
  background: rgba(255,255,255,0.85); color: #3390ec; border: 1.5px solid #3390ec;
  border-radius: 16px; padding: 7px 16px; font-size: 12px; cursor: pointer;
}
.unlock-btn:hover { background: #fff; }
.unlock-btn.unlocked { background: rgba(255,255,255,0.5); border-color: #aaa; color: #999; cursor: default; }
/* Input bar */
.chat-input-bar {
  flex-shrink: 0; background: #fff; border-top: 1px solid #dfe3e7;
  padding: 5px 8px 22px; display: flex; align-items: center; gap: 5px; z-index: 30;
}
.chat-input {
  flex: 1; background: #f0f2f5; border: 1px solid #dfe3e7; border-radius: 16px;
  padding: 7px 12px; color: #000; font-size: 13px; outline: none;
}
.chat-input::placeholder { color: rgba(0,0,0,0.3); }
.chat-input:read-only { cursor: default; }
.send-btn {
  width: 32px; height: 32px; border-radius: 50%; background: #3390ec;
  border: none; color: #fff; font-size: 14px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.send-btn:hover { background: #4aa0f0; }
.send-btn:active { transform: scale(0.9); }
.mic-btn {
  width: 32px; height: 32px; border-radius: 50%; background: #3390ec;
  border: none; color: #fff; font-size: 15px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.mic-btn.recording { background: #e53935; animation: micPulse 0.9s infinite; }
@keyframes micPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.12)} }
.mic-label { flex: 1; color: rgba(0,0,0,0.35); font-size: 12px; padding: 0 3px; }
.mic-label.rec { color: #e53935; }
.ti-group, .vi-group { display: flex; flex: 1; gap: 5px; align-items: center; }
.imode-text .vi-group, .imode-voice .ti-group,
.imode-disabled .ti-group, .imode-disabled .vi-group { display: none; }
.disabled-label {
  flex: 1; text-align: center; color: rgba(0,0,0,0.25); font-size: 11px; display: none;
}
.imode-disabled .disabled-label { display: block; }

.nav-spacer { height: 4rem; }
@media (max-width: 600px) {
  .scene { margin: 0 0.5rem 1rem; }
  .quiz-options { flex-direction: column; }
  .quiz-option { min-width: 100%; }
  .episode-header h1 { font-size: 1.3rem; }
}"""


JS = r"""
(function() {
  var scenes = document.querySelectorAll('.scene');
  var btnNext = document.getElementById('btnNext');
  var btnPrev = document.getElementById('btnPrev');
  var progress = document.getElementById('progress');
  var endScreen = document.getElementById('endScreen');
  var statsEl = document.getElementById('stats');
  var currentIndex = 0, correctCount = 0, totalQuizzes = 0;
  var answeredScenes = new Set();
  var sceneMap = {};
  scenes.forEach(function(s,i){ sceneMap[s.dataset.sceneId]=i; });
  var navHistory=[], quizResults={}, choiceTarget=null;

  function resolveNext(id){ return (id&&sceneMap[id]!==undefined)?sceneMap[id]:null; }

  function showScene(index){
    scenes.forEach(function(s){s.classList.remove('active');});
    if(index<scenes.length){
      scenes[index].classList.add('active');
      scenes[index].scrollIntoView({behavior:'smooth',block:'start'});
      initPhoneChat(scenes[index]);
    }
    currentIndex=index;
    btnPrev.disabled=(navHistory.length===0);
    updateProgress(); updateNextButton();
    if(index>=scenes.length){
      endScreen.classList.add('active');
      statsEl.textContent='\u041f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u044b\u0445: '+correctCount+'/'+totalQuizzes;
      btnNext.disabled=true;
    } else { endScreen.classList.remove('active'); }
  }

  function goForward(){
    if(currentIndex>=scenes.length) return;
    var sc=scenes[currentIndex]; navHistory.push(currentIndex); var ni=null;
    if(choiceTarget){ni=resolveNext(choiceTarget);choiceTarget=null;}
    if(ni===null&&quizResults[currentIndex]){
      if(quizResults[currentIndex]==='correct'&&sc.dataset.nextSuccess) ni=resolveNext(sc.dataset.nextSuccess);
      else if(quizResults[currentIndex]==='wrong'&&sc.dataset.nextFail) ni=resolveNext(sc.dataset.nextFail);
    }
    if(ni===null&&sc.dataset.next) ni=resolveNext(sc.dataset.next);
    if(ni===null&&sc.dataset.nextEp){window.location.href=sc.dataset.nextEp;return;}
    if(ni===null) ni=currentIndex+1;
    showScene(ni);
  }
  function goBack(){if(navHistory.length>0) showScene(navHistory.pop());}

  function updateProgress(){
    var v=new Set(navHistory);v.add(currentIndex);
    progress.style.width=Math.min((v.size/scenes.length)*100,100)+'%';
  }
  function updateNextButton(){
    if(currentIndex>=scenes.length){btnNext.disabled=true;return;}
    var sc=scenes[currentIndex];
    var blocking=sc.dataset.blocking==='true';
    var answered=answeredScenes.has(currentIndex);
    var chatPending=sc.dataset.chatPending==='true';
    var choiceWait=sc.querySelector('.story-choice')&&!sc.querySelector('.choice-option.chosen');
    btnNext.disabled=chatPending||(blocking&&!answered)||choiceWait;
  }

  btnNext.addEventListener('click',goForward);
  btnPrev.addEventListener('click',goBack);
  document.addEventListener('keydown',function(e){
    if(e.key==='ArrowRight'||e.key===' '){if(!btnNext.disabled){e.preventDefault();btnNext.click();}}
    else if(e.key==='ArrowLeft'){if(!btnPrev.disabled){e.preventDefault();btnPrev.click();}}
  });

  /* ── iPhone Chat Controller ────────────────────────── */
  function initPhoneChat(sceneEl){
    var phone=sceneEl.querySelector('.phone[data-chat-live]');
    if(!phone||phone.dataset.chatInit) return;
    phone.dataset.chatInit='true';
    sceneEl.dataset.chatPending='true';
    updateNextButton();

    var msgs=JSON.parse(phone.dataset.chatMessages);
    var chatEl=phone.querySelector('.chat-messages');
    var bar=phone.querySelector('.chat-input-bar');
    var inp=phone.querySelector('.chat-input');
    var sendBtn=phone.querySelector('.send-btn');
    var micBtn=phone.querySelector('.mic-btn');
    var micLabel=phone.querySelector('.mic-label');
    var si=Array.from(scenes).indexOf(sceneEl);
    var idx=0, quizOk=null, busy=false;

    function scroll(){chatEl.scrollTo({top:chatEl.scrollHeight,behavior:'smooth'});}
    function now(){var d=new Date();return d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0');}
    function barsHtml(n){var r='';for(var i=0;i<n;i++){r+='<div class="voice-bar" style="height:'+(3+Math.floor(Math.random()*18))+'px"></div>';}return r;}
    function setMode(m,t){bar.className='chat-input-bar imode-'+m;if(m==='text'&&t)inp.value=t;}

    function showTyping(){
      return new Promise(function(res){
        var el=document.createElement('div');
        el.className='typing-row';
        el.innerHTML='<div class="typing-bubble"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
        chatEl.appendChild(el);scroll();
        setTimeout(function(){el.remove();res();},800+Math.random()*400);
      });
    }

    function addText(m){
      var out=m.s==='marko';
      var label={sofa:'\u0421\u043e\u0444\u0430',sofia:'\u0421\u043e\u0444\u0438\u044f',marko:'\u041c\u0430\u0440\u043a\u043e'}[m.s]||m.s;
      var row=document.createElement('div');
      row.className='msg-row '+(out?'outgoing':'incoming');
      row.innerHTML='<div class="bubble '+m.s+'"><div class="sender-name '+m.s+'">'+label+'</div><div>'+m.x+'</div><div class="msg-time">'+now()+'</div></div>';
      chatEl.appendChild(row);scroll();
    }

    /* Voice-over strip inside chat: автор / мама / Вера / ... — живой голос за кадром.
       Остаётся на своей позиции в потоке. Потом x заменяется на <audio>. */
    function addVoiceover(m){
      var row=document.createElement('div');
      var icon=m.s==='author'?'\u270d\ufe0f':'\ud83d\udd0a';
      row.className='voice-row vo-'+m.s;
      row.innerHTML='<div class="vo-head"><span class="vo-icon">'+icon+'</span><span class="vo-name">'+(m.name||m.s)+'</span></div><div class="vo-body">'+m.x+'</div>';
      chatEl.appendChild(row);scroll();
    }

    /* Estimate reading/voice duration (ms) from text length — later replaced by audio.duration */
    function voDuration(text){
      var n=(text||'').length;
      return Math.max(900, Math.min(4500, 55*n));
    }

    function addVoice(m){
      var out=m.s==='marko';
      var label={sofa:'\u0421\u043e\u0444\u0430',sofia:'\u0421\u043e\u0444\u0438\u044f',marko:'\u041c\u0430\u0440\u043a\u043e'}[m.s]||m.s;
      var row=document.createElement('div');
      row.className='msg-row '+(out?'outgoing':'incoming');
      var ds='0:'+m.d.toString().padStart(2,'0');
      var sub=m.x?'<div class="voice-subtitle">'+m.x+'</div>':'';
      row.innerHTML='<div class="bubble '+m.s+'"><div class="sender-name '+m.s+'">'+label+'</div><div class="voice-msg"><button class="voice-play">\u25b6</button><div class="voice-waveform">'+barsHtml(24)+'</div><span class="voice-duration">'+ds+'</span></div>'+sub+'<div class="msg-time">'+now()+'</div></div>';
      chatEl.appendChild(row);scroll();
      row.querySelector('.voice-play').onclick=function(){
        var btn=this;if(btn.dataset.p)return;btn.dataset.p='1';btn.textContent='\u23f8';
        var bb=btn.parentElement.querySelectorAll('.voice-bar');
        var ms=m.d*1000/bb.length,i=0;
        var iv=setInterval(function(){
          if(i<bb.length){bb[i].classList.add('played');i++;}
          else{clearInterval(iv);delete btn.dataset.p;btn.textContent='\u25b6';bb.forEach(function(x){x.classList.remove('played');});}
        },ms);
      };
    }

    function addQuiz(m){
      return new Promise(function(resolve){
        totalQuizzes++;
        var row=document.createElement('div');
        row.className='msg-row incoming';
        var opts=m.o.map(function(o,i){return '<button class="quiz-btn" data-c="'+o.c+'" data-i="'+i+'">'+o.x+'</button>';}).join('');
        row.innerHTML='<div class="bubble sofa"><div class="sender-name sofa">\u0421\u043e\u0444\u0430</div><div class="quiz-question">'+m.q+'</div><div class="quiz-options">'+opts+'</div><div class="msg-time">'+now()+'</div></div>';
        chatEl.appendChild(row);scroll();
        row.querySelectorAll('.quiz-btn').forEach(function(b){
          b.onclick=function(){
            var ok=b.dataset.c==='true';
            b.classList.add(ok?'correct':'wrong');
            row.querySelectorAll('.quiz-btn').forEach(function(x){
              if(x!==b)x.classList.add('disabled');
              if(x.dataset.c==='true'&&x!==b)x.classList.add('correct');
            });
            quizOk=ok;
            if(ok){correctCount++;quizResults[si]='correct';}
            else{quizResults[si]='wrong';}
            resolve(ok);
          };
        });
      });
    }

    function addUnlock(m){
      return new Promise(function(resolve){
        var row=document.createElement('div');
        row.className='unlock-row';
        row.innerHTML='<button class="unlock-btn">'+m.x+'</button>';
        chatEl.appendChild(row);scroll();
        row.querySelector('.unlock-btn').onclick=function(){
          this.textContent='\ud83d\udd13 \u0420\u0430\u0437\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u043e';
          this.classList.add('unlocked');
          resolve();
        };
      });
    }

    sendBtn.addEventListener('click',function(){
      if(busy)return;var m=msgs[idx];
      if(!m||m.s!=='marko')return;
      addText(m);inp.value='';setMode('disabled');
      idx++;setTimeout(processNext,400);
    });
    micBtn.addEventListener('click',function(){
      if(busy)return;var m=msgs[idx];
      if(!m||m.s!=='marko'||m.t!=='voice')return;
      if(micBtn.classList.contains('recording'))return;
      micBtn.classList.add('recording');
      micLabel.textContent='\u0417\u0430\u043f\u0438\u0441\u044c...';micLabel.classList.add('rec');
      setTimeout(function(){
        micBtn.classList.remove('recording');
        micLabel.textContent='\u0413\u043e\u043b\u043e\u0441\u043e\u0432\u043e\u0435';micLabel.classList.remove('rec');
        addVoice(m);setMode('disabled');
        idx++;setTimeout(processNext,400);
      },1500);
    });

    async function processNext(){
      if(idx>=msgs.length){
        setMode('disabled');
        delete sceneEl.dataset.chatPending;
        answeredScenes.add(si);
        updateNextButton();return;
      }
      busy=true;var m=msgs[idx];

      if(m.s==='marko'){
        busy=false;
        setMode(m.t==='voice'?'voice':'text',m.x);
        return;
      }
      if(m.wq&&quizOk===null){busy=false;setTimeout(processNext,300);return;}
      if(m.wq){
        if(m.ok===true&&!quizOk){idx++;busy=false;processNext();return;}
        if(m.ok===false&&quizOk){idx++;busy=false;processNext();return;}
      }
      if(m.t==='unlock'){setMode('disabled');await addUnlock(m);idx++;busy=false;processNext();return;}
      if(m.t==='voiceover'){
        /* Без typing-индикатора: голос просто звучит. Пауза соразмерна длине текста. */
        setMode('disabled');
        addVoiceover(m);
        idx++;
        setTimeout(function(){busy=false;processNext();}, voDuration(m.x));
        return;
      }
      await showTyping();
      if(m.t==='quiz'){await addQuiz(m);idx++;busy=false;processNext();return;}
      if(m.t==='voice'){addVoice(m);}
      else{addText(m);}
      idx++;busy=false;setTimeout(processNext,350);
    }

    setTimeout(processNext,600);
  }

  /* ── Standard Quiz (non-chat) ──────────────────────── */
  document.querySelectorAll('.quiz').forEach(function(quiz){
    var buttons=quiz.querySelectorAll('.quiz-option');
    var feedOk=quiz.querySelector('.quiz-feedback-ok');
    var feedFail=quiz.querySelector('.quiz-feedback-fail');
    var explanation=quiz.querySelector('.quiz-explanation');
    var done=false;totalQuizzes++;
    buttons.forEach(function(btn){
      btn.addEventListener('click',function(){
        if(done)return;done=true;
        var ok=btn.dataset.correct==='true';
        var se=quiz.closest('.scene');
        var si=Array.from(scenes).indexOf(se);
        if(ok){btn.classList.add('selected-correct');correctCount++;if(feedOk)feedOk.hidden=false;quizResults[si]='correct';}
        else{btn.classList.add('selected-wrong');buttons.forEach(function(b){if(b.dataset.correct==='true')b.classList.add('reveal-correct');});if(feedFail)feedFail.hidden=false;quizResults[si]='wrong';}
        if(explanation)explanation.hidden=false;
        buttons.forEach(function(b){b.disabled=true;});
        answeredScenes.add(si);updateNextButton();
      });
    });
  });

  /* ── Choice (auto-advance) ─────────────────────────── */
  document.querySelectorAll('.choice-option').forEach(function(btn){
    btn.addEventListener('click',function(){
      var block=btn.closest('.story-choice');
      block.querySelectorAll('.choice-option').forEach(function(b){b.classList.remove('chosen');});
      btn.classList.add('chosen');
      var t=btn.dataset.target;
      if(t&&sceneMap[t]!==undefined) choiceTarget=t;
      updateNextButton();
      setTimeout(goForward,400);
    });
  });

  /* ── Visual Brief Toggle ───────────────────────────── */
  document.querySelectorAll('.visual-brief').forEach(function(vb){
    var toggle=document.createElement('span');
    toggle.className='vb-toggle';
    toggle.textContent='\ud83c\udfa8 Visual brief \u25b8';
    toggle.addEventListener('click',function(){
      vb.classList.toggle('open');
      toggle.textContent=vb.classList.contains('open')?'\ud83c\udfa8 Visual brief \u25be':'\ud83c\udfa8 Visual brief \u25b8';
    });
    vb.parentNode.insertBefore(toggle,vb);
  });

  showScene(0);
})();
"""


def render_episode_html(data: dict) -> str:
    """Render full episode HTML."""
    ep_id = data.get("episode_id", "?")
    title = esc(data.get("episode_title", f"Эпизод {ep_id}"))
    lesson = esc(data.get("lesson", ""))
    terms = data.get("terms_introduced", [])
    scenes = data.get("scenes", [])

    terms_html = ""
    if terms:
        terms_html = f'<p class="ep-terms">Новые термины: {", ".join(esc(t) for t in terms)}</p>'

    # Previously recap as scene 0
    previously = data.get("previously", "")
    previously_html = ""
    if previously:
        prev_text = render_author_text(previously)
        enter_req = data.get("enter_requires", {})
        req_flags = enter_req.get("flags", [])
        req_ep = enter_req.get("previous_episode", "")
        req_html = ""
        if req_flags or req_ep:
            req_parts = []
            if req_ep:
                req_parts.append(f"Эпизод {req_ep}")
            for fl in req_flags:
                req_parts.append(fl)
            req_html = f'<div class="scene-flags">\U0001f512 Требуется: {", ".join(esc(r) for r in req_parts)}</div>'

        previously_html = f"""
  <section class="scene scene-previously active" data-scene-id="previously" data-index="-1">
    <div class="scene-header">
      <div class="scene-counter">\U0001f4dc Ранее</div>
    </div>
    <div class="scene-content">
      <div class="author-text">{prev_text}</div>
    </div>
    {req_html}
  </section>"""

    # Group consecutive Sofa scenes into single phone chains
    units = group_phone_chains(scenes)

    scene_offset = 1 if previously else 0
    total = len(units) + scene_offset

    scenes_html_parts = []
    for i, unit in enumerate(units):
        idx = i + scene_offset
        if unit["type"] == "chain":
            scenes_html_parts.append(render_scene_chain(unit["scenes"], idx, total))
        else:
            scenes_html_parts.append(render_scene(unit["scene"], idx, total))
    scenes_html = "\n".join(scenes_html_parts)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Эпизод {ep_id} — «{title}»</title>
<style>
{CSS}
</style>
</head>
<body>

<div class="progress-bar" id="progress"></div>

<header class="episode-header">
  <h1>Эпизод {ep_id} — «{title}»</h1>
  <p class="ep-lesson">{lesson}</p>
  {terms_html}
</header>

{previously_html}
{scenes_html}

<div class="end-screen" id="endScreen">
  <h2>Конец эпизода {ep_id}</h2>
  <p>«{title}»</p>
  <div class="stats" id="stats"></div>
</div>

<div class="nav-spacer"></div>

<div class="nav-bar">
  <button class="nav-btn" id="btnPrev" disabled>\u2190 Назад</button>
  <button class="nav-btn primary" id="btnNext">Дальше \u2192</button>
</div>

<script>
{JS}
</script>
</body>
</html>"""


def build_episode(yaml_path: Path):
    """Build HTML for a single episode YAML."""
    data = load_episode(yaml_path)
    ep_id = data.get("episode_id", 0)
    filename = f"ep_{int(ep_id):03d}.html"
    output_path = OUTPUT_DIR / filename

    html_content = render_episode_html(data)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"  \u2713 {yaml_path.name} \u2192 {output_path.relative_to(ROOT)}")
    return output_path


def build_index(episode_files: list):
    """Build index.html from episode plans, marking gameflow coverage honestly."""
    built_episode_map = {}
    for ep_file in sorted(episode_files):
        data = load_episode(ep_file)
        ep_id = int(data.get("episode_id", 0))
        built_episode_map[ep_id] = {
            "title": html.escape(data.get("episode_title", f"Эпизод {ep_id}")),
            "lesson": html.escape(data.get("lesson", "")),
            "scene_count": len(data.get("scenes", [])),
            "href": f'ep_{ep_id:03d}.html',
        }

    day_sections = []
    total_episode_count = 0
    built_count = 0
    for day_file in sorted(EPISODES_DIR.glob("day_*.yaml")):
        day_data = load_yaml(day_file) or {}
        day_num = day_data.get("day", "?")
        arc = html.escape(day_data.get("story_arc", ""))
        lessons = ", ".join(day_data.get("lessons", []))

        cards = []
        for episode in day_data.get("episodes", []):
            ep_id = int(episode.get("ep", 0))
            total_episode_count += 1

            built = built_episode_map.get(ep_id)
            title = html.escape(episode.get("title", f"Эпизод {ep_id}"))
            blocks = ", ".join(episode.get("blocks", []))

            if built:
                built_count += 1
                lesson_meta = built["lesson"] or html.escape(blocks)
                cards.append(
                    f'<a href="{built["href"]}" class="ep-card ep-card-ready">'
                    f'<span class="ep-num">Эпизод {ep_id}</span>'
                    f'<span class="ep-title">«{title}»</span>'
                    f'<span class="ep-meta">{lesson_meta} \u00b7 {built["scene_count"]} сцен</span>'
                    f'<span class="ep-status ep-status-ready">HTML готов</span>'
                    f"</a>"
                )
            else:
                block_meta = html.escape(blocks) if blocks else "Без блока"
                cards.append(
                    f'<div class="ep-card ep-card-missing">'
                    f'<span class="ep-num">Эпизод {ep_id}</span>'
                    f'<span class="ep-title">«{title}»</span>'
                    f'<span class="ep-meta">{block_meta}</span>'
                    f'<span class="ep-status ep-status-missing">Нет gameflow / HTML</span>'
                    f"</div>"
                )

        day_sections.append(
            f'<section class="day-section">'
            f'<h2>День {day_num}</h2>'
            f'<p class="day-meta">{arc}</p>'
            f'<p class="day-lessons">Уроки: {html.escape(lessons)}</p>'
            f'{"".join(cards)}'
            f"</section>"
        )

    coverage_text = f"Покрытие игры: {built_count} из {total_episode_count} эпизодов"

    index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Сила Слова — Игра</title>
<style>
:root {{
  --bg: #0d0d12; --card: #16161e; --text: #e8e6e3;
  --muted: #8b8a88; --accent: #7c9fd4; --border: #2a2a35;
  --ok: #7fb069; --warn: #d8a657;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg); color: var(--text);
  max-width: 760px; margin: 0 auto; padding: 2rem 1rem 3rem;
}}
h1 {{ text-align: center; font-size: 1.5rem; margin-bottom: 0.5rem; }}
.subtitle {{ text-align: center; color: var(--muted); font-size: 0.95rem; margin-bottom: 0.5rem; }}
.coverage {{
  text-align: center; color: var(--accent); font-size: 0.9rem;
  margin-bottom: 2rem; font-weight: 600;
}}
.day-section {{
  margin-bottom: 1.5rem; padding: 1rem; background: #12121a;
  border: 1px solid var(--border); border-radius: 14px;
}}
.day-section h2 {{ font-size: 1.1rem; margin-bottom: 0.25rem; }}
.day-meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 0.2rem; }}
.day-lessons {{ color: var(--accent); font-size: 0.82rem; margin-bottom: 0.9rem; }}
.ep-card {{
  display: block; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  text-decoration: none; color: var(--text); transition: all 0.2s;
}}
.ep-card-ready:hover {{ border-color: var(--accent); background: #1c1c28; }}
.ep-card-missing {{
  opacity: 0.9; border-style: dashed; background: #14141b;
}}
.ep-num {{ font-size: 0.8rem; color: var(--accent); font-weight: 600; }}
.ep-title {{ display: block; font-size: 1.1rem; margin: 0.2rem 0; }}
.ep-meta {{ font-size: 0.8rem; color: var(--muted); }}
.ep-status {{
  display: inline-block; margin-top: 0.55rem; font-size: 0.78rem;
  font-weight: 600;
}}
.ep-status-ready {{ color: var(--ok); }}
.ep-status-missing {{ color: var(--warn); }}
</style>
</head>
<body>
<h1>Сила Слова</h1>
<p class="subtitle">Каталог собирается из `pipeline/source/episodes`, а кликабельность зависит от наличия gameflow/HTML.</p>
<p class="coverage">{coverage_text}</p>
{"".join(day_sections)}
</body>
</html>"""

    index_path = OUTPUT_DIR / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  \u2713 index.html")


def main():
    args = sys.argv[1:]

    if args:
        yaml_files = []
        for arg in args:
            name = arg if arg.endswith(".yaml") else f"{arg}.yaml"
            path = GAMEFLOW_DIR / name
            if path.exists():
                yaml_files.append(path)
            else:
                print(f"  \u2717 Not found: {path}")
    else:
        yaml_files = sorted(GAMEFLOW_DIR.glob("ep_*.yaml"))

    if not yaml_files:
        print("No gameflow YAML files found.")
        return

    print(f"Building {len(yaml_files)} episode(s)...")

    if OUTPUT_DIR.exists():
        for old in OUTPUT_DIR.glob("*.html"):
            old.unlink()
        print(f"  \u2713 Cleaned server/game/")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for yf in yaml_files:
        build_episode(yf)

    build_index(yaml_files)
    print("Done.")


if __name__ == "__main__":
    main()
