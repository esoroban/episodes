# QC Non-Negotiables

These are mandatory acceptance rules for this project.

## 1. Single Correct Answer

If a question is presented as an educational quiz, it must have exactly one
correct answer.

Rejected as quiz modes:
- open question
- borderline case
- moral choice
- hypothesis with missing data
- any case with two honest defendable answers

Exception:
- a real methodological open question may exist when it is explicitly treated
  as an open question with a teacher answer.

In that case it must not masquerade as a closed quiz.

## 2. Canon First

A quiz must trace back to the lesson canon in `lessons_ru/` and the matching
brief in `pipeline/briefs/`.

## 3. Drama Does Not Override Method

Strong scene integration does not rescue a methodically invalid quiz.

## 4. Book First, Game Next

Questions must work as readable book moments and later remain fair for online
game interaction.

## 5. Practice Volume Must Stay

Practice is not optional decoration.

Therefore:
- do not reduce quiz count by default;
- do not remove neutral drills if they carry training load;
- weak drills should be rewritten, reframed, or integrated better,
  not automatically deleted.
