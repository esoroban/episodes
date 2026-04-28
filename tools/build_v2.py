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
import hashlib
import html as html_mod
import json
import pathlib
import random
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


BODY_INJECTION = (
    '<div id="v2-audio-controls">'
    '<button id="v2-rate" type="button" title="Скорость 1× / 2×" aria-label="Скорость">1×</button>'
    '<button id="v2-play" type="button" title="Play / Pause" aria-label="Play/Pause">▶</button>'
    '<button id="v2-lang" type="button" title="Перевод (UK ↔ RU)" aria-label="Перевод">🌐 Перевод</button>'
    '<button id="v2-copy" type="button" title="Скопировать содержимое сцены" aria-label="Копировать">📋 Копировать</button>'
    '</div>\n'
    '<div id="v2-scene-badge">—</div>\n'
)

PROD_OVERRIDES = (
    '<style id="v2-prod-overrides">'
    # Debug-панель из image_prompts_experiment перекрывает #btnNext на мобилках.
    '.ipe-debug{display:none!important}'
    # Источник рендерит верхний ряд .audio-controls (text-toggle + audio-pause)
    # и левую .episode-nav. Оба блока выносим наружу — сверху живёт только
    # v2-группа (rate / play / lang) и scene-badge.
    '.audio-controls,.episode-nav{display:none!important}'
    # v2 audio-controls: три кнопки в ряд, верх-право. Всегда видимы.
    '#v2-audio-controls{'
    'position:fixed;top:10px;right:12px;z-index:220;'
    'display:flex;gap:6px;align-items:center'
    '}'
    '#v2-audio-controls button{'
    'background:rgba(0,0,0,0.65);color:#fff;'
    'border:1px solid rgba(255,255,255,0.25);'
    'border-radius:8px;padding:7px 10px;line-height:1;cursor:pointer;'
    'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;'
    'font-size:13px;font-weight:600;min-width:36px;text-align:center'
    '}'
    '#v2-audio-controls button:hover{background:rgba(0,0,0,0.85)}'
    # Scene-badge: верх-лево, контрастный моно-шрифт. Показывает epNNN_sMM.
    '#v2-scene-badge{'
    'position:fixed;top:10px;left:12px;z-index:220;'
    'background:rgba(0,0,0,0.7);color:#fff;'
    'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;'
    'font-size:12px;font-weight:600;letter-spacing:0.02em;'
    'padding:6px 9px;border-radius:6px;'
    'border:1px solid rgba(255,255,255,0.22);pointer-events:none'
    '}'
    # iOS Safari: `animation: fadeIn` с transform:translateY() на .scene
    # оставляет element в качестве containing block для position:fixed
    # даже после анимации → .story-choice (fixed;bottom:80px) попадает за
    # overflow:hidden. Убираем анимацию.
    '.scene{animation:none!important}'
    # Audio-mode: choice-кнопки появляются после того как аудио-очередь
    # для активной сцены опустела (class `.audio-done`, ставит JS ниже).
    'body.audio-mode section.scene:not(.audio-done) .story-choice{'
    'display:none!important'
    '}'
    # Text-mode: choice-кнопки перекрывали субтитры снизу. UX:
    # (1) Показ: текст субтитров + кнопка «Дальше» внизу. Choice скрыт.
    # (2) Клик «Дальше» → ставим `.v2-choice-revealed` → текст скрыт, choice показан.
    # Аудио-режим не трогаем — там вся очередь уже отыгрывает текст в речи.
    'body:not(.audio-mode) section.scene.active:not(.v2-choice-revealed) .story-choice{'
    'display:none!important'
    '}'
    'body:not(.audio-mode) section.scene.active.v2-choice-revealed .scene-content .author-text,'
    'body:not(.audio-mode) section.scene.active.v2-choice-revealed .scene-content .dialogue-block{'
    'display:none!important'
    '}'
    # --- Фикс невидимых choice-кнопок на iOS Safari ---
    # Гипотеза: .story-choice (position:fixed) внутри активной .scene,
    # у которой overflow:hidden, на iOS хит-тестится по viewport, но
    # ПАЙНТ клиппится ancestor layer-ом. Даёт ровно симптом: DOM есть,
    # tap работает, на экране ничего. Лечим overflow на активной сцене.
    'body.audio-mode section.scene.active{overflow:visible!important}'
    # Дополнительно: у .nav-bar базовое правило ставит backdrop-filter:
    # blur(12px). На iOS это — классический триггер странного
    # compositing-поведения соседних fixed-слоёв. Сбрасываем.
    '.nav-bar{'
    '-webkit-backdrop-filter:none!important;'
    'backdrop-filter:none!important'
    '}'
    '</style>\n'
    '<script id="v2-audio-done-tracker">\n'
    '(function () {\n'
    '  var playingSet = new Set();\n'
    '  // Timestamp момента, когда в последний раз ЧТО-ТО играло.\n'
    '  // Если сейчас ничего не играет и с того момента прошло >SILENCE_MS —\n'
    '  // считаем, что автор дочитал, и показываем кнопки выбора.\n'
    '  var lastActivityAt = Date.now();\n'
    '  var SILENCE_MS = 300;\n'
    '  var currentRate = 1;  // playback rate (1x / 2x)\n'
    '\n'
    '  // Patch HTMLAudioElement.prototype.play — на первый play() каждому\n'
    '  // аудио навешиваем трекинг. Работает для всех способов создания.\n'
    '  var origPlay = HTMLAudioElement.prototype.play;\n'
    '  HTMLAudioElement.prototype.play = function () {\n'
    '    var a = this;\n'
    '    if (!a.__v2Tracked) {\n'
    '      a.__v2Tracked = true;\n'
    '      a.addEventListener("play",  function () { playingSet.add(a); lastActivityAt = Date.now(); });\n'
    '      a.addEventListener("pause", function () { playingSet.delete(a); });\n'
    '      a.addEventListener("ended", function () { playingSet.delete(a); });\n'
    '      a.addEventListener("error", function () { playingSet.delete(a); });\n'
    '    }\n'
    '    lastActivityAt = Date.now();\n'
    '    try { a.playbackRate = currentRate; } catch (_) {}\n'
    '    return origPlay.apply(a, arguments);\n'
    '  };\n'
    '\n'
    '  function anyPlaying() {\n'
    '    var r = false;\n'
    '    playingSet.forEach(function (a) { if (!a.paused && !a.ended) r = true; });\n'
    '    return r;\n'
    '  }\n'
    '\n'
    '  function audioDoneCheck() {\n'
    '    var active = document.querySelector(".scene.active");\n'
    '    if (!active) return;\n'
    '    if (!document.body.classList.contains("audio-mode")) {\n'
    '      active.classList.add("audio-done");\n'
    '      return;\n'
    '    }\n'
    '    if (anyPlaying()) {\n'
    '      lastActivityAt = Date.now();\n'
    '      active.classList.remove("audio-done");\n'
    '      return;\n'
    '    }\n'
    '    if (Date.now() - lastActivityAt > SILENCE_MS) {\n'
    '      active.classList.add("audio-done");\n'
    '    }\n'
    '  }\n'
    '\n'
    '  function updateBadge(sid) {\n'
    '    var badge = document.getElementById("v2-scene-badge");\n'
    '    if (badge) badge.textContent = sid || "—";\n'
    '  }\n'
    '\n'
    '  // Text-mode choice-gate: пока юзер не нажал «Дальше» на сцене\n'
    '  // с .story-choice, апстрим-логика делает btnNext.disabled=true.\n'
    '  // Форс-разблокируем, чтобы юзер мог раскрыть choice нажатием.\n'
    '  function handleTextModeChoiceGate(active) {\n'
    '    if (document.body.classList.contains("audio-mode")) return;\n'
    '    if (!active.querySelector(".story-choice")) return;\n'
    '    if (active.classList.contains("v2-choice-revealed")) return;\n'
    '    if (active.querySelector(".choice-option.chosen")) return;\n'
    '    var btn = document.getElementById("btnNext");\n'
    '    if (btn && btn.disabled) btn.disabled = false;\n'
    '  }\n'
    '\n'
    '  function updateV2PlayLabel() {\n'
    '    var btn = document.getElementById("v2-play");\n'
    '    if (!btn) return;\n'
    '    var inAudio = document.body.classList.contains("audio-mode");\n'
    '    var pauseBtn = document.getElementById("audio-pause");\n'
    '    var playing = inAudio && pauseBtn &&\n'
    '                  pauseBtn.classList.contains("visible") &&\n'
    '                  pauseBtn.textContent === "⏸";\n'
    '    btn.textContent = playing ? "⏸" : "▶";\n'
    '  }\n'
    '\n'
    '  var lastActiveSid = null;\n'
    '  function checkScene() {\n'
    '    var active = document.querySelector(".scene.active");\n'
    '    if (!active) return;\n'
    '    var sid = active.dataset.sceneId || "";\n'
    '    if (sid !== lastActiveSid) {\n'
    '      lastActiveSid = sid;\n'
    '      lastActivityAt = Date.now();\n'
    '      document.querySelectorAll("section.scene.audio-done").forEach(function (s) {\n'
    '        if (s !== active) s.classList.remove("audio-done");\n'
    '      });\n'
    '      document.querySelectorAll("section.scene.v2-choice-revealed").forEach(function (s) {\n'
    '        if (s !== active) s.classList.remove("v2-choice-revealed");\n'
    '      });\n'
    '      updateBadge(sid);\n'
    '    }\n'
    '    audioDoneCheck();\n'
    '    handleTextModeChoiceGate(active);\n'
    '    updateV2PlayLabel();\n'
    '  }\n'
    '\n'
    '  function init() {\n'
    '    setInterval(checkScene, 250);\n'
    '\n'
    '    // Rate toggle (1× ↔ 2×)\n'
    '    var rateBtn = document.getElementById("v2-rate");\n'
    '    if (rateBtn) {\n'
    '      rateBtn.addEventListener("click", function (e) {\n'
    '        e.stopPropagation();\n'
    '        currentRate = currentRate === 1 ? 2 : 1;\n'
    '        rateBtn.textContent = currentRate + "×";\n'
    '        playingSet.forEach(function (a) {\n'
    '          try { a.playbackRate = currentRate; } catch (_) {}\n'
    '        });\n'
    '      });\n'
    '    }\n'
    '\n'
    '    // Play / Pause. Если audio-mode выключен — клик включает его\n'
    '    // (source-кнопка #text-toggle делает всю работу: переключает\n'
    '    // body.audio-mode и стартует очередь). Если включён — прокси к\n'
    '    // #audio-pause (pause/resume текущего трека).\n'
    '    var playBtn = document.getElementById("v2-play");\n'
    '    if (playBtn) {\n'
    '      playBtn.addEventListener("click", function (e) {\n'
    '        e.stopPropagation();\n'
    '        var inAudio = document.body.classList.contains("audio-mode");\n'
    '        if (!inAudio) {\n'
    '          var toggle = document.getElementById("text-toggle");\n'
    '          if (toggle) toggle.click();\n'
    '        } else {\n'
    '          var pauseBtn = document.getElementById("audio-pause");\n'
    '          if (pauseBtn) pauseBtn.click();\n'
    '        }\n'
    '      });\n'
    '    }\n'
    '\n'
    '    // Язык: /uk/ ↔ /ru/ в том же пути.\n'
    '    var langBtn = document.getElementById("v2-lang");\n'
    '    if (langBtn) {\n'
    '      langBtn.addEventListener("click", function (e) {\n'
    '        e.stopPropagation();\n'
    '        var p = location.pathname;\n'
    '        var next = null;\n'
    '        if (p.indexOf("/uk/") !== -1) next = p.replace("/uk/", "/ru/");\n'
    '        else if (p.indexOf("/ru/") !== -1) next = p.replace("/ru/", "/uk/");\n'
    '        if (next && next !== p) {\n'
    '          location.href = next + location.search + location.hash;\n'
    '        }\n'
    '      });\n'
    '    }\n'
    '\n'
    '    // Copy: собрать текстовое содержимое активной сцены и положить\n'
    '    // в буфер обмена. Берём: scene_id, автор-текст, dialogue-реплики,\n'
    '    // chat-пузыри (если has-phone), choice-вопрос + варианты.\n'
    '    var copyBtn = document.getElementById("v2-copy");\n'
    '    if (copyBtn) {\n'
    '      var origLabel = copyBtn.textContent;\n'
    '      copyBtn.addEventListener("click", function (e) {\n'
    '        e.stopPropagation();\n'
    '        var active = document.querySelector("section.scene.active");\n'
    '        if (!active) return;\n'
    '        var lines = [];\n'
    '        var sid = active.dataset.sceneId || "";\n'
    '        if (sid) lines.push("[" + sid + "]");\n'
    '        active.querySelectorAll(".scene-content .author-text p").forEach(function (p) {\n'
    '          var t = (p.textContent || "").trim();\n'
    '          if (t) lines.push(t);\n'
    '        });\n'
    '        active.querySelectorAll(".scene-content .dialogue-block").forEach(function (d) {\n'
    '          var who = d.querySelector(".dl-who");\n'
    '          d.querySelectorAll("p").forEach(function (p) {\n'
    '            var t = (p.textContent || "").trim();\n'
    '            if (!t) return;\n'
    '            var prefix = who && who.textContent ? who.textContent.trim() + ": " : "";\n'
    '            lines.push(prefix + t);\n'
    '          });\n'
    '        });\n'
    '        var phone = active.querySelector(".phone[data-chat-messages]");\n'
    '        if (phone) {\n'
    '          try {\n'
    '            var msgs = JSON.parse(phone.dataset.chatMessages);\n'
    '            msgs.forEach(function (m) {\n'
    '              if (!m) return;\n'
    '              var txt = (m.x || "").trim();\n'
    '              if (!txt) return;\n'
    '              var who = m.name || m.s || "";\n'
    '              lines.push((who ? who + ": " : "") + txt);\n'
    '            });\n'
    '          } catch (_) {}\n'
    '        }\n'
    '        var choiceQ = active.querySelector(".story-choice .choice-question");\n'
    '        if (choiceQ && (choiceQ.textContent || "").trim()) {\n'
    '          lines.push("");\n'
    '          lines.push(choiceQ.textContent.trim());\n'
    '          active.querySelectorAll(".story-choice .choice-option").forEach(function (b, i) {\n'
    '            var t = (b.textContent || "").trim();\n'
    '            if (t) lines.push((i + 1) + ") " + t);\n'
    '          });\n'
    '        }\n'
    '        var text = lines.join("\\n").replace(/\\n{3,}/g, "\\n\\n").trim();\n'
    '        var done = function (ok) {\n'
    '          copyBtn.textContent = ok ? "✓ Скопировано" : "⚠ Ошибка";\n'
    '          setTimeout(function () { copyBtn.textContent = origLabel; }, 1400);\n'
    '        };\n'
    '        if (navigator.clipboard && navigator.clipboard.writeText) {\n'
    '          navigator.clipboard.writeText(text).then(function () { done(true); },\n'
    '                                                     function () { done(false); });\n'
    '        } else {\n'
    '          try {\n'
    '            var ta = document.createElement("textarea");\n'
    '            ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";\n'
    '            document.body.appendChild(ta); ta.select();\n'
    '            var ok = document.execCommand("copy");\n'
    '            document.body.removeChild(ta);\n'
    '            done(ok);\n'
    '          } catch (_) { done(false); }\n'
    '        }\n'
    '      });\n'
    '    }\n'
    '\n'
    '    // Text-mode choice-gate: перехват клика на #btnNext ДО основного\n'
    '    // handler\'а. Регистрируем на document в capture-фазе —\n'
    '    // document-handler отрабатывает раньше target-handler\'ов, и\n'
    '    // stopImmediatePropagation блокирует основной (который\n'
    '    // вызывает goForward и уводит сцену).\n'
    '    document.addEventListener("click", function (e) {\n'
    '      var t = e.target;\n'
    '      if (!t || t.id !== "btnNext") return;\n'
    '      if (document.body.classList.contains("audio-mode")) return;\n'
    '      var active = document.querySelector("section.scene.active");\n'
    '      if (!active) return;\n'
    '      if (!active.querySelector(".story-choice")) return;\n'
    '      if (active.classList.contains("v2-choice-revealed")) return;\n'
    '      if (active.querySelector(".choice-option.chosen")) return;\n'
    '      e.stopImmediatePropagation();\n'
    '      e.preventDefault();\n'
    '      active.classList.add("v2-choice-revealed");\n'
    '    }, true);\n'
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


def shuffle_quiz_options(html: str, ep_id: str) -> tuple[str, int]:
    """Reorder Telegram-chat quiz options inside `data-chat-messages` attributes
    so that correct answers are uniformly distributed across positions over the
    whole episode. Same algorithm as build_game.balance_episode_quizzes().

    Two-phase:
      1. Walk the entire HTML, collect every quiz option list across all
         data-chat-messages attributes, in document order.
      2. Group by len(options); for each group build round-robin target
         positions, shuffle with seed = sha1(ep_id + n_opts). Move the correct
         option in each quiz to its target position. Keep other options in
         their original relative order.

    Result: for an episode with 12 binary quizzes, exactly 6 have correct
    on top and 6 on bottom — no streaks, but order between specific quizzes
    stays stable across rebuilds (deterministic per-(episode, n_opts) seed).

    Returns (rewritten_html, n_quizzes_balanced).
    """
    pattern = re.compile(r'data-chat-messages="([^"]*)"')

    blocks = []
    for m in pattern.finditer(html):
        encoded = m.group(1)
        decoded = html_mod.unescape(encoded)
        try:
            messages = json.loads(decoded)
        except json.JSONDecodeError:
            blocks.append((m.start(), m.end(), None))
            continue
        if not isinstance(messages, list):
            blocks.append((m.start(), m.end(), None))
            continue
        blocks.append((m.start(), m.end(), messages))

    quiz_refs = []
    for _, _, messages in blocks:
        if messages is None:
            continue
        for msg in messages:
            if not isinstance(msg, dict) or msg.get("t") != "quiz":
                continue
            opts = msg.get("o")
            if not isinstance(opts, list) or len(opts) < 2:
                continue
            quiz_refs.append(opts)

    from collections import defaultdict
    by_n = defaultdict(list)
    for opts in quiz_refs:
        by_n[len(opts)].append(opts)

    n_quizzes = 0
    for n_opts, group in by_n.items():
        if n_opts < 2:
            continue
        k = len(group)
        targets = [j % n_opts for j in range(k)]
        seed = int(hashlib.sha1(f"{ep_id}::{n_opts}".encode("utf-8")).hexdigest()[:12], 16)
        random.Random(seed).shuffle(targets)
        for opts, target in zip(group, targets):
            correct_idx = next(
                (i for i, o in enumerate(opts) if isinstance(o, dict) and o.get("c")),
                None,
            )
            if correct_idx is None:
                continue
            correct_obj = opts.pop(correct_idx)
            opts.insert(target, correct_obj)
            n_quizzes += 1

    rewritten_parts = []
    cursor = 0
    for start, end, messages in blocks:
        rewritten_parts.append(html[cursor:start])
        if messages is None:
            rewritten_parts.append(html[start:end])
        else:
            new_decoded = json.dumps(messages, ensure_ascii=False)
            new_encoded = html_mod.escape(new_decoded, quote=True)
            rewritten_parts.append(f'data-chat-messages="{new_encoded}"')
        cursor = end
    rewritten_parts.append(html[cursor:])
    return "".join(rewritten_parts), n_quizzes


def rewrite_html(html: str, public_url: str, nnn: str) -> tuple[str, int, int, int]:
    """Return (rewritten_html, n_audio, n_images, n_chat_images) counts."""
    base = f"{public_url}/ep_{nnn}"

    # Match "audio/<filename>" or "images/<filename>" in double quotes.
    audio_pat = re.compile(r'"audio/([^"]+)"')
    image_pat = re.compile(r'"images/([^"]+)"')
    # chat_images в source'е лежат в `data-chat-messages`-атрибуте,
    # который HTML-encoded: внутри него JSON-кавычки записаны как &quot;,
    # а путь — `../chat_images/FILE` (относительный из-за JS-префикса
    # `images/`, см. ниже). Переписываем на абсолютный CDN URL и дальше
    # патчим JS, чтобы он не префиксил абсолютные URL.
    chat_img_pat = re.compile(r'&quot;\.\./chat_images/([^&]+)&quot;')

    n_audio = 0
    n_images = 0
    n_chat = 0

    def sub_audio(m: re.Match) -> str:
        nonlocal n_audio
        n_audio += 1
        return f'"{base}/audio/{m.group(1)}"'

    def sub_image(m: re.Match) -> str:
        nonlocal n_images
        n_images += 1
        return f'"{base}/images/{m.group(1)}"'

    def sub_chat_img(m: re.Match) -> str:
        nonlocal n_chat
        n_chat += 1
        return f'&quot;{base}/chat_images/{m.group(1)}&quot;'

    # ПЕРВЫМ: патч JS-рендера addImage. В source-коде строка:
    #   '<img src="images/'+m.src+'"
    # То есть внутри src="..." сидит JS-конкатенация. Если сперва прогнать
    # image_pat regex, он захватит `"images/'+m.src+'"` как одну пару и
    # впишет CDN — строка развалится. Поэтому патчим JS РАНЬШЕ image/chat.
    # После патча m.src (абсолютный CDN для chat_images) летит в src без
    # префикса, обычные имена файлов префиксятся `images/`.
    old_js = '\'<img src="images/\'+m.src+\'"'
    new_js = '\'<img src="\'+(/:\\/\\//.test(m.src)?m.src:"images/"+m.src)+\'"'
    html = html.replace(old_js, new_js)

    html = audio_pat.sub(sub_audio, html)
    html = image_pat.sub(sub_image, html)
    html = chat_img_pat.sub(sub_chat_img, html)
    # Сократить `pause_after_ms` между репликами в 4 раза (150→38, 400→100,
    # 800→200). Источник ставит 150/400/800 мс — для живой аудио-драмы это
    # много, особенно при ×2 playbackRate в debug-режиме. Делим на 4.
    pause_pat = re.compile(r'"pause_after_ms"\s*:\s*(\d+)')
    html = pause_pat.sub(
        lambda m: f'"pause_after_ms": {round(int(m.group(1)) / 4)}',
        html,
    )
    # Инжекция prod-overrides (CSS + audio-done tracker) в <head>
    # и debug-skip-кнопки сразу после <body>.
    html = html.replace("</head>", PROD_OVERRIDES + "</head>", 1)
    # Источник пишет либо `<body>` (ep_001..005), либо `<body class="lang-uk">`
    # (ep_006+). Инжектим сразу после закрывающего `>` первого <body ...>.
    html = re.sub(
        r"(<body\b[^>]*>)",
        lambda m: m.group(1) + "\n" + BODY_INJECTION,
        html,
        count=1,
    )
    return html, n_audio, n_images, n_chat


def build_episode(src: pathlib.Path, nnn: str, public_url: str) -> dict:
    src_html = src / f"ep_{nnn}" / f"ep_{nnn}.html"
    if not src_html.exists():
        return {"nnn": nnn, "skipped": True, "reason": f"missing {src_html}"}

    html = src_html.read_text(encoding="utf-8")
    html, n_shuffled = shuffle_quiz_options(html, ep_id=str(int(nnn)))
    rewritten, n_audio, n_images, n_chat = rewrite_html(html, public_url, nnn)

    out_html = OUT_DIR / f"ep_{nnn}" / f"ep_{nnn}.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(rewritten, encoding="utf-8")

    return {
        "nnn": nnn,
        "skipped": False,
        "audio": n_audio,
        "images": n_images,
        "chat_images": n_chat,
        "shuffled": n_shuffled,
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
        help="Episode numbers (e.g. 1 2 5). Default — all 1..32",
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
        nums = list(range(1, 33))
    nnns = [f"{n:03d}" for n in nums]

    idx_out = build_index(src)
    print(f"index      → {idx_out.relative_to(REPO)}")

    total_audio = 0
    total_images = 0
    total_chat = 0
    total_shuffled = 0
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
        total_chat += r["chat_images"]
        total_shuffled += r["shuffled"]
        print(f"ep_{nnn}     → {r['out'].relative_to(REPO)}  "
              f"(audio: {r['audio']}, images: {r['images']}, "
              f"chat_images: {r['chat_images']}, "
              f"quiz_shuffled: {r['shuffled']})")

    print()
    print(f"built {built}/{len(nnns)} episodes")
    print(f"rewrites — audio: {total_audio}, images: {total_images}, "
          f"chat_images: {total_chat}, quiz_shuffled: {total_shuffled}")
    if skipped:
        print(f"skipped {len(skipped)}:")
        for nnn, reason in skipped:
            print(f"  ep_{nnn}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
