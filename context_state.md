# CONTEXT STATE — current project state

> Updated after each work session.
> Last updated: 2026-04-13

---

## Project Phase
Pipeline built. Steps 0–3 active. 10 episodes written (Days 1–3). Next: Day 4+.

## Source of Truth
- **Episode structure:** `pipeline/grid.yaml` (50 episodes, 70 blocks, 13 days)
- **Episode plans:** `pipeline/episodes/day_01.yaml`, `day_02.yaml`, `day_03.yaml`
- **Lesson content:** `pipeline/briefs/*.yaml` (25 briefs, 70 blocks)
- **Written episodes:** `book/ep_001..010.md`
- **OLD lesson map:** `_reference/LESSON_MAP.md` — **DEPRECATED**, describes 40-episode structure

## What's Done

### Step 0 — Lesson Briefs (COMPLETED)
- [x] Skill `/lesson-brief` — `.claude/skills/lesson-brief/SKILL.md`
- [x] All 25 briefs ready: `pipeline/briefs/brief_{1A..13A}.yaml`
- [x] Total: **70 blocks** from 25 lessons

### Step 0-QA — Validation (COMPLETED, PASS)
- [x] Skill `/qa-briefs` — `.claude/skills/qa-briefs/SKILL.md`
- [x] QA script: `tools/qa_briefs.py`
- [x] Result: 19/25 votes match exactly, 6 deltas explainable
- [x] Verdict: PASS

### Step 1 — Story Grid (COMPLETED)
- [x] Skill `/story-grid` — `.claude/skills/story-grid/SKILL.md`
- [x] `pipeline/grid.yaml` — **approved by author 2026-04-12**
- [x] 70 blocks → 50 episodes (17 merges)
- [x] 13 days: 11 days × 4 ep + 1 day × 2 ep = 50 episodes

### Step 2 — Episode Plans (Days 1–3 COMPLETED)
- [x] Skill `/episode-plan` — `.claude/skills/episode-plan/SKILL.md`
- [x] `pipeline/episodes/day_01.yaml` — APPROVED
- [x] `pipeline/episodes/day_02.yaml` — created 2026-04-13
- [x] `pipeline/episodes/day_03.yaml` — created 2026-04-13
- [ ] Days 4–13 — NOT CREATED

### Step 3 — Episode Maps (Partial)
- [x] Skill `/episode-map` — `.claude/skills/episode-map/SKILL.md`
- [x] `pipeline/mapped/ep_001.yaml`
- [x] `pipeline/mapped/ep_002.yaml`
- [x] `pipeline/mapped/ep_008.yaml` — created 2026-04-13
- [x] `pipeline/mapped/ep_009.yaml` — created 2026-04-13
- [x] `pipeline/mapped/ep_010.yaml` — created 2026-04-13
- [ ] Maps for ep_003..007 — NOT CREATED (episodes written without maps)

### Writing (10 EPISODES COMPLETED)
- [x] `book/ep_001.md` — Day 1, block 1A.1 (факт, мнение)
- [x] `book/ep_002.md` — Day 1, block 1A.2 (неправда)
- [x] `book/ep_003.md` — Day 1, blocks 1B.1+1B.2 (хитрое утверждение, отговорка, инструменты)
- [x] `book/ep_004.md` — Day 1, block 1B.3 (детектив правды)
- [x] `book/ep_005.md` — Day 2, block 2A.1 (повторяемость, закономерность, совпадение)
- [x] `book/ep_006.md` — Day 2, block 2A.2 (светофор повторений)
- [x] `book/ep_007.md` — Day 2, block 2B.1 (причина, следствие, после≠вследствие)
- [x] `book/ep_008.md` — Day 2, block 2B.2 (третья причина)
- [x] `book/ep_009.md` — Day 3, block 3A.1 (три цели спора)
- [x] `book/ep_010.md` — Day 3, block 3A.2 (солдат, разведчик)
- [ ] Episodes 11–50 — NOT WRITTEN

### Review HTML
- [x] `pipeline/review/ep_001_010_review.html` — all 10 episodes (lesson vs book side-by-side)

### Deployment
- [x] GitHub: `esoroban/SylaSlovaDramma` (full project, private)
- [x] GitHub: `esoroban/episodes` (renderer feed, 10 episodes in book/)

## Pipeline Architecture

```
lessons_ru/*.yaml ──► Step 0 (/lesson-brief) ──► Step 0-QA (/qa-briefs) ──► Step 1 (/story-grid)
                                                                              │
source/plot.md ──────────────────────────────────────────────────────────────►│
                                                                              │
                                                                              ▼
                                                                         Step 2 (/episode-plan)
                                                                              │
                                                                              ▼
                                                                         Step 3 (/episode-map)
                                                                              │
                                                                              ▼
                                                                         Step 4 (writing)
```

## Skills

| Skill | Path | Step |
|-------|------|------|
| `/lesson-brief` | `.claude/skills/lesson-brief/` | 0 |
| `/qa-briefs` | `.claude/skills/qa-briefs/` | 0-QA |
| `/story-grid` | `.claude/skills/story-grid/` | 1 |
| `/episode-plan` | `.claude/skills/episode-plan/` | 2 |
| `/qa-episodes` | `.claude/skills/qa-episodes/` | 2-QA / 3-QA |
| `/episode-map` | `.claude/skills/episode-map/` | 3 |

## Cumulative Terms by Episode

| Ep | Day | Block | New terms | Total available |
|----|-----|-------|-----------|----------------|
| 1 | 1 | 1A.1 | факт, мнение | 2 |
| 2 | 1 | 1A.2 | неправда | 3 |
| 3 | 1 | 1B.1+1B.2 | хитрое утверждение, отговорка, инструменты проверки | 6 |
| 4 | 1 | 1B.3 | детектив правды | 7 |
| 5 | 2 | 2A.1 | повторяемость, закономерность, совпадение | 10 |
| 6 | 2 | 2A.2 | светофор повторений | 11 |
| 7 | 2 | 2B.1 | причина, следствие, после — не значит вследствие | 14 |
| 8 | 2 | 2B.2 | третья причина | 15 |
| 9 | 3 | 3A.1 | три цели спора | 16 |
| 10 | 3 | 3A.2 | солдат, разведчик | 18 |

## What's Next
- [ ] Episode plans for Days 4–13
- [ ] Episode maps for remaining episodes
- [ ] Writing episodes 11–50
- [ ] QA passes on written episodes

## Known Risks
- Mapping 1A was done before grid — may need updating
- 5A: 4 blocks merged into 1 episode (5 terms) — dense episode
- Day 12 compresses 7 source episodes into 4 blocks — dense day
- `_reference/LESSON_MAP.md` is DEPRECATED — do not use for numbering
