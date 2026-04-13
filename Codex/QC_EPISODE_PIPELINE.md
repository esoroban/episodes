# Episode QC Pipeline

This pipeline is for reviewing finished or draft episodes and producing a
rewrite-oriented summary.

It is designed for a product that must work first as a book and later as an
online game.

## Goal

For every episode:
- check methodology against `lessons_ru/*.yaml`;
- check quiz quality and drama integration;
- produce a concise rewrite brief;
- rerun the check after changes.

## Inputs

Required:
- episode text from `book/` or another working episode file;
- matching lesson YAML from `lessons_ru/`;
- matching lesson brief from `pipeline/briefs/`.

Optional but useful:
- lesson map;
- prior QC reports;
- author decisions in [AUTHOR_DECISIONS.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/Codex/AUTHOR_DECISIONS.md).

## Pipeline Stages

### Stage 0. Match

Map:
- episode -> lesson;
- episode -> allowed vocabulary;
- episode -> required practice types.

Output:
- episode lesson card;
- list of lesson concepts that must survive adaptation.

### Stage 1. Extract

Extract from the episode:
- all quiz-like questions;
- all open questions;
- all rules Sofa states;
- all places where the quiz changes action.

Output:
- raw question inventory.

### Stage 2. Classify Question Type

Every question must be tagged as exactly one of:
- `closed_quiz`
- `open_hypothesis`
- `dramatic_choice`
- `discussion_prompt`
- `open_question_teacher_answer`

Rule:
- only `closed_quiz` may be judged by right/wrong QC standards.
- every `closed_quiz` must have exactly one defendable correct answer.
- `open_question_teacher_answer` is allowed only when the methodology truly
  requires an open question followed by a teacher answer.

Output:
- question mode map.

### Stage 3. Method Check

For each `closed_quiz`:
- trace it to the lesson canon;
- identify the expected answer;
- test ambiguity;
- test whether future knowledge is required;
- test whether the question teaches the intended idea.

For each `open_question_teacher_answer`:
- trace it to the lesson canon;
- verify that open form is methodically justified;
- verify that teacher answer is pedagogically sufficient;
- verify that the open form is not replacing a required closed quiz.

Output:
- methodology findings;
- episode methodology score.

### Stage 4. Drama Check

For each question block:
- assign drama integration score `0-3`;
- check whether the question arises from action;
- check whether success/failure changes what happens next;
- check whether the scene would weaken if the quiz were removed.

Output:
- drama findings;
- episode drama-integration score.

### Stage 5. Book-to-Game Check

Check:
- can the question become a fair game choice later;
- can the player understand success conditions;
- is the answer visible from scene logic, not only author intent;
- does the scene support replay and feedback.

Output:
- gameplay conversion findings.

### Stage 6. Rewrite Brief

Produce a short rewrite summary using four lists:
- `keep`
- `cut`
- `replace`
- `add`

Rule:
- no abstract critique without an action.
- do not reduce practice volume as a default fix.
- when a quiz example is weak, prefer `replace` or `rewrite in-scene`
  over `cut`.

Output:
- rewrite brief for the episode.

### Stage 7. Rerun

After changes:
- rerun the same pipeline;
- compare before/after;
- confirm whether the rewrite actually fixed the flagged issues.

Output:
- delta report.

## Mandatory Episode Deliverables

Each reviewed episode must end with:
- methodology score;
- drama value score;
- top blockers;
- rewrite summary;
- optional second-pass notes after rerun.

## Output Formats

Primary user-facing format:
- HTML report in Russian.

Internal support format:
- Markdown or English notes inside `Codex`.

## Rewrite Summary Template

For each episode:

1. Keep:
   what already carries both lesson and drama.
2. Cut:
   what is methodically invalid or dead weight.
3. Replace:
   what has the right job but the wrong form.
4. Add:
   what the lesson canon requires but the episode still under-delivers.

## Quality Bar

An episode is ready for the next stage when:
- all closed quizzes have defendable answers;
- all closed quizzes have exactly one defendable correct answer;
- open questions are no longer masquerading as closed quizzes;
- all teacher-answer open questions are explicitly marked and justified;
- the episode preserves the lesson core;
- the episode preserves required practice density;
- the drama is not reduced to a worksheet;
- the questions are viable for later game conversion.
