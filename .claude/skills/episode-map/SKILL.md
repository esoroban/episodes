---
name: episode-map
description: |
  Transplants generic quizzes and theory from briefs into the episode's plot context.
  Works with episode plan + briefs + source. Output — a mapped episode ready for writing.
  Triggers: "transplant episode", "episode map", "episode mapping 1".
  Argument: episode number (1–50) or "day N" (all episodes of a day).
  Without argument — asks which episode.
---

# Episode Map — Transplanting Quizzes and Theory into the Plot (Step 3)

You transplant lesson content (generic examples, quizzes, theory) into the specific
plot context of an episode. Input — abstract lesson + episode structure.
Output — episode with quizzes and theory tied to the plot, ready for writing.

## Language

All instructions in this file are in English.
All generated output (mapped episodes, quizzes, theory) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## How it differs from lesson-map

| | lesson-map | episode-map (this one) |
|---|---|---|
| Unit | Entire lesson (1A) | One episode (ep.1) |
| Context | General source plot | Specific drama from episode plan |
| Quizzes | Warmup/middle/finale | Sofa block / challenge |
| Knows | Which lesson | Which scene, who's in it, what conflict |

## Input

- Episode plan: `pipeline/episodes/day_{NN}.yaml` (specific episode)
- Lesson brief: `pipeline/briefs/brief_{ID}.yaml` (for this episode's blocks)
- YAML lesson: `lessons_ru/lesson_{ID}.yaml` (read-only, only ru keys)
- Plot: `source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md` (read-only)
- Grid: `pipeline/grid.yaml` (terms, story_beat)
- Style: `pipeline/style_profile.yaml`

## Output

- `pipeline/mapped/ep_{NNN}.yaml` (NNN = 001..050, with leading zeros)

## Algorithm

### Phase 1: Explore

1. Read the episode from episode plan (drama, sofa_block, challenge, cliffhanger)
2. Read this episode's blocks from the brief
3. Read original quiz texts from the YAML lesson (ru keys)
4. Read source episodes for scene context
5. Note: all generic quizzes, stories, drama context, terms_available (cumulative)

### Phase 2: Plan

For each quiz, decide: **keep generic or transplant into the plot**.

**Sofa block (theory + primary practice, ~40% of quizzes):**
- How Sofa introduces the term through a scene moment
- First 2–3 quizzes: can be generic (warmup)
- Rest: transplant into current scene context
- Wordings tied to what Marko SEES and HEARS

**Challenge (application in plot, ~60% of quizzes):**
- ALL plot-based — tied to character actions
- Use character names, plot situations
- Provocative: tied to cliffhanger or inter-episode intrigue

**Character replacement:**
- Generic children → plot characters, matched by role
- Do not overload one character
- Antagonists (Ray, Voice) — only if in this episode
- Vera — "benign" context; Lina — don't reveal early; Max — honest roles

**Checks (CRITICAL, before showing to author):**

1. **Term order:** quizzes use ONLY terms_available (cumulative)
2. **Answer correctness:** every answer unambiguous per lesson definitions
3. **Spoiler check:** plot quizzes don't spoil future twists

**Show the author:**
1. Table: quiz / type / original → mapping / answer
2. How Sofa introduces each term
3. Controversial replacements + questions

**STOP. Wait for approval.**

### Phase 3: Write

After approval — write `pipeline/mapped/ep_{NNN}.yaml` using the template.

## Parallel run

With argument `day N`:
- Episodes within a day are sequential (terms_available is cumulative)
- Days are independent — can parallelize across days

## Constraints

- DO NOT edit source/, briefs/, YAML lessons, episode plans
- DO NOT change episode structure (drama/sofa/challenge/cliffhanger)
- DO NOT change term definitions or theory
- DO NOT invent plot events not in source
- CAN change quiz wordings (generic → plot-based)
- CAN change quiz order within sofa block and challenge
- CAN add plot quizzes (mark type: added)
