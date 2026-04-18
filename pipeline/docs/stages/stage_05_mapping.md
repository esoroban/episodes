# Step 0.5 — Lesson-to-Plot Mapping

Intermediate step between the lesson brief (step 0) and the episode brief (step 1).
Transplants generic examples from the lesson into Marko's world.

## Why

The lesson contains generic characters (Mykola, Masha, Dmytryk) and generic situations
(schoolyard, ice cream stand). The mapping transforms them into our story's world:
the same situations, but with our characters and tied to book events.

## Input

- `pipeline/source/briefs/brief_{ID}.yaml` — lesson brief (from step 0)
- `source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md` — plot (read-only)
- `lessons_ru/lesson_{ID}.yaml` — lesson YAML (read-only, only ru keys)

## Output

- `pipeline/work/mappings/mapping_{ID}.yaml` — lesson-to-plot mapping

## Skill

`.claude/skills/lesson-map.md`
Invocation: `/lesson-map {ID}` (e.g. `/lesson-map 1A`)

## Three Mapping Principles

### 1. Transplantation, not reinvention

Examples from the lesson are preserved as close to the original as possible.
An ice cream argument stays an ice cream argument — it's just Marko and Max arguing,
not Mykola and Masha. Change the content of an example only if it truly doesn't fit.

### 2. Character substitution

Generic children from the lesson are replaced with characters from our plot.
The circumstances remain the same — school, recess, classroom. But it's Marko's school.

Substitution rules:
- One generic character → one of our characters (within a block)
- Choose by personality: which of our characters would behave similarly?
- Do NOT overload one character excessively within a single lesson
- Main characters (Lina, Ray, Vera) — use carefully:
  their role in the plot must not be compromised by premature revelation
- For minor roles, unnamed classmates are allowed

### 3. Plot quizzes — the majority

Most quizzes are tied to Marko's world. Structure of each practice block:

- **Warm-up (first 2-3)** — simple generic ones, as in the lesson.
  Needed for warm-up — the child is still getting into the mode.
- **Middle (4-6)** — from Marko's life, from his school, from his friends.
  Familiar characters in familiar situations.
- **Finale (3-5)** — provocative, from the main plot.
  The most valuable. Questions without a clear-cut answer at the current
  stage of the plot. Make the reader think and want to find out what happens next.

Examples of finale quizzes:
- "Marko doesn't have a sister — fact, opinion, or falsehood?"
- "Voice says: 'It's safe here.' Verifiable?"
- "Lina said: 'I remember Sofia.' Is this a fact?"

## Rules for plot quizzes

1. **No spoilers.** A quiz can pose a question whose answer will be
   revealed later. But it must not reveal a plot twist.

2. **Don't break characters.** A quiz must not portray a character as
   unambiguously bad/good before that is revealed in the plot.
   "Vera is a kind teacher" — acceptable (the child thinks so).
   "Vera is a manipulator" — unacceptable (spoiler).

3. **Open questions are more valuable than closed ones.** "Can this be verified?" —
   better than "this is a lie." The child should think, not guess.

4. **Cumulativeness.** A quiz can only use terms that have already been
   introduced (in this block or earlier). You cannot use
   "fake" in a block where only "fact" and "opinion" have been introduced.

## Author validation

After creating the mapping — show it to the author for approval.
Required questions:
- Are all character substitutions logical?
- Are there spoilers in the plot quizzes?
- Is the generic/plot quiz balance acceptable?
- Is any character overloaded?

## Status

- [x] mapping_1A.yaml — done (pilot)
- [ ] remaining lessons — after format approval
