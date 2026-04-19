# CONTEXT STATE — current project state

> Updated after each work session.
> Last updated: 2026-04-19

---

## Project Phase
**Gameflow + day-by-day freeze.** Work mode: close each day fully (RU → proofread → freeze → UK), then move on (see `project_day_by_day_localization` memory).

- **Day 1 (ep_001–004, lessons 1A + 1B): FROZEN 2026-04-19.**
  Git tag: `day-01-frozen` @ commit `8888c05`.
  Author read-through complete. RU content locked; do not edit without explicit request.
- Days 2–13 gameflow: NOT STARTED
- UK translation layer for Day 1: NOT STARTED (next step after tooling)
- HTML renderer, validator, artifact audit: DONE

### New Layer: Gameflow
- `pipeline/gameflow/spec/` — schema, branching rules, visual briefs, pipeline rules
- `pipeline/gameflow/episodes/ep_001..004.yaml` — 47 scenes, 4 flavor detours, 6 soft fails
- `tools/build_game.py` — gameflow YAML → interactive HTML
- `tools/validate_gameflow.py` — catches duplicate keys, broken links, unused flags
- `publish/game/` — generated HTML (dark theme, scene-by-scene navigation)

### Previous Phase (COMPLETED)
Pipeline built. Steps 0–4 completed. 50 episodes written (Days 1–13).

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
- [x] `pipeline/episodes/day_06.yaml` — created 2026-04-14 (ep_021–024)
- [x] `pipeline/episodes/day_07.yaml` — created 2026-04-14 (ep_025–028)
- [x] `pipeline/episodes/day_08.yaml` — created 2026-04-14 (ep_029–032) APPROVED
- [x] `pipeline/episodes/day_09.yaml` — created 2026-04-14 (ep_033–036) APPROVED
- [x] `pipeline/episodes/day_10.yaml` — created 2026-04-14 (ep_037–040) APPROVED
- [ ] Days 11–13 — NOT CREATED

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
- [x] `pipeline/mapped/ep_021.yaml` through `ep_028.yaml` — created 2026-04-14
- [ ] Maps for ep_003..007 — NOT CREATED (episodes written without maps)

### Writing (40 EPISODES COMPLETED)
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
- [x] `book/ep_021.md` — Day 6, blocks 6A.1+6A.2 (уклонение/поворотник, смена темы/тональности, ответ на другой)
- [x] `book/ep_022.md` — Day 6, blocks 6A.3+6A.4 (вопрос-детектор, волшебная фраза)
- [x] `book/ep_023.md` — Day 6, block 6B.1 (обобщение — ловушка слов)
- [x] `book/ep_024.md` — Day 6, blocks 6B.2+6B.3 (подмена понятий, закон тождества, контр-ход)
- [x] `book/ep_025.md` — Day 7, block 7A.1 (противоречие, закон непротиворечия)
- [x] `book/ep_026.md` — Day 7, block 7A.2 (корректное напоминание)
- [x] `book/ep_027.md` — Day 7, block 7B.1 (обоснование, три типа обоснования)
- [x] `book/ep_028.md` — Day 7, blocks 7B.2+7B.3 (нападение на человека, три вида, защита)
- [x] `book/ep_029.md` — Day 8, block 8A.1 (пугало, преувеличение, упрощение, добавление, изменение смысла)
- [x] `book/ep_030.md` — Day 8, blocks 8A.2+8A.3 (уточнение/формула защиты, честный пересказ)
- [x] `book/ep_031.md` — Day 8, blocks 8B.1+8B.2 (манипуляция страхом, четыре вида, три вопроса-фильтра)
- [x] `book/ep_032.md` — Day 8, block 8B.3 (четыре шага защиты от запугивания)
- [x] `book/ep_033.md` — Day 9, block 9A.1 (страшная цепочка)
- [x] `book/ep_034.md` — Day 9, block 9A.2 (три рентгеновских вопроса)
- [x] `book/ep_035.md` — Day 9, block 9B.1 (авторитет, компетентность, ложный авторитет)
- [x] `book/ep_036.md` — Day 9, block 9B.2 (практика: Лина — агент Софии)
- [x] `book/ep_037.md` — Day 10, block 10A.1 (ложная дилемма, закон исключённого третьего)
- [x] `book/ep_038.md` — Day 10, blocks 10A.2+10A.3 (выбор без выбора)
- [x] `book/ep_039.md` — Day 10, blocks 10B.1+10B.2 (составной вопрос, вопрос-ловушка)
- [x] `book/ep_040.md` — Day 10, block 10B.3 (риторический вопрос)
- [ ] Episodes 41–50 — NOT WRITTEN

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
| 21 | 6 | 6A.1+6A.2 | уклонение от ответа (поворотник), смена темы, смена тональности, ответ на другой вопрос | 53 |
| 22 | 6 | 6A.3+6A.4 | вопрос-детектор, волшебная фраза (возврат к вопросу) | 55 |
| 23 | 6 | 6B.1 | обобщение (ловушка слов) | 56 |
| 24 | 6 | 6B.2+6B.3 | подмена понятий, закон тождества, контр-ход | 59 |
| 25 | 7 | 7A.1 | противоречие, закон непротиворечия | 61 |
| 26 | 7 | 7A.2 | корректное напоминание | 62 |
| 27 | 7 | 7B.1 | обоснование, три типа обоснования | 64 |
| 28 | 7 | 7B.2+7B.3 | нападение на человека, три вида нападения, защита от нападения | 67 |
| 29 | 8 | 8A.1 | пугало (искажение слов), преувеличение, упрощение, добавление, изменение смысла | 72 |
| 30 | 8 | 8A.2+8A.3 | уточнение (формула защиты), честный пересказ | 74 |
| 31 | 8 | 8B.1+8B.2 | манипуляция страхом, четыре вида запугивания, три вопроса-фильтра | 77 |
| 32 | 8 | 8B.3 | четыре шага защиты от запугивания | 78 |
| 33 | 9 | 9A.1 | страшная цепочка | 79 |
| 34 | 9 | 9A.2 | три рентгеновских вопроса | 80 |
| 35 | 9 | 9B.1 | авторитет, компетентность, ложный авторитет | 83 |
| 36 | 9 | 9B.2 | (практика, нет новых) | 83 |
| 37 | 10 | 10A.1 | ложная дилемма, закон исключённого третьего | 85 |
| 38 | 10 | 10A.2+10A.3 | выбор без выбора | 86 |
| 39 | 10 | 10B.1+10B.2 | составной вопрос, вопрос-ловушка | 88 |
| 40 | 10 | 10B.3 | риторический вопрос (вопрос-утверждение) | 89 |

## What's Next
- [ ] Episode plans for Days 11–13
- [ ] Episode maps for remaining episodes
- [ ] Writing episodes 41–50
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
- Day 6: 72 часа Макса, речи Рея, Софиины записи, агенты стирают словами, СТИРАНИЕ МАКСА
- Day 7: Марко один, Сем (новый союзник), файл Веры (20 лет), ГОЛОС — ОТЕЦ ВЕРЫ
- Day 8: Радио Рея (пугало), правда как оружие, четыре кнопки страха, МАМА ИСЧЕЗЛА (ушла добровольно)
- Day 9: План вернуть Макса, три нитки Лины, ВЕЛИКОЕ ПРЕДАТЕЛЬСТВО, шрам «С» — Лина агент Софии, число 30
- Day 10: Ультиматум Рея (ложная дилемма), сломать артефакты? НЕ СМЕЙ!, стеклянная комната (София — правый глаз серый), башня Голоса, число 20
