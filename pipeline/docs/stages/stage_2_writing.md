# Step 2 — Chapter Rewriting

We don't write from scratch. We take the existing episode and make two passes:

## Two passes

### Pass A — Style
Rewrite the prose of the existing episode in the chosen literary style.
Plot, characters, events — stay the same. Only how it's written changes, not what is written.

### Pass B — Lesson Weaving
Into the rewritten episode we weave the lesson so that:
- Theory arises from the situation (not a lecture, but a discovery)
- Practice (quizzes) is part of the action
- The lesson cannot be removed without breaking the scene

## Order
Pilot: lessons 1A → 1B → 2A → 2B. Then scaling (Step 3).

## Input
- `episodes/ep_XX.md` — existing episode with lesson annotation
- `pipeline/source/briefs/brief_XX.yaml` — lesson brief with blocks

## Agents

### STYLE-REWRITER
Rewrites the episode's prose in the chosen style. Preserves all events, dialogues, turns.

### THEORY-REWRITER
Weaves the lesson's theory into the episode's scenes. Examples come from this episode's plot.

### QA-THEORY
- Is the lesson's essence undistorted?
- Are the examples from the correct episode?
- Is a term used before its introduction?

### PRACTICE-REWRITER
Weaves quizzes into the action. At least 80% of practice from the lesson.

### QA-PRACTICE
- Has the correct answer shifted?
- Do the distractors work?
- 10-15 quizzes per episode

### CHAPTER-COMPOSER
Final assembly: stylized plot + theory + practice.

### QA-CONTINUITY
- Fact chronology
- Concepts are not used before introduction
- Character arcs are consistent

## Output
- `book/ep_XX.md` — finished chapter
