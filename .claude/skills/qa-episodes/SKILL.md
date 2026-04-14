---
name: qa-episodes
description: |
  Validates episode-plan and episode-map outputs: term order, answer correctness,
  spoiler check, quiz completeness. Returns PASS/FAIL verdict.
  Triggers: "check episodes", "qa episodes", "qa-episodes".
  Argument: "plan" (checks episode plans), "map" (checks episode maps),
  "all" (both), day number (e.g., "plan day 1"). Without argument — all.
---

# QA Episodes — Episode Validation (Gate between Steps)

You are a **separate validation agent**. You did NOT create the files being checked.
Your job is to find errors the generator missed.

This is a gate:
- Between step 2 (episode-plan) and step 3 (episode-map): **qa-episodes plan**
- Between step 3 (episode-map) and step 4 (writing): **qa-episodes map**

Without PASS, the pipeline cannot advance.

## Language

All instructions in this file are in English.
All generated output (verdicts, reports, tables) must be written in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

For **episode plans**:
- `pipeline/episodes/day_*.yaml` — episode plans
- `pipeline/grid.yaml` — reference: terms, votes, blocks
- `pipeline/briefs/*.yaml` — reference: practice_summary, votes

For **episode maps**:
- `pipeline/mapped/ep_*.yaml` — mapped episodes
- `pipeline/episodes/day_*.yaml` — reference: structure
- `pipeline/briefs/*.yaml` — reference: original quizzes
- `lessons_ru/*.yaml` — reference: original texts (read-only)

## Three checks

### Check 1: Term order (CRITICAL)

1. For each day, build cumulative terms_available from grid.yaml
2. For each episode, verify:
   - **In episode plans:** quiz descriptions, Sofa's Rule, triggers — no future terms?
   - **In episode maps:** each quiz options[] — only from terms_available? Explanations — no future term references?
3. Result: PASS or list of violations (file, episode, field, offending term, when introduced)

### Check 2: Content correctness (CRITICAL)

**For episode plans:** check each quiz description — answer unambiguously correct?

**For episode maps (stricter):** check EACH quiz:
1. **Answer correctness:**
   - Fact = verifiable with specific tool AND confirmed
   - Opinion = CANNOT verify (no instrument, subjective assessment)
   - Falsehood = verifiable AND NOT confirmed
   - Subjective assessments (boring, beautiful, best, overtired) = ALWAYS opinion
   - If disputable → FAIL

2. **Explanation correctness:** logically follows from definition? No false claims?

3. **Binary check:** if terms_available = only [fact, opinion] → quizzes must be binary (two options)

**Common errors checklist:**
- "You're overtired" — opinion, NOT fact (no tired-o-meter)
- "Dogs are better than cats" — opinion (no better-o-meter)
- "The movie is funny" — opinion (everyone's different)
- "All kids love sweets" — falsehood (verifiable, has exceptions)
- "Water boils at 100°" — fact (thermometer)
- "There are 24 hours in a day" — fact (clock)

### Check 3: Spoiler check

For each plot quiz (type: story or plot):
1. Does it reveal a future plot twist?
2. Does it break a character before the plot does?
3. Does it show info Marko doesn't know yet?

**Key spoiler boundaries by day:**

| Twist | Revealed | Before that — forbidden |
|-------|----------|------------------------|
| Lina's grey thread | Day 3 (ep.10) | Calling Lina an agent |
| Leon's erasure | Day 3 (ep.12) | Talking about erasures |
| Vera extracts info | Day 3 (ep.12) | Calling Vera a manipulator |
| Sofia — prisoner or co-author? | Day 4 (ep.16) | Giving the answer |
| Mom knew | Day 5 (ep.19-20) | Revealing Mom's choice |
| Max's erasure | Day 6 (ep.24) | Talking about Max's death |
| Vera — Voice's daughter | Day 7 (ep.28) | Linking Vera to Voice |
| Lina's betrayal | Day 9 (ep.35) | Calling Lina a double agent |
| Lina — Sofia's agent | Day 9 (ep.36) | Revealing the "S" scar |
| Sofia + Voice co-authors | Day 12 (ep.45) | Revealing the conspiracy |

## Output format

```
QA EPISODES — РЕЗУЛЬТАТ ({plan|map})
=====================================
Проверено: {N} эпизодов из {M} дней

ПРОВЕРКА 1 — ПОРЯДОК ТЕРМИНОВ:
  День 1, эп.1: PASS (terms_available: [факт, мнение])
  День 1, эп.2: PASS (terms_available: [факт, мнение, неправда])
  ...
  ИТОГО: PASS / {N} нарушений

ПРОВЕРКА 2 — КОРРЕКТНОСТЬ КОНТЕНТА:
  День 1, эп.1, sq3: PASS
  День 1, эп.2, cq2: FAIL — «переутомился» = мнение, не факт
  ...
  ИТОГО: PASS / {N} ошибок

ПРОВЕРКА 3 — СПОЙЛЕРЫ:
  День 1: PASS (нет сюжетных спойлеров)
  ...
  ИТОГО: PASS / {N} спойлеров

=========
ВЕРДИКТ: PASS — можно переходить к шагу {следующему}
         FAIL — {список что исправить}
```

## On FAIL

For each error:
- Exact location (file, episode, quiz)
- Error type (term_order / content / spoiler)
- Problem description
- Suggested fix
- Reference to lesson definition (for content errors)

DO NOT fix automatically — only report and suggest.

## Constraints

- DO NOT edit the files being checked
- DO NOT edit source, briefs, YAML lessons
- Only check and return verdict
- When in doubt — FAIL with note "needs author decision"
