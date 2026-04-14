# CONTEXT STATE — current project state

> Updated after each work session.
> Last updated: 2026-04-14

---

## Project Phase
Pipeline built. Steps 0–4 active. 20 episodes written (Days 1–5). Next: Day 6+.

## Source of Truth
- **Episode structure:** `pipeline/grid.yaml` (50 episodes, 70 blocks, 13 days)
- **Episode plans:** `pipeline/episodes/day_01.yaml` through `day_05.yaml`
- **Lesson content:** `pipeline/briefs/*.yaml` (25 briefs, 70 blocks)
- **Written episodes:** `book/ep_001..020.md`
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

### Step 2 — Episode Plans (Days 1–5 COMPLETED)
- [x] Skill `/episode-plan` — `.claude/skills/episode-plan/SKILL.md`
- [x] `pipeline/episodes/day_01.yaml` — APPROVED
- [x] `pipeline/episodes/day_02.yaml` — created 2026-04-13
- [x] `pipeline/episodes/day_03.yaml` — created 2026-04-13
- [x] `pipeline/episodes/day_04.yaml` — completed 2026-04-14 (ep_013–016)
- [x] `pipeline/episodes/day_05.yaml` — created 2026-04-14 (ep_017–020)
- [ ] Days 6–13 — NOT CREATED

### Step 3 — Episode Maps (Days 1–5 partial)
- [x] Skill `/episode-map` — `.claude/skills/episode-map/SKILL.md`
- [x] `pipeline/mapped/ep_001.yaml`
- [x] `pipeline/mapped/ep_002.yaml`
- [x] `pipeline/mapped/ep_008.yaml` — created 2026-04-13
- [x] `pipeline/mapped/ep_009.yaml` — created 2026-04-13
- [x] `pipeline/mapped/ep_010.yaml` — created 2026-04-13
- [x] `pipeline/mapped/ep_011.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_012.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_013.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_014.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_015.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_016.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_017.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_018.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_019.yaml` — created 2026-04-14
- [x] `pipeline/mapped/ep_020.yaml` — created 2026-04-14
- [ ] Maps for ep_003..007 — NOT CREATED (episodes written without maps)

### Writing (20 EPISODES COMPLETED)
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
- [x] `book/ep_011.md` — Day 3, block 3B.1+3B.2 (эмпатия, активное слушание)
- [x] `book/ep_012.md` — Day 3, block 3B.3 (формула высказывания)
- [x] `book/ep_013.md` — Day 4, block 4A.1 (невербальная коммуникация, ГЛАЗ)
- [x] `book/ep_014.md` — Day 4, blocks 4A.2+4A.3+4A.4 (зрительный контакт, поза, жесты, мимика, интонация, сарказм)
- [x] `book/ep_015.md` — Day 4, block 4B.1 (доверие/Этос, чувства/Пафос, доказательства/Логос)
- [x] `book/ep_016.md` — Day 4, block 4B.2 (баланс способов)
- [x] `book/ep_017.md` — Day 5, blocks 5A.1–5A.4 (своими глазами, услышал, три вопроса, уровни интернета, дипфейк)
- [x] `book/ep_018.md` — Day 5, blocks 5A.5+5A.6 (правило двух источников, один думает vs много проверили)
- [x] `book/ep_019.md` — Day 5, blocks 5B.1+5B.2 (центральная идея, дерево спора, ствол, ветка, листок, формула сути)
- [x] `book/ep_020.md` — Day 5, blocks 5B.3+5B.4 (независимые/зависимые источники)
- [ ] Episodes 21–50 — NOT WRITTEN

### Review HTML
- [x] `pipeline/review/ep_001_010_review.html` — first 10 episodes (lesson vs book side-by-side)

### Deployment
- [x] GitHub: `esoroban/SylaSlovaDramma` (full project, private)
- [x] GitHub: `esoroban/episodes` (renderer feed, episodes in book/)

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
| 11 | 3 | 3B.1+3B.2 | эмпатия (сопереживание), активное слушание | 20 |
| 12 | 3 | 3B.3 | формула высказывания | 21 |
| 13 | 4 | 4A.1 | невербальная коммуникация, ГЛАЗ | 23 |
| 14 | 4 | 4A.2+4A.3+4A.4 | зрительный контакт, открытая поза, закрытая поза, жесты, мимика, интонация, сарказм | 30 |
| 15 | 4 | 4B.1 | доверие (Этос), чувства (Пафос), доказательства (Логос) | 33 |
| 16 | 4 | 4B.2 | баланс способов | 34 |
| 17 | 5 | 5A.1–5A.4 | своими глазами, услышал от других, три вопроса для проверки, уровни интернета, дипфейк | 39 |
| 18 | 5 | 5A.5+5A.6 | правило двух источников, один человек думает vs много людей проверили | 41 |
| 19 | 5 | 5B.1+5B.2 | центральная идея, дерево спора, ствол, ветка (аргумент), листок (деталь), формула сути | 47 |
| 20 | 5 | 5B.3+5B.4 | независимые источники, зависимые источники | 49 |

## What's Next
- [ ] Episode plans for Days 6–13
- [ ] Episode maps for remaining episodes
- [ ] Writing episodes 21–50
- [ ] QA passes on written episodes
- [ ] Maps for ep_003..007 (retroactive, low priority)

## Known Risks
- Mapping 1A was done before grid — may need updating
- Day 12 compresses 7 source episodes into 4 blocks — dense day
- `_reference/LESSON_MAP.md` is DEPRECATED — do not use for numbering

## Key Story Milestones Reached
- Day 1: Исчезновение Софии, Софа включается, Лина помнит
- Day 2: Вход в Зеркальный Город, Леон, числа
- Day 3: Ссора с Линой, Макс, СТИРАНИЕ ЛЕОНА, Вера вытягивает информацию
- Day 4: Зеркало-портал к маме, Рекламная улица, Рей-пленник, два плаката Софии, подполье
- Day 5: Сопротивление Софии, дерево связей → Вера, МИДСЕЗОННАЯ БОМБА (мама выбрала), запись Софии
