---
name: qa-briefs
description: |
  Validates lesson briefs: compares votes in YAML vs briefs, finds blocks
  without terms, checks empty fields, returns PASS/FAIL verdict.
  Triggers: "check briefs", "qa briefs", "brief validation", "qa-briefs".
  Without arguments — checks all briefs. With argument — a specific one (e.g., qa-briefs 5A).
---

# QA Briefs — Lesson Brief Validation (Step 0-QA)

You run a quality gate on briefs before proceeding to the next pipeline step.
Without passing QA, the pipeline cannot advance to grid.

## Language

All instructions in this file are in English.
All generated output (verdicts, reports, tables) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- Briefs: `pipeline/briefs/brief_*.yaml`
- YAML lessons: `lessons_ru/lesson_*.yaml` (read-only)
- QA script: `tools/qa_briefs.py`

## Algorithm

### 1. Run the script

```bash
python3 tools/qa_briefs.py
```

The script outputs:
- Per-lesson table: votes in YAML vs votes in brief
- Blocks without terms
- Summary: total block count, global delta
- Issue list

### 2. Interpret results

**For each issue, determine the type:**

**Type A: Vote delta**
- Open the brief and the YAML
- Count manually: how many steps with type=vote and type=vote_multichoice in the YAML?
- How many discussion steps? (discussion ≠ vote, do not count)
- If the delta is explained by discussion → mark as "explained, not an error"
- If the delta is NOT explained → brief needs rework

**Type B: Block without terms**
- Open the brief, read the block
- Final practice / closing? → Acceptable (merge candidate in grid)
- Review of past lessons? → Acceptable (attached to the first block)
- Agent missed a concept? → Brief needs rework

**Type C: Empty fields**
- summary or key_material empty → brief needs rework

### 3. Verdict

**PASS** if:
- All briefs exist (25 of 25)
- No unexplained deltas (or all explained as discussion)
- No empty summary/key_material
- Blocks without terms — all acceptable (practice/closing)

**FAIL** if:
- Unexplained deltas exist (votes genuinely lost)
- Required fields are empty
- Blocks where a concept was missed

### 4. On FAIL

For each problematic brief:
- Describe the issue
- Suggest a fix (which block to revise)
- Ask the author: fix now or mark and move on?

### 5. Show the author

Output a compact table:

```
QA BRIEFS — РЕЗУЛЬТАТ
=====================
Всего брифов: 25/25
Votes: YAML=1068, брифы=1039, дельта=-29

ПРОБЛЕМЫ:
  4A:  delta=-8  → discussion-шаги, не ошибка  ✓
  3B:  delta=-8  → vote_multichoice, не ошибка  ✓
  ...

БЛОКИ БЕЗ ТЕРМИНОВ (кандидаты на объединение):
  7B.3, 9B.2, 5B.4, 10A.3, 12A.1, 12B.3

ВЕРДИКТ: PASS — можно переходить к grid
```

## Output

Does not create any file. The result is a PASS/FAIL verdict with interpreted issues.
The verdict is recorded in `pipeline/stages/stage_0_qa.md` (Status section).

## Constraints

- DO NOT edit YAML lessons (read-only)
- DO NOT edit briefs automatically — only report the issue
- Brief fixes go through `/lesson-brief` (redo a specific lesson)
