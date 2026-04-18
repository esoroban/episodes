# Question Modes

This file defines the allowed question modes for QC.

## 1. closed_quiz

Use when:
- the learner must choose or produce one correct answer.

Acceptance rule:
- exactly one defendable correct answer.

## 2. open_question_game_input

Use when:
- the methodology intentionally asks an open question;
- the episode explicitly marks it as an open-input task;
- the future game can present it as a free-text or open-response interaction.

Acceptance rules:
- must be explicitly marked as open;
- must belong to the lesson logic;
- must not replace a spot where a closed quiz is required;
- must include a clear hint or algorithm;
- must include an example-model answer;
- must be logically usable in the future game without pretending to have one
  hidden exact answer.
- if it is reflective or philosophical, it must be treated as reflection,
  not as scored correctness.
- if it changes the plot or values, it should usually be treated as a
  dramatic choice, not as pedagogical open input.

## 3. open_hypothesis

Use when:
- the story does not yet provide enough data;
- the learner is invited to hypothesize.

Acceptance rule:
- do not score as right/wrong quiz.

## 4. dramatic_choice

Use when:
- the story asks for a value choice or risk choice.

Acceptance rule:
- do not score as right/wrong quiz unless the design explicitly converts it
  into a closed decision task.

## 5. discussion_prompt

Use when:
- the scene invites reflection or transition talk.

Acceptance rule:
- not a scored quiz.
