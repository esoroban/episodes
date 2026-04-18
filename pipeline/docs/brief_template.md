# EPISODE BRIEF TEMPLATE

> Brief = specification for the screenwriter agent.
> Separates design (creative authority) from implementation.
> One brief → one episode. The agent makes no creative decisions — only implements the brief.

---

## Filled out for each episode

```yaml
# ═══════════════════════════════════════════
# EPISODE BRIEF — EP_XX
# ═══════════════════════════════════════════

episode_number: XX
episode_title: "Episode title"
act: X                          # Act (I–V)
lesson: "XX"                    # Lesson code (1A, 1B, 2A...)
lesson_type: "theory / practice / review"

# ───────────────────────────────────────────
# 1. CORE PURPOSE
# One sentence: why this episode exists.
# Format: [what skill we teach] + [what plot shift occurs]
# ───────────────────────────────────────────
core_purpose: >
  The child learns to distinguish fact from opinion,
  while Marko discovers that his sister has been erased from everyone's memory.

# ───────────────────────────────────────────
# 2. CHARACTER POV
# Whose point of view the material is presented from.
# Affects vocabulary complexity and emotional tone.
# ───────────────────────────────────────────
pov_character: "Marko"
pov_note: >
  Marko — 11 years old, cautious, prone to self-doubt.
  Simple vocabulary, short sentences.

# ───────────────────────────────────────────
# 3. THEORY TARGET
# Specific terms and formulas from GLOSSARY.md
# that must be INTRODUCED or USED in this episode.
# ───────────────────────────────────────────
theory_new:                      # New terms, introduced for the first time
  - term: "fact"
    definition: "can be verified, and verification confirms it"
    must_introduce_via: "situation, not a lecture"
  - term: "opinion"
    definition: "cannot be verified; a personal feeling, evaluation"
    must_introduce_via: "situation, not a lecture"

theory_available:                # Terms from previous lessons (can be used)
  - "list from GLOSSARY.md for this lesson"

theory_forbidden:                # Terms from FUTURE lessons (FORBIDDEN)
  - "reason"                     # appears only in 2B
  - "soldier / scout"            # appears only in 3A

# ───────────────────────────────────────────
# 4. NARRATIVE SUMMARY
# Emotional arc of the scene. Three acts within the episode.
# Teaching must not be dry — it is embedded in emotion.
# ───────────────────────────────────────────
narrative_arc:
  setup: >
    Description of the beginning: where we are, what the hero feels,
    what conflict initiates the action.
  confrontation: >
    Central confrontation: what goes wrong,
    where the lesson theory becomes a necessity,
    where Sofa steps in.
  resolution: >
    How it ends: what the hero understood,
    what changed, cliffhanger for the next episode.

gut_feeling_moment: >
  Required: BEFORE Sofa names the technique —
  Marko (and the reader) must FEEL that something is off.
  Describe the physical/emotional sensation.
  Example: "Everything sounded right, but he wanted to leave."

# ───────────────────────────────────────────
# 5. CONTINUITY
# Stitching with the previous and next episode.
# ───────────────────────────────────────────
continuity:
  previous_episode_ends: >
    Brief description: how the previous episode ended.
    Where the characters are, what happened, emotional tone.
  this_episode_starts: >
    Where and how this episode begins.
    Must logically follow from the previous one.
  this_episode_ends: >
    Cliffhanger or bridge to the next episode.
  next_episode_needs: >
    What the next episode expects to receive
    (location, hero's state, open questions).

# ───────────────────────────────────────────
# 6. KNOWLEDGE TRANSITION
# What the character LEARNED in this episode.
# Acquisition Log — for agent verification.
# ───────────────────────────────────────────
knowledge_acquired:
  - "Marko learned: a fact is something that can be verified"
  - "Marko learned: an opinion cannot be verified, everyone has their own"
  - "Marko understood: Lina confuses details → she cannot be trusted blindly"

knowledge_not_yet:
  - "Marko does NOT yet know about excuses (lesson 1B)"
  - "Marko does NOT yet know about the Mirror City"

# ───────────────────────────────────────────
# 7. QUIZ SCHEMA
# Quiz structure. What types, how many, on what topic.
# ───────────────────────────────────────────
quiz_schema:
  total_target: "10–15"
  format: "Sofa: 'question' → options → ✅ answer — explanation"

  blocks:
    - name: "Warm-up"
      count: "3–5"
      type: "quick, unambiguous"
      topic: "new lesson terms with simple examples FROM THE PLOT"
      note: "Examples tied to the episode's world, not abstract"

    - name: "Theory through situation"
      count: "3–5"
      type: "Sofa introduces the definition AFTER the situation"
      topic: "story from lesson brief + situation from the plot"
      note: "Situation first → then the label. Not the other way around."

    - name: "Challenge"
      count: "3–5"
      type: "complex, ambiguous, require reflection"
      topic: "drama quizzes: Sofia's notes, Lina's words, artifacts"
      note: "Tied to the episode's conflict"

  allowed_options: "ONLY from GLOSSARY.md for this lesson"
  forbidden_options: "terms from future lessons"

# ───────────────────────────────────────────
# 8. STORIES FROM BRIEF
# Required stories/scenarios from the lesson YAML
# that must be integrated into the episode.
# ───────────────────────────────────────────
required_stories:
  - story: "Ice cream argument (Mykola and Masha)"
    how_to_integrate: >
      Do not copy verbatim. Retell through the episode's characters
      or as an example that Sofa provides.
  - story: "Dmytryk and cancelled lessons"
    how_to_integrate: >
      Similarly — through a situation in Marko's world.

# ───────────────────────────────────────────
# 9. CONSTRAINTS
# Hard constraints for the screenwriter agent.
# ───────────────────────────────────────────
constraints:
  length: "7000–9000 characters"
  language: "Russian"
  names: "in Cyrillic (Марко, София, Лина, Макс, Рей, Вера, Леон, Сем, Голос)"
  no_lectures: "theory ONLY through situations; Sofa labels AFTER"
  no_forward_refs: "FORBIDDEN to use terms from future lessons"
  no_invented_theory: "FORBIDDEN to invent theory not present in the lesson YAML"
  no_dangling_refs: "FORBIDDEN to reference events that did not occur in previous episodes"
  gut_feeling: "REQUIRED: physical sensation before each labeling"
  quiz_from_drama: "at least 5 quizzes tied to episode events/dialogues"
```

---

## How to use

1. **Author** fills out the brief (or with Claude's help based on PLOT + lesson YAML + GLOSSARY)
2. **Screenwriter agent** receives ONLY the brief + CHARACTERS.md + MECHANICS.md
3. **QA agents** check the draft AGAINST the brief (not against their own opinion)
4. **Iteration:** QA report → fixes → re-QA → final version
