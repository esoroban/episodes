---
name: gameflow-drama
description: |
  Restores drama that was in the book but got stripped during gameflow conversion.
  Reads book episodes (server/book/), compares with gameflow YAML,
  restores missing drama beats, reconnects quizzes to story.
  Does NOT enforce artificial chain-length limits — if the book shows
  Софа teaching uninterrupted, gameflow keeps it that way.
  Triggers: "restore drama", "gameflow-drama", "drama check", "fix drama".
  Argument: episode number, range ("ep 1-4"), or "all".
  Without argument — asks which episode.
---

# Gameflow Drama — Drama Preservation & Restoration (Step 4b)

You ensure that gameflow episodes preserve the drama from the book episodes.
The gameflow layer structures content into scenes but must NOT strip drama.

## The Problem This Skill Solves

When converting book episodes to gameflow, drama gets lost:
1. **Stripped drama beats** — when the book had narrative/dialogue between
   quizzes but the gameflow dropped it. (The issue is NOT quiz count per se
   — it's drama that was in the book being missing in gameflow. If the book
   had a long uninterrupted teaching sequence by Софа, gameflow keeps it
   long; if the book broke to Марко's reaction or a scene change, gameflow
   must too.)
2. **Missing drama beats** — school scenes, emotional moments, character
   interactions cut from gameflow
3. **Disconnected quizzes** — abstract examples replace story-connected
   quizzes (e.g., "арбуз 8 кг" instead of "Витя сказал 'все говорят'")
4. **Recap contamination** — references to "помнишь?" or "ранее"
   instead of flowing forward

**Length principle:** phone chain length has NO numerical limit. If the book
shows Софа teaching 20 messages straight without a drama break, gameflow
keeps 20 messages straight. Drama breaks the chain when the book says so —
not every N quizzes by artificial rule.

## Language

All instructions in this file are in English.
All generated output must be in **Russian**.

## Input

- `server/book/ep_NNN.md` — full book episode (drama reference)
- `pipeline/gameflow/episodes/ep_NNN.yaml` — current gameflow (to fix)
- `pipeline/episodes/day_NN.yaml` — episode plan (source of truth)
- `pipeline/gameflow/spec/gameflow_schema.md` — scene format

## Output

- Updated `pipeline/gameflow/episodes/ep_NNN.yaml` with drama restored
- Console report: what was added, what was reconnected

## Mandatory Reading

1. `pipeline/gameflow/spec/gameflow_schema.md` — scene format
2. `pipeline/gameflow/spec/pipeline_rules.md` — layer rules
3. The book episode being processed
4. The current gameflow episode

## Core Rule

**100% transfer. The book episode + day plan already contain all drama
and all quizzes in the right proportion. Gameflow is FORMATTING, not
rewriting. Transfer everything — don't drop drama, don't drop quizzes.**

The book has drama scenes woven between quizzes. If the gameflow lost
a drama scene that exists in the book — restore it. If the book has
a quiz triggered by a character's words — keep that connection.

No artificial ratios or metrics. Just transfer what's already written.

### What gets lost and why

Drama gets lost when gameflow-build converts the day plan's `sofa_block`
and `challenge` into quiz scenes but skips the narrative paragraphs
between quizzes that exist in the book. The fix: read the book,
find what's missing, put it back.

### No Recap

Drama scenes must move the story FORWARD. No flashbacks, no "ранее",
no "в предыдущей серии". The player just experienced it.

## Algorithm

### Step 1: Analyze Current Gameflow

1. Read the gameflow YAML
2. Map every scene: DRAMA / QUIZ / TRANSITION
3. Map natural drama breaks (scene/location changes, new characters, Марко reactions)
4. List all quiz questions — note which are story-connected vs abstract

### Step 2: Analyze Book Episode

1. Read the book markdown
2. Extract all dramatic beats:
   - Narrative paragraphs (not quiz-related)
   - Character dialogues (not quiz prompts)
   - Emotional reactions (gut_feeling moments)
   - Environmental descriptions
   - Character interactions
