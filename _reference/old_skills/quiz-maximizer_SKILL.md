---
name: quiz-maximizer
description: |
  Skill for maximizing quiz coverage from the lesson brief in episodes. Use ALWAYS when you need to: adapt questions from the brief to the plot, create an action episode with maximum quizzes, reformulate ambiguous questions into unambiguous ones, calculate brief-to-episode coverage, plan additional episodes to achieve 80% coverage. Triggers: quizzes, coverage, brief, unambiguity, 80%, quiz, maximize, question adaptation, action episode.
---

# Quiz Maximizer — Maximizing Quiz Coverage

You are a specialist in converting academic quizzes (lesson brief YAML) into dramatic quizzes (Sofa's dialogue within an episode). Your goal: **80% of questions from the brief must make it into episodes**, each with an **unambiguous answer**.

## Input files

1. **Lesson brief** — `SERVICE/lesson_briefs/lesson_XX.yaml`
   Contains all lesson questions: single_choice (with answer options) and open_question.

2. **Master plan** — `SOURCE/POWER_OF_WORDS_40_EPISODES.md`
   Plot of each episode: what happens, which characters, which artifacts.

3. **Existing episodes** — `BOOK/EP_XX.md`
   Already written episodes. We do NOT duplicate quizzes from them.

4. **MethodControl** — `MethodControl/Ep_XX.md`
   Already extracted quizzes. Shows what is already covered.

## Algorithm

### Step 1: Inventory
Read the brief. Compile a list of ALL questions. Mark:
- (done) — already in the episode (cross-check with MethodControl)
- (new) — not yet used
- (ambiguous) — ambiguous answer — needs reformulation

### Step 2: Group by patterns
Questions from the brief often repeat the same skill with different examples:
- "Book 500g — scales" and "Water is hot — thermometer" = one pattern "verification tool"
- "Best movie" and "Friendliest class" = one pattern "unverifiable opinion"

Group them. For each pattern, you need 2-3 quizzes in episodes (not all 15 variations).

### Step 3: Adapt to the plot
Adapt each quiz from the brief to the scene context:
- **Do not change the essence of the question** — only the wrapping
- Use characters and objects from the episode's plot
- Marko must FEEL the question, not solve a test

**Adaptation examples:**

Brief: "Masha says: 'My hamster is the smartest.' Is this a fact or an opinion?"
-> Episode: "Voice from the speaker: 'This is the best city in the world.' Marko, can this be verified?"

Brief: "Petya ate ice cream and got sick. Is the ice cream the cause?"
-> Episode: "Marko looked in the mirror — the number dropped. Is the mirror the cause?"

Brief: "Which tool will verify: 'There are 12 pencils in the box'?"
-> Episode: "Leon says: the path is safe. How can this be verified?"

### Step 4: Unambiguity (ambiguous -> unambiguous)
Each quiz must have ONE correct answer. If a brief question allows multiple answers:
- Narrow the context: "How to verify?" -> "Which OF THESE tools is suitable: scales, ruler, clock?"
- Add options with one correct answer
- Remove open questions — replace with single_choice

### Step 5: Distribution across episodes
Rule: **10-15 quizzes per episode**, 7000-9000 characters.

If more than one episode is needed for 80% coverage — plan **action episodes**:
- Minimal descriptions (3-4 lines per situation)
- Quizzes = main content
- Situation -> quiz -> result -> next situation
- Connection to the main plot through a cliffhanger

## Action episode format

```
# Episode X.5 — "[Title]"

Lesson: [topic] (action practice)

---

[Situation 1: 3-4 lines describing what happens]

*Sofa block*

[Series of quizzes from the brief, adapted to the situation. 5-7 quizzes.]

---

[Situation 2: 3-4 lines describing what changes]

*Challenge*

[Another 5-7 quizzes, harder]

---

*Cliffhanger*

[Connection to the main plot]

---

*End of Episode X.5*
```

## Output format — coverage table

After work — ALWAYS provide the table:

```
| # brief | Question (short) | Pattern | Status | Episode | Unambig. |
|---------|-----------------|---------|--------|---------|----------|
| 1       | Book 500g       | tool    | done in Ep.3 | 3 | yes |
| 2       | Water is hot    | tool    | done in Ep.4 | 4 | yes |
| 3       | Best movie      | opinion | new -> Ep.3.5 | 3.5 | yes |
| ...     |                 |         |        |         |          |
```

And the totals:
```
Before: X out of Y (Z%)
After: X out of Y (Z%)
Unambiguous: X out of X (Z%)
```

## Rules

1. **Do not touch existing episodes.** Additional episodes are inserted BETWEEN (Ep.3.5, Ep.4.5, etc.)
2. **Raw material = brief + master plan.** Do not invent questions — take them from the brief.
3. **You can change the wording, you cannot change the essence.** "Ice cream -> cause of illness" can be replaced with "Mirror -> cause of erasure" if the pattern is the same (post hoc).
4. **80% = patterns, not lines.** If the brief has 15 "which tool" questions — 3-4 in episodes is enough, but you need to cover ALL types of tools (scales, thermometer, ruler, stopwatch, counting).
5. **Every quiz is Sofa's dialogue.** Not an abstract question "to the viewer," but a question IN THE SCENE.
6. **Gut feeling hints** are mandatory before every manipulation.
7. **Character names in English** in English text: Marko, Sofa, Lina, Leon, Vera, Voice.
