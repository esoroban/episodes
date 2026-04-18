# Step 1 — Story Grid (rough grid)

Two-pass mapping of lesson blocks to the plot.
Pass 1: rough grid (this step).
Pass 2: detailed episode plans (step 2).

## Why

Between lesson briefs (70 blocks) and the plot (40 episodes in source) there is no
correspondence. The grid creates this correspondence: which blocks go into which day,
with which piece of the plot, which blocks are merged.

## Input

- `pipeline/source/briefs/*.yaml` — all briefs (after QA)
- `source/` — plot (read-only)
- Parameter: max_per_day (episode limit per day, default 4)

## Output

- `pipeline/source/grid.yaml` — rough grid

## Skill

`.claude/skills/story-grid.md`
Invocation: `/story-grid` (no arguments — works with all briefs)

## What the grid does

### 1. Merges small blocks

Blocks without new terms (pure practice) → merged with the neighboring block
from the same lesson. This reduces 70 blocks to ~55-60.

Merge rules:
- Block with terms_introduced: [] → merge with previous
- Two blocks with < 5 votes each → can be merged
- CANNOT merge blocks from different lessons (A and B)
- CANNOT merge blocks if combined votes > 30

### 2. Distributes by day

Each day = one YAML day (1A+1B, 2A+2B, ..., 13A).
If blocks > max_per_day → merge more aggressively.
If blocks < max_per_day → keep as is.

### 3. Links to the plot

For each day → determine:
- Which act of the plot (from source)
- What key events occur
- What story_beat for each episode

The plot from source is a guide, not law. The grid can:
- Stretch one source episode into multiple grid episodes
- Compress multiple source episodes into one (if there are few lessons)
- Reorder events within an act

## grid.yaml format

```yaml
# STORY GRID
# Rough grid: lesson blocks → days → plot
# Generated based on briefs/*.yaml + source/

max_per_day: 4
total_blocks_raw: 70
total_blocks_merged: 52  # after merges
total_episodes: 52

days:

  - day: 1
    lessons: ["1A", "1B"]
    story_arc: "Act I: Awakening"
    story_summary: "Sofia's disappearance, mom doesn't remember, Sofa"
    source_episodes: [1, 2]  # which source episodes this day covers
    episodes:
      - ep: 1
        blocks: ["1A.1"]
        story_beat: "Morning without a sister"
        terms: ["fact", "opinion"]
        votes: 15
      - ep: 2
        blocks: ["1A.2"]
        story_beat: "Falsehood and its types"
        terms: ["falsehood"]
        votes: 34
      - ep: 3
        blocks: ["1B.1"]
        story_beat: "Tricky statements"
        terms: ["tricky statement", "excuse"]
        votes: 16
      - ep: 4
        blocks: ["1B.2", "1B.3"]  # merged
        story_beat: "Five verification tools + truth detective"
        terms: ["verification tools", "truth detective"]
        votes: 76
        merge_rationale: "1B.3 — pure practice without a new concept"

merge_log:
  - merged: ["1B.2", "1B.3"]
    reason: "1B.3 has no new terms, 76 votes acceptable (final training)"
  - merged: ["7B.2", "7B.3"]
    reason: "7B.3 has no new terms, pure practice for the day"
```

## Validation

After creating the grid — show it to the author:
1. Full table: day / episodes / blocks / plot
2. List of merges with rationale
3. Questions:
   - Are the merges logical?
   - Are the story beats in the correct order?
   - Are there days that need more/fewer episodes?

## Status

- [x] grid.yaml — CREATED, approved 2026-04-12 (70 → 50 blocks, 17 merges)
