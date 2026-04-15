#!/usr/bin/env python3
"""
Gameflow → HTML renderer.

Reads YAML scene-flow files from pipeline/gameflow/episodes/
and generates interactive HTML game pages to publish/game/.

Usage:
    python tools/build_game.py                  # all episodes
    python tools/build_game.py ep_001           # single episode
    python tools/build_game.py ep_001 ep_002    # multiple
"""

import sys
import yaml
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMEFLOW_DIR = ROOT / "pipeline" / "gameflow" / "episodes"
OUTPUT_DIR = ROOT / "publish" / "game"


def load_episode(path: Path) -> dict:
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


def scene_type_icon(t: str) -> str:
    icons = {
        "narrative": "\U0001f4d6",
        "dialogue": "\U0001f4ac",
        "quiz": "\u2753",
        "choice": "\U0001f500",
        "feedback": "\U0001f4a1",
        "transition": "\U0001f6b6",
        "cliffhanger": "\u26a1",
    }
    return icons.get(t, "\u25b8")


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

    icon = scene_type_icon(stype)

    content_parts = []

    vb_html = render_visual_brief(vb)
    if vb_html:
        content_parts.append(vb_html)

    author_text = scene.get("author_text", "")
    if author_text:
        content_parts.append(f'<div class="author-text">{render_author_text(author_text)}</div>')

    dialogue = scene.get("dialogue", [])
    if dialogue:
        content_parts.append(f'<div class="dialogue-block">{render_dialogue(dialogue)}</div>')

    # author_text_after (appears after dialogue in some scenes)
    author_text_after = scene.get("author_text_after", "")
    if author_text_after:
        content_parts.append(f'<div class="author-text">{render_author_text(author_text_after)}</div>')

    # Standard options (quiz or choice)
    if scene.get("options") and any("correct" in o for o in scene.get("options", [])):
        content_parts.append(render_quiz(scene, sid))

    if scene.get("options") and any(
        "next" in o and "correct" not in o for o in scene.get("options", [])
    ):
        content_parts.append(render_choice(scene))

    # interactions list (ep_004 style: multiple interactions in one scene)
    for idx, inter in enumerate(scene.get("interactions", [])):
        inter_id = f"{sid}_i{idx}"
        if inter.get("interaction_type") == "vote" or any("correct" in o for o in inter.get("options", [])):
            content_parts.append(render_quiz(inter, inter_id))
        elif inter.get("interaction_type") == "choice" or any("next" in o and "correct" not in o for o in inter.get("options", [])):
            content_parts.append(render_choice(inter))

    # followup_interaction (ep_002 style: secondary interaction after quiz)
    followup = scene.get("followup_interaction", {})
    if followup and followup.get("options"):
        if any("correct" in o for o in followup["options"]):
            content_parts.append(render_quiz(followup, f"{sid}_followup"))
        elif any("next" in o for o in followup["options"]):
            content_parts.append(render_choice(followup))

    flags_set = scene.get("set_flags", [])
    flags_html = ""
    if flags_set:
        flags_html = f'<div class="scene-flags">\U0001f3c1 {", ".join(esc(f) for f in flags_set)}</div>'

    extra_class = f" scene-{stype}"
    if branch_type:
        extra_class += " scene-branch-card"
    if stype == "cliffhanger":
        extra_class += " scene-cliffhanger"

    has_blocking_quiz = bool(
        (scene.get("options") and any("correct" in o for o in scene.get("options", [])))
        or any(any("correct" in o for o in inter.get("options", [])) for inter in scene.get("interactions", []))
    )
    blocking_attr = ' data-blocking="true"' if has_blocking_quiz else ""

    return f"""
  <section class="scene{extra_class}" data-scene-id="{esc(sid)}" data-index="{index}"{blocking_attr}>
    <div class="scene-header">
      <div class="scene-counter">{icon} \u0421\u0446\u0435\u043d\u0430 {index + 1}/{total}</div>
      {loc_time}
      {chars_html}
      {mood_html}
      {branch_html}
    </div>
    <div class="scene-content">
      {"".join(content_parts)}
    </div>
    {flags_html}
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
  padding: 3rem 1.5rem 2rem;
  background: linear-gradient(180deg, #1a1a2e 0%, var(--bg) 100%);
}
.episode-header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
}
.ep-lesson {
  font-size: 0.9rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
}
.ep-terms {
  font-size: 0.85rem;
  color: var(--accent);
  font-family: var(--font-ui);
  margin-top: 0.5rem;
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
  padding: 1rem 1.25rem 0.75rem;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-ui);
  font-size: 0.85rem;
}
.scene-counter { font-weight: 600; margin-bottom: 0.3rem; color: var(--accent); }
.scene-location { color: var(--text-muted); }
.scene-chars { color: var(--text-muted); font-size: 0.8rem; }
.scene-mood { color: var(--text-muted); font-size: 0.8rem; font-style: italic; margin-top: 0.2rem; }
.scene-branch { color: var(--branch); font-size: 0.8rem; font-weight: 600; margin-top: 0.3rem; }
.scene-content { padding: 1.25rem; }
.author-text p { margin-bottom: 0.75rem; }
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
.nav-spacer { height: 4rem; }
@media (max-width: 600px) {
  .scene { margin: 0 0.5rem 1rem; }
  .quiz-options { flex-direction: column; }
  .quiz-option { min-width: 100%; }
  .episode-header h1 { font-size: 1.3rem; }
}"""


