---
name: qa-references
description: |
  Validates reference consistency in gameflow episodes.
  Checks that every "remember?", character mention, event reference, and
  lesson term usage is traceable to a concrete scene in current or previous episodes.
  Catches broken back-references like "Помнишь Дмитрика?" when Дмитрик never appeared.
  Triggers: "qa references", "check references", "qa-references", "validate references".
  Argument: episode number, range, or "all".
  Without argument — validates all episodes.
---

# QA References — Back-Reference Consistency Validator

You validate that every reference to prior knowledge in gameflow episodes
is traceable to a concrete scene the player has actually seen.

The core rule: **if the text says "помнишь X" or treats X as known,
then X must have appeared in a scene on the main line of the current
or a previous episode.** Branch-only content does NOT count as "known"
because the player may have skipped the branch.

## Language

All instructions in this file are in English.
All report output must be in **Russian** (error messages, descriptions).

## Input

- `pipeline/gameflow/episodes/ep_NNN.yaml` — episode(s) to validate
- `pipeline/episodes/day_NN.yaml` — episode plans (for cross-checking terms)
- `lessons_ru/lesson_*.yaml` — lesson source (for identifying lesson-only characters)

## Output

- Console report: PASS / FAIL per episode with details
- If issues found: specific scene IDs, exact quote, what's missing, how to fix

## Algorithm

### Step 1: Build Knowledge Graph

Process episodes in order (ep_001, ep_002, ...). For each episode,
walk the **main line only** (following `next_default` from s01, skipping
scenes with `branch_type` set). Build cumulative state:

```
knowledge = {
  characters_seen: [],     # names from characters_present on main line
  characters_introduced: { name: scene_id },
  events: [],              # key events from author_text/dialogue
  terms_introduced: [],    # from terms_introduced field
  terms_used: [],          # from terms_used field
  objects_seen: [],        # props, items mentioned
  locations_visited: [],   # from location field
  lesson_characters: [],   # characters from lessons (Дмитрик, Витя, etc.)
}
```

**Lesson characters** are names that exist in lesson briefs but NOT in
the drama (not in source/characters). These are teaching examples and
must be TOLD as fresh stories, not referenced as memories.

### Step 2: Identify References

For each scene, scan these text fields:
- `author_text`
- `author_text_after`
- `dialogue[].line`
- `feedback_success`
- `feedback_soft_fail`
- `correct_logic`

#### Reference patterns to detect:

**EXPLICIT BACK-REFERENCES** (highest priority):
- "помнишь" / "помните" / "вспомни" + name/event
- "ты уже знаешь" / "мы уже" / "ты уже видел"
- "как мы видели" / "как мы говорили" / "как было"
- "ранее" / "раньше" / "в прошлый раз"
- "снова" / "опять" + character/event (implying prior encounter)

**IMPLICIT BACK-REFERENCES** (medium priority):
- Character name used without introduction (not in characters_present
  of any prior main-line scene)
- Lesson term used before it appears in any episode's terms_introduced
- Event/object referenced as known ("дневник" before scene where diary is found)

**LESSON-CHARACTER REFERENCES** (high priority):
- Names from lesson briefs (Дмитрик, Витя, Оленка, Микола, Маша, Сашко, Петрик, etc.)
  used with "помнишь" or treated as known — these characters only exist
  in lesson examples and have NEVER appeared in the game flow
- Correct: "Представь: мальчик Дмитрик прибежал..." (fresh story)
- Broken: "Помнишь Дмитрика? Он сказал..." (player never met him)

### Step 3: Run Checks

#### CHECK 1: Explicit Back-References
```
For each explicit back-reference pattern found in scene S of episode E:
  Extract the referenced entity (name, event, term).
  Search knowledge graph (all main-line scenes before S, including
  prior episodes).
  
  FOUND → PASS
  NOT FOUND → ERROR: "Сцена {S}: «{quote}» — ссылка на {entity},
               но {entity} не появлялся в основном потоке.
               Последнее известное появление: {scene_id или 'нигде'}."
```

#### CHECK 2: Lesson Character Contamination
```
For each lesson character name found in episode text:
  Is the name in characters_present of any main-line scene? → PASS (drama character)
  Is the name introduced as a FRESH story ("представь", "однажды",
  "например", "есть мальчик/девочка")? → PASS
  Is the name referenced as KNOWN ("помнишь", "ты знаешь", no introduction)?
  → ERROR: "{name} — персонаж из урока, не из сюжета. Игрок его не знает.
     Нужно рассказать историю заново или убрать «помнишь»."
```

**Lesson character registry** — build from lessons_ru/:
Scan all lesson YAML files for character names that appear in lesson
examples but NOT in the drama character list (Марко, София, Софа, Лина,
Макс, Рей, Леон, Вера, Сем, Голос, мама). Any other proper name
(capitalized, Cyrillic) found in lesson texts is a lesson character.

