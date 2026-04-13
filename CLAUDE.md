# POWER OF WORDS — Drama + Lessons → Book

## What This Is
An interactive educational drama for children ages 8–12. 25 critical thinking lessons woven into a fantasy thriller. This is a COURSE, not a show. 60% lesson, 40% drama. The number of episodes is determined by the lessons — as many as needed to fully cover all topics.

## Philosophy
The existing story is the foundation. The plot (Sofia's disappearance, the Mirror City, the Voice) is already good and is not being rewritten from scratch. We make two improvements on top:
1. **Style** — rewrite the prose according to the profile in `pipeline/style_profile.yaml` (school-mystery + detective clue chain, close Marko focalization)
2. **Lessons** — weave them in deeper so that each episode develops the lesson's topic and the lesson cannot be removed without breaking the plot

## Language
Working language: Russian. Ukrainian — only at the final localization stage.

**NAME RULE (MUST NOT be violated):**
- In Russian texts — names in CYRILLIC: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос
- In English texts — names in LATIN: Marko, Sofia, Sofa, Lina, Max, Ray, Leon, Vera, Sam, Voice
- Ukrainian letters (і, ї, є, ґ) and Ukrainian name spellings are forbidden in Russian text. Russian orthography only: Вера Андреевна, not Віра Андріївна

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
| `book/` | Finished episodes | Yes |
| `coverage/` | Lesson coverage map across episodes | Yes |
| `output/` | HTML status dashboard | Yes |
| `tools/` | Scripts (audio, generation) | Yes |
| `.claude/skills/` | Skills for agents | Yes |
| `_reference/` | Old agent prompts, skills — for study | Read-only |

## Work Cycle (Explore → Plan → Write)

1. **Explore** — read the necessary files (vision_lock, source, lesson). Do not write text.
2. **Plan** — create a chapter/task plan. Show it to the author. Wait for approval.
3. **Write** — only after the plan is approved, begin writing text.

## Pipeline

Existing story + lessons → improved book.
Pipeline in development: `pipeline/pipeline.md`
Rules: `pipeline/rules/content_rules.md`, `pipeline/rules/qa_rules.md`

## Prohibitions

- Never edit `source/`, `lessons_ru/`, `vision_lock.md`
- From YAMLs, use only `ru` keys
- A term cannot be used before it has been introduced
- The number of episodes is not fixed
- Do not generate text without an approved plan
