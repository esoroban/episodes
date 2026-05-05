# POWER OF WORDS — Drama + Lessons → Game

## What This Is
An interactive educational drama for children ages 8–12. 25 critical thinking lessons woven into a fantasy thriller. This is a COURSE, not a show. 60% lesson, 40% drama. The number of episodes is determined by the lessons — as many as needed to fully cover all topics.

## Current Phase
**Gameflow.** Episodes are written (50 episodes, Days 1–13). We are now building the game scene-flow layer and generating playable HTML from it. See "Gameflow Pipeline" section below.

## Philosophy
The existing story is the foundation. The plot (Sofia's disappearance, the Mirror City, the Voice) is already good and is not being rewritten from scratch. We make two improvements on top:
1. **Style** — rewrite the prose according to the profile in `pipeline/docs/style_profile.yaml` (school-mystery + detective clue chain, close Marko focalization)
2. **Lessons** — weave them in deeper so that each episode develops the lesson's topic and the lesson cannot be removed without breaking the plot

## Language
Working language: Russian. Ukrainian — only at the final localization stage.

**NAME RULE (MUST NOT be violated):**
- In Russian texts — names in CYRILLIC: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос
- In English texts — names in LATIN: Marko, Sofia, Sofa, Lina, Max, Ray, Leon, Vera, Sam, Voice
- Ukrainian letters (і, ї, є, ґ) and Ukrainian name spellings are forbidden in Russian text. Russian orthography only: Вера Андреевна, not Віра Андріївна

**SIMPLE LANGUAGE RULE (audience 8–12 years old).** All player-facing text
(`dialogue.line`, `intro`, `hint`, `closing`, `feedback_*`, `correct_logic`,
`author_text*`, `question`, `option.text`, `option.fb`, `mood`,
`visual_brief.atmosphere`) must be readable by a 4th-grader without
explanation. **No Latin/Greek terms** like *ad hominem*, *tu quoque*,
*praeteritio*, *ad populum*, *post hoc*, *false dichotomy*. Whitelist
(introduced in lessons): *этос*, *пафос*, *логос*, *демагогия*, *риторика*.
For full rule + список запрещённых слов с заменами: see
[pipeline/docs/rules/content_rules.md → Простой язык](pipeline/docs/rules/content_rules.md).
YAML comments (`#`) and dev-only fields are exempt — there latinisms are OK.

## Characters
| Character | Role |
|-----------|------|
| Marko | Protagonist, 11 years old. Weakness: agrees with whoever spoke last |
| Sofia | Missing twin sister, 11 years old |
| Sofa | Broken AI in a cracked phone (Sofia programmed it) |
| Lina | Double agent, friend/spy, 12 years old |
| Max | Loyal friend, straightforward, honest |
| Ray | Herald of the Voice, teenage demagogue, 15 years old |
| Leon | Old professor, unreliable source |
| Vera (Vera Andreevna) | Teacher, mentor. First mention — Vera Andreevna, then simply Vera |
| Sam | Younger kid, Marko teaches him (from ep.17) |
| Voice | Antagonist, controls the Mirror City through language |

## Governing Documents

| File | Purpose | Editable? |
|------|---------|-----------|
| `vision_lock.md` | World DNA: axioms, twists, rules — concise extract from source | **NO** without author's permission |
| `context_state.md` | Current project state: what's done, what's in progress | Yes, update after each session |
| `decision_log.md` | Author's decision journal — agent does not challenge without explicit request | Yes, append to it |

## Project Structure

| Folder | Contents | Editable? |
|--------|----------|-----------|
| `source/` | Original: plot, characters, mechanics, glossary | **NO** — read-only (protected by hook) |
| `episodes/` | Working copy of the plot, split into episodes (created from `source/`) | Yes |
| `lessons_ru/` | 25 trilingual YAMLs (ru/en/uk). We use only `ru` keys | **NO** — read-only (protected by hook) |
| `lessons_en/` | English extractions — not used | Ignore |
| `pipeline/` | Pipeline: stages, rules, briefs, drafts, agents | Yes |
| `pipeline/source/episodes/` | Episode plans by day (source of truth for episodes) | Yes |
| `pipeline/gameflow/` | **Game scene-flow layer** (see Gameflow Pipeline) | Yes |
| `pipeline/gameflow/spec/` | Schema, branching rules, visual brief rules | Yes |
| `pipeline/gameflow/episodes/` | Gameflow YAML files per episode | Yes |
| `server/book/` | Human-readable episode markdown | Yes |
| `publish/game/` | Generated HTML game (output of build_game.py) | Yes (generated) |
| `tools/` | Scripts: build_game.py, validate_gameflow.py, build_book.py | Yes |
| `.claude/skills/` | Skills for agents | Yes |
| `_reference/` | Old agent prompts, skills — for study | Read-only |

## Work Cycle (Explore → Plan → Write)

1. **Explore** — read the necessary files (vision_lock, source, lesson). Do not write text.
2. **Plan** — create a chapter/task plan. Show it to the author. Wait for approval.
3. **Write** — only after the plan is approved, begin writing text.

## Pipeline

Existing story + lessons → improved book.
Pipeline in development: `pipeline/docs/pipeline.md`
Rules: `pipeline/docs/rules/content_rules.md`, `pipeline/docs/rules/qa_rules.md`

## Gameflow Pipeline

### What it is
A game scene-flow layer between episode plans and rendered HTML. Each episode is broken into interactive scenes with navigation, quizzes, choices, and visual briefs.

### Data flow
```
pipeline/source/episodes/day_NN.yaml  ──→  pipeline/gameflow/episodes/ep_NNN.yaml  ──→  publish/game/ep_NNN.html
server/book/ep_NNN.md  ──────────┘          ↑                                         ↑
                                     (manual, with skills)                    (python3 tools/build_game.py)
```

### Key files
| File | Purpose |
|------|---------|
| `pipeline/gameflow/spec/pipeline_rules.md` | How layers connect — **read this first** |
| `pipeline/gameflow/spec/gameflow_schema.md` | Scene schema: all fields, enums, examples |
| `pipeline/gameflow/spec/branching_rules.md` | 4 allowed branch types, merge rules, flag registry |
| `pipeline/gameflow/spec/visual_brief_rules.md` | How to describe art briefs per scene |
| `tools/build_game.py` | Renderer: gameflow YAML → interactive HTML |
| `tools/validate_gameflow.py` | Validator: catches duplicate keys, broken links, unused flags |

### Build commands
```
python3 tools/build_game.py              # generate all HTML from gameflow
python3 tools/validate_gameflow.py       # validate all gameflow YAML
```

### Progress
- Day 1 (ep_001–ep_004): gameflow DONE, HTML generated
- Days 2–13: gameflow NOT STARTED (episode plans exist in pipeline/source/episodes/)

## Creating Episodes (reusable for any story/season)

### Full pipeline: lessons → episodes → gameflow → game
1. **Lesson briefs** — skill `lesson-brief`: split YAML lesson into theory blocks
2. **Story grid** — skill `story-grid`: distribute blocks across days
3. **Episode plan** — skill `episode-plan`: create day plan with scenes, quizzes, story beats
4. **Episode map** — skill `episode-map`: transplant quizzes into plot context
5. **Gameflow** — skill `gameflow-build`: break episode into interactive scenes
6. **Drama restoration** — skill `gameflow-drama`: restore drama from book, break quiz streaks, reconnect quizzes to story
7. **Branches** — skill `gameflow-branch`: add optional branch scenes
8. **QA references** — skill `qa-references`: validate back-reference consistency
9. **QA branches** — skill `qa-branches`: validate branch continuity
10. **Build** — `python3 tools/build_game.py`: generate playable HTML

### When starting a new season or story
All skills, tools, and specs are **story-agnostic**. They work with any plot + lessons combination. To start fresh:
1. Create new `source/` with plot
2. Create new `lessons_ru/` with lessons
3. Run the pipeline from step 1
4. The gameflow spec and tools work as-is

## Prohibitions

- Never edit `source/`, `lessons_ru/`, `vision_lock.md`
- From YAMLs, use only `ru` keys
- A term cannot be used before it has been introduced
- The number of episodes is not fixed
- Do not generate text without an approved plan
- No `previously` blocks in gameflow episodes — the player just played the previous episode
- Lesson characters (Дмитрик, Витя, etc.) must be told as fresh stories, never as "помнишь?"