#### CHECK 3: Term Usage Before Introduction
```
For each lesson term T used in scene S:
  Has T been listed in terms_introduced of the current or any
  prior episode?
  YES → PASS
  NO → ERROR: "Термин «{T}» используется в {S}, но ещё не введён.
       Первое введение: эпизод {E} (terms_introduced)."
```

#### CHECK 4: Character First Appearance
```
For each character name in dialogue or author_text of scene S:
  Has this character appeared in characters_present of any
  main-line scene before S (current + prior episodes)?
  YES → PASS
  NO → Is this a NEW introduction (first time in characters_present
       of S itself)?
    YES → PASS (legitimate introduction)
    NO → WARNING: "{name} упоминается в тексте {S}, но не в
         characters_present ни одной предыдущей сцены."
```

#### CHECK 5: Previously Block Check
```
For each episode:
  Does it contain a 'previously' field?
  YES → WARNING: "Эпизод {E} содержит блок 'previously'.
       Убрать — ребёнок только что прошёл предыдущий эпизод."
  NO → PASS
```

#### CHECK 6: Event Continuity
```
For each scene S that references a specific prior event
(e.g., "дверь захлопнулась", "число упало", "Вера забрала дневник"):
  Can this event be traced to a specific scene in prior episodes?
  YES → PASS
  NO → WARNING: "Событие «{event}» в {S} не прослеживается
       до конкретной сцены. Возможно — новый элемент, но проверь."
```

### Step 4: Cross-Episode Term Chain
```
For episodes in order, verify:
  terms_used of episode E ⊆ union of terms_introduced of all episodes before E
  
  For each term in terms_used NOT in prior terms_introduced:
    ERROR: "Эпизод {E} использует термин «{T}» (terms_used),
     но он ещё не введён ни в одном предыдущем эпизоде."
```

### Step 5: Report

Output format:

```
═══════════════════════════════════════════
QA REFERENCES — ep_NNN: «Title»
═══════════════════════════════════════════

CHECK 1 — Явные обратные ссылки
  ✅ PASS | ❌ FAIL: описание проблемы
     Сцена: ep002_s03
     Текст: «Помнишь Дмитрика?»
     Проблема: Дмитрик не появлялся в основном потоке
     Фикс: рассказать историю заново

CHECK 2 — Персонажи из уроков
  ✅ PASS | ❌ FAIL: описание

CHECK 3 — Термины до введения
  ✅ PASS | ❌ FAIL: описание

CHECK 4 — Первое появление персонажей
  ✅ PASS | ⚠️ WARNING: описание

CHECK 5 — Блоки «ранее»
  ✅ PASS | ⚠️ WARNING: описание

CHECK 6 — Событийная связность
  ✅ PASS | ⚠️ WARNING: описание

CHECK 7 — Цепочка терминов между эпизодами
  ✅ PASS | ❌ FAIL: описание

───────────────────────────────────────────
ИТОГ: X PASS, Y FAIL, Z WARNING
═══════════════════════════════════════════
```

When running on "all", show summary at the end:

```
═══════════════════════════════════════════
ИТОГО: N эпизодов проверено
  ✅ PASS: X
  ❌ FAIL: Y (эпизоды: ...)
  ⚠️ WARNING: Z
═══════════════════════════════════════════
```

## Common Errors and Fixes

### ERROR: Lesson character referenced as known
**Problem:** "Помнишь Дмитрика?" — Дмитрик is from lesson 1A, never appeared in game.
**Fix:** Replace "Помнишь" with a fresh telling: "Представь: мальчик Дмитрик
прибежал в школу и крикнул: «Завтра уроков не будет!»"

### ERROR: Term used before introduction
**Problem:** Scene uses "неправда" as a concept but episode hasn't introduced it yet.
**Fix:** Either move the scene after term introduction, or rephrase to avoid the term.

### ERROR: Explicit back-reference to nothing
**Problem:** "Ты уже видел, как..." but the referenced event is not in any prior scene.
**Fix:** Either add the event to a prior scene, or rephrase as a new statement.

### WARNING: Previously block exists
**Problem:** Episode has a recap block.
**Fix:** Remove the `previously:` field entirely.

## Constraints

- This skill does NOT edit episode files — it only reports issues
- The gameflow-build or manual editing fixes reported issues
- Run this AFTER gameflow episodes are created, BEFORE final build
- Can be run on single episode, range, or all
- Knowledge graph is cumulative: ep_003 check includes knowledge from ep_001 + ep_002
- Branch scenes are tracked separately — they don't contribute to "known" knowledge