3. For each beat, note its position relative to quizzes
4. Extract quiz-to-story connections:
   - Which character said what → which quiz follows

### Step 3: Diff — What's Missing

Compare gameflow vs book:

```
For each dramatic beat in book:
  Is it present in gameflow (in any scene's author_text or dialogue)?
  YES → mark as PRESENT
  NO → mark as MISSING, classify:
    - CRITICAL: character interaction, plot point, emotional moment
    - IMPORTANT: environmental detail, atmosphere
    - OPTIONAL: minor descriptive flourish
```

```
For each quiz in gameflow:
  Is it story-connected in the book?
  YES → Is the connection preserved in gameflow?
    YES → PASS
    NO → mark as DISCONNECTED
  NO → mark as ABSTRACT (OK)
```

### Step 4: Restore Missing Drama

For each MISSING dramatic beat from the book:

1. Find where it belongs in the gameflow (between which scenes)
2. Create a scene using the book text
3. Insert it, updating navigation

**Scene template for restored drama:**

```yaml
- scene_id: ep{NNN}_s{NN}d  # 'd' suffix for restored drama
  episode_id: N
  source_ref: day_NN.epN.{block}
  scene_type: narrative  # or dialogue
  location: "from book"
  time: "from book"
  characters_present: [from book]
  author_text: >
    {text from book episode — transfer, don't rewrite}
  mood: "{mood}"
  next_default: ep{NNN}_s{next}
  visual_brief:
    background: "..."
    atmosphere: "..."
    ui_mode: reading  # or dialogue
```

**Placement:** where the book has it. The book's order of drama/quiz
is already correct — mirror it.

### Step 5: Reconnect Quizzes

For each DISCONNECTED quiz:

1. Find the book's story context for this quiz
2. Add the character's line as `dialogue` before the quiz
3. Or add it to `author_text` of the preceding drama scene

**Example:**

Before (disconnected):
```yaml
- scene_id: ep002_s11
  scene_type: quiz
  question: "«Мой дедушка самый старый в нашем доме.» Факт, мнение или неправда?"
```

After (reconnected):
```yaml
- scene_id: ep002_s10b
  scene_type: dialogue
  dialogue:
    - who: Данила
      line: "Мой дедушка самый старый в нашем доме."
    - who: Софа
      line: "Внимание. Факт, мнение или неправда?"
  next_default: ep002_s11

- scene_id: ep002_s11
  scene_type: quiz
  question: "«Мой дедушка самый старый в нашем доме.» Факт, мнение или неправда?"
```

### Step 6: Expand Thin Drama Scenes

For each drama scene with < 100 characters of author_text:

1. Find the corresponding book passage
2. Expand with concrete sensory details from the book
3. Keep the expansion within the scene's `mood` and `location`

### Step 7: Update Navigation

After inserting drama breakers:
1. Update `next_default` of the scene before the breaker
2. Set the breaker's `next_default` to the next quiz
3. Update the episode flow comment at the top of the file
4. Verify: walk the full scene chain from s01 to the cliffhanger

### Step 8: Validate

