---
name: story-grid
description: |
  Creates a rough grid: distributes lesson blocks across days,
  merges small blocks, links to the plot.
  Triggers: "create grid", "story grid", "grid", "distribute blocks".
  Without arguments — works with all briefs.
---

# Story Grid — Rough Block-to-Day Grid (Step 1)

You create a grid — a map linking lesson blocks to the plot timeline.
This is Pass 1 of the two-pass mapping (rough → detailed).

## Language

All instructions in this file are in English.
All generated output (grid, tables, merge logs) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- All briefs: `pipeline/source/briefs/brief_*.yaml`
- Plot: `source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md` (read-only)
- QA passed: `tools/qa_briefs.py` was run, result — PASS
- Rules: `pipeline/docs/stages/stage_1_grid.md`

## Output

- `pipeline/source/grid.yaml`

## Algorithm

### Phase 1: Explore

1. Read ALL briefs. List: lesson / block / terms / votes
2. Read the entire plot from source. List: episode / title / act / key events
3. Mark blocks without terms (merge candidates)

### Phase 2: Plan

**Step A — Merging blocks**

For each day (1–13), for each lesson (A, B):
- Block without terms → merge with previous (same lesson)
- Two small blocks (< 5 votes each) → can merge
- Record merge_log: what was merged and why
- Count: how many episodes remain for the day?
- If > max_per_day (4) → merge more aggressively

Rules:
- CANNOT merge blocks from A and B
- CANNOT merge if combined votes > 40
- If still > 4 → show the author and ask

**Step B — Linking to plot**

For each day:
1. Determine the plot act (I–V) and key events
2. For each episode — write a story_beat (1 sentence)
3. Specify source_episodes (which source episodes this day covers)

Linking principles:
- Days 1–7 → Act I–II source (episodes 1–18)
- Days 8–11 → Act III source (episodes 19–28)
- Days 12–13 → Act IV–V source (episodes 29–40)
- Plot event order cannot be changed
- Can stretch or compress

**Step C — Show the author**

Output:
1. Table: day / episodes / blocks / plot (compact)
2. List of merges with justification
3. Days still > 4 episodes
4. Specific questions on controversial points

**STOP. Wait for approval.**

### Phase 3: Write

After approval — write `pipeline/source/grid.yaml` using the template.

## Constraints

- DO NOT edit source/ or briefs/
- DO NOT change lesson order (day 1 < day 2, A < B)
- DO NOT invent plot events not in source
- CAN change distribution of source events across days
