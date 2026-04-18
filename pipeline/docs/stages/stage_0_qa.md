# Step 0-QA — Brief Validation

Automatic quality check of briefs before moving on to the grid.
Runs after all briefs are created (step 0).

## Script

`tools/qa_briefs.py`

## What it checks

### 1. Vote completeness
Counts vote steps in the YAML lesson and compares with the total votes in the brief.
- Delta 0 = perfect
- Delta < 0 = votes lost (or difference in vote/discussion definition)
- Delta > 0 = votes invented (agent error)

### 2. Blocks without terms
A block with `terms_introduced: []` is suspicious.
Acceptable cases:
- Final practice / lesson closing (should be merged at the grid step)
- Pure review of past lessons (attached to the first block)
Unacceptable:
- A block where the agent simply missed a new concept

### 3. Empty fields
Every block must have: summary, key_material, practice_summary.

## Pass criteria

- All 25 briefs exist
- Global vote delta ≤ 5% of total count
- No blocks with votes > 0 and empty summary
- Blocks without terms — flagged as merge candidates

## When to run

- After creating / updating any brief
- Before moving to step 1 (story-grid)

## Status

- [x] First run — 2026-04-12
  - 19/25 briefs: votes match
  - 6 deltas (total -29 votes) — difference in discussion counting
  - 6 blocks without terms — merge candidates
  - Verdict: **PASS** — can proceed to grid