1. All CRITICAL dramatic beats from book are PRESENT
2. Quiz count unchanged (drama restoration doesn't add/remove quizzes)
3. No broken navigation links
4. Run `python3 tools/validate_gameflow.py` to verify

## Report Format

```
═══════════════════════════════════════════
DRAMA RESTORATION — ep_NNN: «Title»
═══════════════════════════════════════════

БЫЛО:
  Сцен: 25 (drama: 8, quiz: 15, transition: 2)
  Макс. квиз-стрик: 9 (s13–s21)
  Drama/quiz: 22% / 78%

СТАЛО:
  Сцен: 31 (drama: 14, quiz: 15, transition: 2)
  Макс. квиз-стрик: 3
  Drama/quiz: 45% / 55%

ДОБАВЛЕНО:
  + ep001_s05d — Школа: Данила «тебе приснилось» (из книги, стр.99-110)
  + ep001_s08d — Парта с наклейками котов (из книги, стр.112-120)
  + ep001_s14d — Реакция Марко: сжимает телефон (из книги, стр.145-150)
  + ep001_s17d — Олена шепчется (из книги, стр.155-160)
  + ep001_s20d — Витя: «все говорят» (из книги, стр.165-170)

ПЕРЕПОДКЛЮЧЕНО:
  ~ s05: квиз теперь привязан к словам Данилы (было: абстрактный)
  ~ s13: квиз привязан к словам Вити (было: абстрактный)

ПРОПУЩЕНО (нет в книге / не критично):
  - Описание школьной мебели (декоративное)

───────────────────────────────────────────
QUIZ COUNT: 15 → 15 (без изменений)
NAVIGATION: ✅ замкнута
═══════════════════════════════════════════
```

## Interaction with Other Skills

### Before gameflow-drama:
- `gameflow-build` creates initial gameflow YAML
- Drama may already be thin at this point

### After gameflow-drama:
- `qa-references` validates that new drama scenes don't break references
- `qa-branches` validates branch continuity
- `validate_gameflow.py` checks technical validity
- `build_game.py` generates HTML

### Integration into gameflow-build:
When `gameflow-build` runs, it should produce initial gameflow.
Then `gameflow-drama` runs as a second pass to enrich it.
The pipeline becomes:

```
gameflow-build → gameflow-drama → gameflow-branch → qa-references → qa-branches → validate → build
```

## Constraints

- DO NOT change quiz questions, answers, or order
- DO NOT add new quizzes
- DO NOT invent story events — only use book/plan content
- DO NOT change terms_introduced or terms_used
- DO NOT break phone chains — drama breakers go BETWEEN chains, not inside
- CAN expand existing author_text with book content
- CAN add new drama scenes between quiz blocks
- CAN reconnect quizzes to story context
- CAN adjust visual_brief for new scenes

## Phone Chain Awareness (CRITICAL)

Quiz scenes often form phone chains (consecutive Софа scenes at same
location rendered as a chat interface). Drama breakers must respect this:

**Option A: Break between chains**
Insert drama at the natural gap between sofa_block and challenge.
The sofa chain (e.g., s04b–s10) stays intact.
Drama goes between s10 and s12.
The challenge chain (e.g., s12–s21) stays intact.

**Option B: Break within a chain — ONLY if the book shows a break there**
Do NOT split chains by quiz count. If the book has uninterrupted Софа-teaching
for 20 messages, gameflow keeps it as one chain. The telegram-bot metaphor
tolerates arbitrary length — player is engaged with the bot.

Split a chain only when the book explicitly has:
- Scene/location change
- Another character enters
- An emotional reaction or action beat from Марко

When the book has such a break and gameflow missed it — restore it.
When the book has no break — don't invent one.

**Preferred approach:** Option A (insert drama between natural sub-sections).
Never insert drama purely to limit chain length.

## Special Cases

### Quizzes that ARE drama
Some book quizzes are embedded in story dialogue — a character says
something, Софа comments, quiz follows naturally. Mark them — they're
both narrative flow AND quiz mechanic:

```yaml
  story_quiz: true  # this quiz is part of the narrative flow
```

### Challenge express quizzes
Challenge blocks are designed for speed — rapid-fire quizzes.
Streak length is whatever the book shows. Do NOT insert artificial
Марко-reaction breathers every N quizzes. Only add author_text_before
if the book explicitly has it at that point. When the book keeps
quizzes back-to-back without reaction, gameflow does the same.

```yaml
# Instead of separate scene, add to the quiz itself:
- scene_id: ep001_s16
  scene_type: quiz
  author_text_before: >
    Марко кивает. Быстрее. Он чувствует ритм.
  question: "«Трава зелёного цвета.» Факт или мнение?"
```

This `author_text_before` renders before the quiz in the chat, giving
a narrative breath without breaking the phone chain.
