---
name: lesson-map
description: |
  Maps a lesson to the plot: transplants generic examples into Marko's world.
  Replaces characters, adapts stories, creates plot quizzes.
  Triggers: "lesson mapping", "transplant lesson", "lesson map", "mapping 1A".
  Argument: lesson ID (e.g., 1A, 5B, 12A). Without argument — asks which lesson.
---

# Lesson Map — Lesson-to-Plot Mapping (Step 0.5)

You create a lesson mapping — a document that transplants generic examples
from a YAML lesson into Marko's world. This is an intermediate layer between
the lesson brief (step 0) and the episode plan (step 1).

## Language

All instructions in this file are in English.
All generated output (mappings, quizzes, stories) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- Lesson brief: `pipeline/source/briefs/brief_{ID}.yaml` (required, must exist)
- YAML lesson: `lessons_ru/lesson_{ID}.yaml` (read-only, only ru keys)
- Plot: `source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md` (read-only)
- Rules: `pipeline/docs/stages/stage_05_mapping.md`
- Argument: lesson ID (1A, 1B, 2A ... 13A)

## Output

- File: `pipeline/work/mappings/mapping_{ID}.yaml`

## Algorithm

### Phase 1: Explore (do not write the mapping yet)

1. Read the lesson brief (`brief_{ID}.yaml`)
2. Read the entire YAML lesson (only ru keys)
3. Read the relevant source episodes linked to this lesson
4. List all generic characters from the lesson
5. List all stories/examples
6. List all vote steps with text and options

### Phase 2: Plan (show the author)

For each block from the brief, compose a plan:

**Character replacement:**
- Each generic character → a specific character of ours (or unnamed classmate)
- Justification for the choice

**Stories:**
- Each story → action: keep / adapt / replace
- If adapt/replace — how exactly

**Quizzes (most important):**
- Split all vote steps into three groups: warmup / middle / finale
- For each quiz: keep generic or replace with plot-based?
- For plot-based: propose specific wording
- The majority of quizzes should be plot-based

**Questions for the author:**
- Character replacements: "Dmytryk → [who]? Because [why]. OK?"
- Controversial quizzes: "Does this quiz spoil [what]?"
- Balance: "In block X: Y generic, Z plot-based. Acceptable?"

**STOP. Wait for author approval.**

### Phase 3: Write (after approval)

Write the mapping to `pipeline/work/mappings/mapping_{ID}.yaml` using the template.

## Three mapping principles

### 1. Transplantation, not reinvention
Preserve lesson examples as close to the original as possible.
Change content only if it genuinely doesn't fit.

### 2. Character replacement
Generic children → our characters, matched by personality.
Do not overload one character in a single lesson.

### 3. Plot quizzes — the majority
- **Warmup (first 2–3):** simple generic, as in the lesson
- **Middle (4–6):** from Marko's school life, familiar characters
- **Finale (3–5):** provocative, from the main plot, open-ended questions

## Rules for plot quizzes

- Do not spoil plot twists
- Do not break characters (don't reveal roles before the plot does)
- Open questions are more valuable than closed ones
- Cumulative terms only — only already-introduced terms

## Rules for characters

- Do not overload one character in a single lesson
- Main antagonists (Ray, Voice) — only in finale quizzes
- Vera — acceptable in a "benign" context (child still trusts her)
- Lina — carefully, don't present as unreliable too early
- Max — ideal for simple, honest roles
- Unnamed classmates — for incidental roles

## Constraints

- DO NOT edit YAML lessons or source (read-only)
- DO NOT invent stories not present in the lesson or source
- DO NOT change theory, definitions, or conclusions
- DO NOT create a mapping without a brief (first run `/lesson-brief`)
- From YAML, take ONLY ru keys
