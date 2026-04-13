# CONTEXT STATE — current project state

> Updated after each work session.
> Last updated: 2026-04-12

---

## Project Phase
Pipeline built. Steps 0, 0-QA, and 1 completed. Next step: Episode Plan (step 2).

## What's Done
- [x] Folder structure (English lowercase names)
- [x] CLAUDE.md — core (philosophy, characters, prohibitions)
- [x] vision_lock.md — world DNA
- [x] pipeline/pipeline.md — current pipeline (6 steps)
- [x] source/ — original (read-only)
- [x] lessons_ru/ — 25 YAML lessons (read-only)

### Step 0 — Lesson Briefs (COMPLETED)
- [x] Skill `/lesson-brief` — `.claude/skills/lesson-brief/SKILL.md`
- [x] All 25 briefs ready: `pipeline/briefs/brief_{1A..13A}.yaml`
- [x] Total: **70 blocks** from 25 lessons

### Step 0-QA — Validation (COMPLETED, PASS)
- [x] Skill `/qa-briefs` — `.claude/skills/qa-briefs/SKILL.md`
- [x] QA script: `tools/qa_briefs.py`
- [x] Result: 19/25 votes match exactly, 6 deltas are explainable (discussion vs vote)
- [x] 6 blocks without terms — candidates for merging in grid
- [x] Verdict: PASS

### Step 0.5 — Mapping (pilot done, moved to step 3)
- [x] Skill `/lesson-map` — `.claude/skills/lesson-map/SKILL.md`
- [x] Pilot: `pipeline/mappings/mapping_1A.yaml` (done before grid, may need updating)
- Mapping is now done AFTER episode-plan (step 3), not before grid

### Step 1 — Story Grid (COMPLETED)
- [x] Skill `/story-grid` — `.claude/skills/story-grid/SKILL.md`
- [x] Stage: `pipeline/stages/stage_1_grid.md`
- [x] `pipeline/grid.yaml` — **CREATED, approved by author 2026-04-12**
- [x] 70 blocks → 50 episodes (17 merges)
- [x] 13 days: 11 days x 4 ep + 1 day x 2 ep = 50 episodes

## Blocks by Day (from QA)

| Day | A | B | Total | Limit 4 |
|-----|---|---|-------|---------|
| 1 | 2 | 3 | 5 | +1 |
| 2 | 2 | 2 | 4 | ok |
| 3 | 2 | 3 | 5 | +1 |
| 4 | 4 | 2 | 6 | +2 |
| 5 | 6 | 4 | 10 | +6 |
| 6 | 4 | 3 | 7 | +3 |
| 7 | 2 | 3 | 5 | +1 |
| 8 | 3 | 3 | 6 | +2 |
| 9 | 2 | 2 | 4 | ok |
| 10 | 3 | 3 | 6 | +2 |
| 11 | 2 | 2 | 4 | ok |
| 12 | 3 | 3 | 6 | +2 |
| 13 | 2 | — | 2 | -2 |
| **TOTAL** | 37 | 33 | **70** | +18 over limit of 52 |

## What's Not Started
- [ ] Skill `/episode-plan` — detailed episode plans (created after grid) — **NEXT STEP**
- [ ] Chapter rewriting
- [ ] episodes/ — working copy of the plot
- [ ] book/ — finished chapters

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
                                                                         Step 3 (/lesson-map)
                                                                              │
                                                                              ▼
                                                                         Step 4 (writing)
```

## Skills (all in folder format with SKILL.md + templates/ + references/)

| Skill | Path | Step |
|-------|------|------|
| `/lesson-brief` | `.claude/skills/lesson-brief/` | 0 |
| `/qa-briefs` | `.claude/skills/qa-briefs/` | 0-QA |
| `/story-grid` | `.claude/skills/story-grid/` | 1 |
| `/episode-plan` | `.claude/skills/episode-plan/` | 2 |
| `/qa-episodes` | `.claude/skills/qa-episodes/` | 2-QA / 3-QA |
| `/episode-map` | `.claude/skills/episode-map/` | 3 |
| `/lesson-map` | `.claude/skills/lesson-map/` | (устарел, заменён episode-map) |

### Step 2 — Episode Plan (IN PROGRESS)
- [x] Skill `/episode-plan` — `.claude/skills/episode-plan/SKILL.md`
- [x] Stage: `pipeline/stages/stage_2_episode_plan.md`
- [x] Template: `.claude/skills/episode-plan/templates/day_template.yaml`
- [x] Pilot: `pipeline/episodes/day_01.yaml` — APPROVED
- [x] Two critical checks added to the skill (term order + content correctness)
- [ ] **Days 2–13 — NOT CREATED**
- Launch: `/episode-plan all` → 13 sub-agents in parallel

### Writing (IN PROGRESS)
- [x] Pilot: `book/ep_001.md` — APPROVED by author
- [x] Review HTML: `pipeline/review/ep_001_review.html`
- [x] Prompt for ep.2-7: `pipeline/prompts/write_ep_002_007.md`
- [ ] **Episodes 2–7 — NOT WRITTEN**
- [ ] Episodes 8–50 — NOT WRITTEN

## Open Questions
- Literary style — defined in `pipeline/style_profile.yaml`

## Known Risks
- Mapping 1A was done before grid — may need updating
- 5A: 4 blocks merged into 1 episode (5 terms) — dense episode
- 6B.2+6B.3: 35v — borderline merge (approved)
- Day 12 compresses 7 source episodes into 4 blocks — dense day
- Old stages (stage_1_episode_planning.md, stage_2_writing.md, stage_3_scaling.md) are outdated
