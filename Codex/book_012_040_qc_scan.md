# QC Scan — New Episodes 12-40

## What exists

Current `book/` contents:
- `ep_001.md` ... `ep_040.md`

## What had not been fully checked before this pass

Before this scan:
- `ep_001-011` had already been reviewed in depth
- `ep_012-015` had only partial order-focused review
- `ep_016-040` had not been fully reviewed

This pass focuses on the **new corpus**:
- `ep_012-040`

Rules used:
- closed учебный вопрос = one defendable correct answer
- open / hypothesis / teacher-answer modes must not masquerade as closed quiz
- examples should be attached to drama as much as possible
- lesson order must not jump ahead

---

## High-confidence findings

### 1. `BLOCKER` Episode 16 marks two-leg persuasion as “balanced”

In [ep_016.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_016.md:85):
- `Эту книжку читают учителя, и в ней 100 интересных историй.` → `сбалансировано`

Problem:
- by the episode’s own rule, balance requires **all three**: trust + feelings + evidence
- this example only has trust + evidence

Same issue in [ep_016.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_016.md:89):
- `Я здесь работаю 15 лет, и этот товар хвалят все покупатели.` → `сбалансировано`

Problem:
- again, no clear emotional leg
- the keyed answer conflicts with the lesson definition

Direction:
- either change answer to `не сбалансировано`
- or add the missing third leg into the prompt

### 2. `BLOCKER` Episode 25 leaves a closed contradiction question non-closed

In [ep_025.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_025.md:63):
- `«На обед — каша!» Через час: «На обед — суп!» Противоречие?` → `возможно`

Problem:
- `возможно` is not a closed quiz answer under your rules
- the question is under-specified and should not be keyed as a closed binary check

Direction:
- either specify that both statements refer to the same menu at the same time
- or move it to open/teacher-answer mode

### 3. `BLOCKER` Episode 28 also leaves a closed contradiction question non-closed

In [ep_028.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_028.md:75):
- `Вася: «Я за здоровое питание!» — ест бургер в субботу. Противоречие?` → `неоднозначно`

Problem:
- same defect: closed question, non-closed answer
- this directly violates your `must have` rule

Direction:
- either rewrite to a clean contradiction
- or explicitly mark it as open/teacher-answer

### 4. `BLOCKER` Episode 35 asks a binary question but gives a third answer

In [ep_035.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_035.md:89):
- `Разбирается или нет?` → `нужно уточнить`

Problem:
- the question frame is binary
- the keyed answer introduces a third category

Direction:
- either change the question to `разбирается / не разбирается / нужно уточнить`
- or make the example itself decisive

### 5. `BLOCKER` Episode 36 repeats the same structural defect

In [ep_036.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_036.md:57):
- `Уместная ссылка или ошибка?` → `нужно уточнить`

Problem:
- again, binary frame, third answer
- not acceptable for a closed quiz as currently phrased

Direction:
- either add `нужно уточнить` as a formal option
- or rewrite example to produce a clean binary result

### 6. `MAJOR` Episode 15 leaks the next lesson too early

In [ep_015.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_015.md:113) and [ep_015.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_015.md:133):
- `три ножки табуретки`
- `табуретка на двух ножках не стоит`

Problem:
- this already teaches `balance of persuasion methods`
- but the episode is supposed to be the base introduction of `ethos/pathos/logos`

Direction:
- keep `ep_015` on identifying the three methods
- move the `taburetka / balance` thesis fully into the next episode

### 7. `MEDIUM` Episode 20 contains a weakly attached external practice block

In [ep_020.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_020.md:97):
- school cafeteria
- break length
- classroom hamster

Problem:
- methodically understandable
- but dramatically weakly attached to current story state

Direction:
- keep practice volume
- re-skin these examples into the world of Sofia / Voice / school journal / Vera / underground

### 8. `MEDIUM` Episode 14 under-trains `gestures` relative to the rest of 4A

In [ep_014.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_014.md:51):
- gestures are introduced
- but compared with pose / mimic / intonation, they get much less concrete exercise

Problem:
- not a lesson-order failure
- but a methodological thin spot inside the block

Direction:
- add or rewrite 1-2 practice items so gestures are not only declared, but actually discriminated

### 9. `MEDIUM` Episode 39 likely overclassifies a loaded question as a trap

In [ep_039.md](/Users/iuriinovosolov/Documents/SylaSlovaDramma/book/ep_039.md:105):
- `Ты часто врёшь родителям?` → `ловушка`

Risk:
- this is certainly a loaded or accusing question
- but as phrased, it is not as clean a trap as `Когда ты перестал...`
- a child could defensibly parse it as an ordinary accusatory question

Direction:
- if you want a pure trap, use a stronger hidden presupposition
- example: `Когда ты перестал врать родителям?`

---

## Overall scan verdict

### What is already strong
- the lesson ladder from `ep_012` onward is much cleaner than the earlier drift in `ep_003 / ep_004 / ep_011`
- `ep_012-014` are generally methodically on track
- the later curriculum is structurally present across `ep_016-040`

### Main recurring defects in the new corpus
- binary question frame + third answer in key
- closed question + non-closed keyed answer (`возможно`, `неоднозначно`)
- some practice blocks remain externally skinned instead of drama-native
- a few episodes begin teaching the next step slightly too early

## Immediate priority list

1. `ep_016` — fix the “balanced / not balanced” answer key
2. `ep_025` — remove `возможно` from closed contradiction question
3. `ep_028` — remove `неоднозначно` from closed contradiction question
4. `ep_035` — fix binary frame vs third answer
5. `ep_036` — fix binary frame vs third answer
6. `ep_015` — remove early `taburetka / balance` teaching from the cliff
