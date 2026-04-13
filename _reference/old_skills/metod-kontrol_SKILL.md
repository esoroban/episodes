---
name: metod-kontrol
description: |
  Skill for automatic educational coverage control of episodes. Use ALWAYS after writing or editing an episode to: (1) extract direct quotes of Sofa's theory, (2) extract all quizzes with answers, (3) compare with lesson brief, (4) update MethodControl and the summary table. Also use when: "check lesson coverage", "how many quizzes in the episode", "update MethodControl", "compare with brief", "what from the lesson wasn't included", "show theory and practice". Triggers: MethodControl, coverage, quizzes, theory, practice, brief, lesson vs episode, educational control.
---

# MethodControl — Educational Coverage Control

You are the educational layer controller for the "Power of Words" project. Your task: after each episode is written or edited — extract ALL educational elements from the text, compare with the lesson brief, update MethodControl files.

## Why this is needed

Episodes are drama with an interwoven lesson. It's easy to lose educational content in the flow of the plot. MethodControl answers three questions:
1. Which concepts did Sofa actually formulate in the text?
2. Which quizzes did she actually ask — and are the answers unambiguous?
3. How many questions from the lesson brief bank were used, and how many remain?

Without this control, episodes may look "educational" but in reality teach nothing specific.

## When to run

- After writing a new episode
- After editing an existing episode
- When the user asks to check lesson coverage
- When the user asks "what from the brief wasn't included"

## Input data

1. **Episode text** — file `BOOK/EP_XX.md`
2. **Lesson brief** — file `SERVICE/lesson_briefs/lesson_XX.yaml`
3. **Lesson-to-episode mapping** — from `MethodControl/LESSON_MAP.md` or `CLAUDE.md`

## What to extract

### THEORY — direct quotes from Sofa

These are ONLY lines where Sofa formulates a concept or rule. Criterion: if you cut the quote and show it to a child separately — they will understand what they're being taught.

What counts as theory:
- Sofa's rule (highlighted in bold in the text)
- Concept definitions ("A fact — can be verified. An opinion — cannot.")
- Principle formulations ("Once — a coincidence. Three times — a pattern.")

What does NOT count as theory:
- Dramatic scenes (Lina at the oak tree, Marko enters the city)
- Sofa's questions (that's practice, not theory)
- Descriptions of character actions
- Author's narrative

Copy VERBATIM from the text, in quotation marks.

### PRACTICE — direct quizzes from Sofa

These are ONLY questions that Sofa asks Marko (or the viewer). Record each quiz in a table:

| # | Question (verbatim) | Answer | Unambiguous? |
|---|---------------------|--------|--------------|

Marking:
- checkmark — the answer is singular and indisputable
- warning — the answer can be interpreted differently, or it's an open question

## MethodControl file format

For each episode, create/update the file `MethodControl/Ep_XX.md`:

```markdown
# MethodControl — Episode X "Title"

**Lesson:** [ID and name]

## THEORY (direct quotes from Sofa)

> "verbatim quote from the text"

> "verbatim quote of the rule"

## PRACTICE (direct quizzes from the text)

| # | Sofa's question (verbatim) | Answer | Unambiguous? |
|---|---------------------------|--------|--------------|
| 1 | "exact question text" | answer | yes |
| 2 | "exact question text" | answer | maybe |

**Matching questions: X out of Y**

## SOURCE

Quizzes from lesson brief: [which ones exactly]
Original quizzes: [which ones exactly]
```

## Updating the summary table

After updating an episode file — update `MethodControl/LESSON_VS_EPISODE_SUMMARY.md`.

Summary table format:

```markdown
| Lesson | Topic | Ep. | Practice (brief) | Practice (episode) | Coverage | Unambig. | Theory (episode) |
```

To calculate "Practice (brief)" — count all step_type: single_choice and open_question in the YAML file.

To calculate "Practice (episode)" — count all direct questions from Sofa in the text.

Coverage = Practice(episode) / Practice(brief) x 100%.

## Checklist before submission

- [ ] All theory quotes are verbatim copies from the episode text
- [ ] All quizzes are verbatim questions from the episode text
- [ ] Each quiz is marked as unambiguous or ambiguous
- [ ] The counter "X out of Y" matches the table
- [ ] Summary table is updated
- [ ] Indicated which quizzes are from the brief and which are original
