---
name: episode-plan
description: |
  Creates a detailed episode plan for ONE day: scenes, quizzes, story beats,
  term placement. Works with grid.yaml + briefs + source.
  Triggers: "episode plan", "plan day 3", "episode-plan".
  Argument: day number (1–13) or "all" (parallel run for all days).
  Without argument — asks which day.
---

# Episode Plan — Detailed Episode Plan (Step 2)

You create a detailed episode plan for one day.
This is Pass 2 of the two-pass mapping (rough grid → detailed plan).

Grid provided: which blocks in which day, with which plot segment.
Episode Plan provides: what specifically happens in each episode — scene by scene.

## Language

All instructions in this file are in English.
All generated output (plans, quizzes, story beats) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- `pipeline/grid.yaml` — rough grid (read ONLY your day)
- Day's briefs: `pipeline/briefs/brief_{lesson_id}.yaml`
- Plot: `source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md` (read-only, ONLY source_episodes for this day)
- Style: `pipeline/style_profile.yaml` (if exists)
- Argument: day number (1–13)

## Output

- `pipeline/episodes/day_{NN}.yaml` (NN = 01..13, with leading zero)

## Algorithm

### Phase 1: Explore

1. Read your day's section from grid.yaml
2. Read briefs for all lessons of the day
3. Read from source ONLY the episodes in source_episodes
4. Note: episode count, terms (order matters!), story beats, quizzes, dramatic events

### Phase 2: Plan

For each episode, compose a plan with four parts:

**DRAMA (3–4 min):**
Plot events, characters, location, conflict, gut feeling hint,
how the lesson arises NATURALLY from the situation

**SOFA BLOCK (4–5 min):**
Term introduced, trigger from drama, quizzes (count and type),
Sofa's Rule (1–2 sentences, like a proverb, formulated AFTER quizzes),
one "real life" question

**CHALLENGE (5–6 min):**
Dramatic test where the term is applied, plot-context quizzes,
how Marko copes (considering his flaw — people-pleaser),
roles of Vera / Ray / Voice if present

**CLIFFHANGER (1–2 min):**
Twist, must-watch-next, connection to next episode

### Quiz distribution

- SOFA BLOCK: ~40% of quizzes (theory + primary practice)
- CHALLENGE: ~60% of quizzes (application in plot)
- Minimum 10, maximum 15 per episode
- If < 10 votes → add plot quizzes (marked as `added`)
- If > 15 votes → move some to extra practice (marked as `extra`)

### Term order check (CRITICAL)

A term cannot be used BEFORE it is introduced. This applies to:
- Answer options in quizzes
- Answer explanations
- Drama and sofa block text
- Sofa's Rule

**Check algorithm (mandatory BEFORE showing to author):**

1. Build cumulative terms_available per episode
2. For EACH quiz: verify options use only available terms
3. For text: technique can be shown in ACTION but NAMED only after introduction
4. If violation found: **STOP. Fix BEFORE showing to author.**

### Content correctness check (CRITICAL)

Every quiz answer must be unambiguously correct per lesson definitions.

Key rules:
- Fact = can be verified with a specific tool AND confirmed
- Opinion = CANNOT be verified (no instrument, subjective)
- Falsehood = can be verified AND NOT confirmed
- Subjective assessments (boring, beautiful, best) = ALWAYS opinion

If error found: **STOP. Fix BEFORE showing to author.**

### Show the author (STOP)

1. Table: ep / blocks / terms / quizzes / story_beat
2. Each episode plan in 3–5 lines
3. Check results: term order PASS/FAIL, content correctness PASS/FAIL
4. Questions on controversial points

**STOP. Wait for approval.**

### Phase 3: Write

After approval — write `pipeline/episodes/day_{NN}.yaml` using the template.

## Parallel run (all)

With argument `all`:
1. Read grid.yaml entirely
2. For each day — launch a subagent via Agent tool
3. Subagents work in parallel, results collected for author approval

## Constraints

- DO NOT edit source/, briefs/, grid.yaml
- DO NOT change term order from grid
- DO NOT invent plot events not in source
- DO NOT add theory not in briefs
- CAN expand story_beat with source details
- CAN redistribute quizzes between sofa block and challenge
