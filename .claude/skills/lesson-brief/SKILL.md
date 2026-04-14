---
name: lesson-brief
description: |
  Creates a lesson brief: reads the YAML lesson, splits it into theory blocks,
  writes a text summary for each block to pipeline/briefs/.
  Triggers: "create lesson brief", "split lesson", "lesson brief", "brief 1A".
  Argument: lesson ID (e.g., 1A, 5B, 12A). Without argument — asks which lesson.
---

# Lesson Brief — Splitting a Lesson into Blocks for Episodes

You create a lesson brief — an intermediate document between a YAML lesson and episode plans.
The brief splits the lesson into logical blocks. Each block becomes the basis for one episode.

## Language

All instructions in this file are in English.
All generated output (briefs, summaries) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- YAML lesson: `lessons_ru/lesson_{ID}.yaml` (read-only, do not edit)
- Argument: lesson ID (1A, 1B, 2A ... 13A)

## Output

- File: `pipeline/briefs/brief_{ID}.yaml`

## Block Splitting Rule

**Unit of splitting — theory block.**

A theory block = a scene (or group of scenes) that introduces a NEW concept,
term, or tool, plus the practice that reinforces it.

### Algorithm

1. Read the YAML lesson scene by scene (only `ru` keys)
2. Every time a **new concept** appears — that starts a new block
3. Everything after (practice, examples, votes) belongs to this block
   until the next concept begins
4. Introductory scenes (warm-up, hook story) — attach to the first block
5. Closing scenes (synthesis, final check, wrap-up) — attach to the last block

### What counts as a new concept

- A new term with a definition (fact, opinion, falsehood, cause, generalization...)
- A new tool or technique (repetition stoplight, detective question, argument tree...)
- A new type/kind (type of intimidation, type of attack, type of question...)

### What does NOT count as a new concept

- Practice (votes, cases) — part of the previous block
- Review/warm-up from past lessons — attach to the first block
- A hook story without a new term — attach to the first block

### Exception: inseparable pairs

If two concepts form an inseparable pair (one without the other makes no sense),
they go into one block. Example: fact + opinion in lesson 1A — a contrastive pair
introduced together.

Sign of an inseparable pair: one concept's definition CONTAINS the other
("opinion is something that is NOT a fact").

### However many you get — that's how many it is

Do not force the block count to any specific number.
One lesson may yield 2, 3, or 4 blocks — however it goes.

## Output file format

Uses the template from `templates/brief_template.yaml`.

## Procedure

1. Read the entire YAML lesson (only ru keys)
2. List all scenes with their titles
3. Count vote steps in each scene
4. Identify where new concepts are introduced — these are block boundaries
5. Group scenes into blocks per the rules above
6. For each block, write summary and key_material
7. Write the result to `pipeline/briefs/brief_{ID}.yaml`
8. Show the user a brief summary: how many blocks, what terms in each

## Constraints

- DO NOT edit the YAML lesson (read-only)
- DO NOT invent theory not present in the YAML
- DO NOT skip practice — every vote must belong to a block
- From YAML, take ONLY ru keys
