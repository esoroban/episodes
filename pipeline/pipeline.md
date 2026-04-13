# Pipeline — Lessons + Plot → Book

Universal pipeline: takes a set of YAML lessons + a plot and creates
an educational drama with episodes. Works with any plot.

## Steps

| Step | What we do | Skill | Stage | Output |
|------|-----------|-------|-------|--------|
| 0 — Lesson Briefs | Splitting YAML into blocks | `/lesson-brief` | `stage_0_extraction.md` | `briefs/*.yaml` |
| 0-QA — Validation | Brief quality check | `/qa-briefs` | `stage_0_qa.md` | stdout |
| 1 — Story Grid | Rough grid: blocks → days → plot | `/story-grid` | `stage_1_grid.md` | `grid.yaml` |
| 2 — Episode Plan | Detailed episode plans (by day, in parallel) | `/episode-plan` | `stage_2_episode_plan.md` | `episodes/day_NN.yaml` |
| 2-QA — Validation | Episode plan quality check | `/qa-episodes plan` | `stage_2_qa_episodes.md` | stdout (PASS/FAIL) |
| 3 — Episode Map | Transplanting quizzes and theory into episode context | `/episode-map` | `stage_3_episode_map.md` | `mapped/ep_NNN.yaml` |
| 3-QA — Validation | Episode map quality check | `/qa-episodes map` | `stage_2_qa_episodes.md` | stdout (PASS/FAIL) |
| 4 — Writing | Writing episode prose | (future) | `stage_4_writing.md` | `book/*.md` |

## Order and Dependencies

```
lessons_ru/*.yaml ──► Step 0 (brief) ──► Step 0-QA ──► Step 1 (grid)
                                                          │
source/plot.md ──────────────────────────────────────────►│
                                                          │
                                                          ▼
                                                     Step 2 (episode-plan)
                                                          │
                                                     Gate: qa-episodes plan
                                                          │
                                                          ▼
                                                     Step 3 (episode-map)
                                                          │
                                                     Gate: qa-episodes map
                                                          │
                                                          ▼
                                                     Step 4 (writing)
```

## Principles

- **Explore → Plan → Write** at every step
- **Author approves** before moving to the next step
- **QA validation** after every bulk step
- **Parallelization**: steps 0, 2, 3 are executed in parallel across lessons/days
- **Step 1 (grid)** — the only sequential step: requires the full picture
