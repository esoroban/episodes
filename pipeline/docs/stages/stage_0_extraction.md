# Step 0 — Lesson Briefs

Horizontal pass, all 25 lessons. Each lesson is split into logical blocks.
Each block will become the basis for one episode.

## Input
- `lessons_ru/*.yaml` — only `ru` keys are used

## What we do
For each lesson, we create a **lesson brief** — an intermediate document between the YAML and episode briefs.

Skill: `.claude/skills/lesson-brief.md`
Invocation: `/lesson-brief {ID}` (e.g. `/lesson-brief 1A`)

## Splitting rule

The unit of splitting is a **theory block**: a scene (or group of scenes) that introduces a new concept/term/tool, plus the practice that reinforces it.

- New concept = start of a new block
- Practice after theory = part of the same block
- Introductory scenes → go to the first block
- Closing scenes → go to the last block
- Inseparable pairs (fact + opinion) → one block

Detailed rules are in the skill.

## Output
- `pipeline/source/briefs/brief_{ID}.yaml` — lesson brief with blocks

## Status
- [x] brief_1A.yaml — done (2 blocks)
- [ ] remaining 24 lessons