JS = """
(function() {
  const scenes = document.querySelectorAll('.scene');
  const btnNext = document.getElementById('btnNext');
  const btnPrev = document.getElementById('btnPrev');
  const progress = document.getElementById('progress');
  const endScreen = document.getElementById('endScreen');
  const statsEl = document.getElementById('stats');

  let currentIndex = 0;
  let correctCount = 0;
  let totalQuizzes = 0;
  let answeredScenes = new Set();

  const sceneMap = {};
  scenes.forEach((s, i) => { sceneMap[s.dataset.sceneId] = i; });

  function showScene(index) {
    scenes.forEach(s => s.classList.remove('active'));
    if (index < scenes.length) {
      scenes[index].classList.add('active');
      scenes[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    currentIndex = index;
    btnPrev.disabled = (index === 0);
    updateProgress();
    updateNextButton();
    if (index >= scenes.length) {
      endScreen.classList.add('active');
      statsEl.textContent = 'Правильных ответов: ' + correctCount + ' / ' + totalQuizzes;
      btnNext.disabled = true;
    } else {
      endScreen.classList.remove('active');
    }
  }

  function updateProgress() {
    const pct = ((currentIndex + 1) / scenes.length) * 100;
    progress.style.width = Math.min(pct, 100) + '%';
  }

  function updateNextButton() {
    if (currentIndex >= scenes.length) { btnNext.disabled = true; return; }
    const scene = scenes[currentIndex];
    const isBlocking = scene.dataset.blocking === 'true';
    const isAnswered = answeredScenes.has(currentIndex);
    const hasUnansweredChoice = scene.querySelector('.story-choice') &&
                                 !scene.querySelector('.choice-option.chosen');
    btnNext.disabled = (isBlocking && !isAnswered) || hasUnansweredChoice;
  }

  btnNext.addEventListener('click', function() {
    if (currentIndex < scenes.length) showScene(currentIndex + 1);
  });
  btnPrev.addEventListener('click', function() {
    if (currentIndex > 0) showScene(currentIndex - 1);
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight' || e.key === ' ') {
      if (!btnNext.disabled) { e.preventDefault(); btnNext.click(); }
    } else if (e.key === 'ArrowLeft') { btnPrev.click(); }
  });

  document.querySelectorAll('.quiz').forEach(function(quiz) {
    var buttons = quiz.querySelectorAll('.quiz-option');
    var feedbackOk = quiz.querySelector('.quiz-feedback-ok');
    var feedbackFail = quiz.querySelector('.quiz-feedback-fail');
    var explanation = quiz.querySelector('.quiz-explanation');
    var answered = false;
    totalQuizzes++;

    buttons.forEach(function(btn) {
      btn.addEventListener('click', function() {
        if (answered) return;
        answered = true;
        var isCorrect = btn.dataset.correct === 'true';
        var sceneEl = quiz.closest('.scene');
        var sceneIdx = Array.from(scenes).indexOf(sceneEl);

        if (isCorrect) {
          btn.classList.add('selected-correct');
          correctCount++;
          if (feedbackOk) feedbackOk.hidden = false;
        } else {
          btn.classList.add('selected-wrong');
          buttons.forEach(function(b) {
            if (b.dataset.correct === 'true') b.classList.add('reveal-correct');
          });
          if (feedbackFail) feedbackFail.hidden = false;
        }
        if (explanation) explanation.hidden = false;
        buttons.forEach(function(b) { b.disabled = true; });
        answeredScenes.add(sceneIdx);
        updateNextButton();
      });
    });
  });

  document.querySelectorAll('.choice-option').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var choiceBlock = btn.closest('.story-choice');
      choiceBlock.querySelectorAll('.choice-option').forEach(function(b) { b.classList.remove('chosen'); });
      btn.classList.add('chosen');
      var target = btn.dataset.target;
      if (target && sceneMap[target] !== undefined) {
        btnNext.onclick = function() {
          showScene(sceneMap[target]);
          btnNext.onclick = function() {
            if (currentIndex < scenes.length) showScene(currentIndex + 1);
          };
        };
      }
      updateNextButton();
    });
  });

  document.querySelectorAll('.visual-brief').forEach(function(vb) {
    var toggle = document.createElement('span');
    toggle.className = 'vb-toggle';
    toggle.textContent = '\\u{1f3a8} Visual brief \\u25b8';
    toggle.addEventListener('click', function() {
      vb.classList.toggle('open');
      toggle.textContent = vb.classList.contains('open')
        ? '\\u{1f3a8} Visual brief \\u25be'
        : '\\u{1f3a8} Visual brief \\u25b8';
    });
    vb.parentNode.insertBefore(toggle, vb);
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

    scene_offset = 1 if previously else 0
    total = len(scenes) + scene_offset
    scenes_html = "\n".join(render_scene(s, i + scene_offset, total) for i, s in enumerate(scenes))

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
    """Build index.html with links to all episodes."""
    links = []
    for ep_file in sorted(episode_files):
        data = load_episode(ep_file)
        ep_id = data.get("episode_id", "?")
        title = html.escape(data.get("episode_title", f"Эпизод {ep_id}"))
        lesson = html.escape(data.get("lesson", ""))
        scene_count = len(data.get("scenes", []))
        links.append(
            f'<a href="ep_{int(ep_id):03d}.html" class="ep-link">'
            f'<span class="ep-num">Эпизод {ep_id}</span>'
            f'<span class="ep-title">«{title}»</span>'
            f'<span class="ep-meta">{lesson} \u00b7 {scene_count} сцен</span>'
            f"</a>"
        )

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
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg); color: var(--text);
  max-width: 600px; margin: 0 auto; padding: 2rem 1rem;
}}
h1 {{ text-align: center; font-size: 1.5rem; margin-bottom: 0.5rem; }}
.subtitle {{ text-align: center; color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }}
.ep-link {{
  display: block; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  text-decoration: none; color: var(--text); transition: all 0.2s;
}}
.ep-link:hover {{ border-color: var(--accent); background: #1c1c28; }}
.ep-num {{ font-size: 0.8rem; color: var(--accent); font-weight: 600; }}
.ep-title {{ display: block; font-size: 1.1rem; margin: 0.2rem 0; }}
.ep-meta {{ font-size: 0.8rem; color: var(--muted); }}
</style>
</head>
<body>
<h1>Сила Слова</h1>
<p class="subtitle">День 1 — Акт I: Пробуждение</p>
{"".join(links)}
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
        print(f"  \u2713 Cleaned publish/game/")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for yf in yaml_files:
        build_episode(yf)

    build_index(yaml_files)
    print("Done.")


if __name__ == "__main__":
    main()
