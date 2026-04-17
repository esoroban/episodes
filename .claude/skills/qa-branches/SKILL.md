---
name: qa-branches
description: |
  Validates branch information continuity in gameflow episodes.
  Checks that merge points don't create plot holes from skipped branches.
  Triggers: "qa branches", "check branches", "qa-branches", "validate branches".
  Argument: episode number, range, or "all".
  Without argument — validates all episodes that have branches.
---

# QA Branches — Branch Information Continuity Validator (Step 4c)

You validate that gameflow episode branches maintain information continuity.
The core rule: a player who skips ALL branches must still understand the
full story. A player who takes a branch must not encounter contradictions
when returning to the main line.

## Language

All instructions in this file are in English.
All report output must be in **Russian** (error messages, descriptions).

## Input

- `pipeline/gameflow/episodes/ep_NNN.yaml` — episode(s) to validate
- `pipeline/gameflow/branches/ep_NNN_branches.md` — branch documentation
- `pipeline/gameflow/spec/branching_rules.md` — branch rules

## Output

- Console report: PASS / FAIL per episode with details
- If issues found: specific scene IDs, what's broken, how to fix

## Algorithm

### Step 1: Parse Episode

1. Read the episode YAML
2. Build the scene graph:
   - Main line: sequence of scenes following `next_default` from s01
   - Branches: scenes with `branch_type` set, identified by `merge_to`
   - Choice points: scenes with `interaction_type: choice`
3. For each branch, identify:
   - Entry point (choice scene)
   - Branch scenes (all scenes between entry and merge)
   - Merge point (the `merge_to` target)
   - Branch depth (number of scenes)

### Step 2: Information Extraction

For each scene (main line and branch), extract:

- **Characters introduced** — first appearance of a name in `characters_present`
- **Facts revealed** — key information in `author_text` and `dialogue`
- **Items discovered** — props, objects, documents mentioned
- **Flags set** — `set_flags` values
- **Flags required** — `require_flags` values
- **Terms used** — lesson terms mentioned
- **Locations visited** — new locations

### Step 3: Continuity Checks

Run these checks for every branch:

#### CHECK 1: Main Line Self-Containment
```
For each scene S on main line AFTER a merge point:
  For each fact/character/item referenced in S:
    Is it introduced on the main line (before S)?
    YES → PASS
    NO → Is it introduced in a branch?
      YES → ERROR: "Scene {S} references {fact} which is only
             available in branch {branch_id}. Main line player
             won't know about it."
      NO → WARNING: "Scene {S} references {fact} with no
            introduction found."
```

#### CHECK 2: Branch-to-Main Transition
```
For each branch B with merge_to M:
  Read merge target scene M.
  Does M assume knowledge from the SKIPPED main line scenes?
  (scenes between choice point and M that the branch player didn't see)
  
  If choice has option A → branch, option B → main:
    Player taking branch skips main scenes between choice and M.
    Does M reference content from those skipped scenes?
    YES → ERROR: "Branch player misses scene {skipped} content
           but merge target {M} references it."
    NO → PASS
```

**IMPORTANT:** In our architecture, branches are ADDITIONS — the main line
option goes directly to the merge target. So there are no "skipped main
scenes." The choice is: take the branch (extra scenes) OR go directly
to merge target. This simplifies Check 2: just verify the merge target
doesn't assume branch content was seen.

#### CHECK 3: Flag Continuity
```
For each flag F set in a branch:
  Is F used in require_flags anywhere on main line?
  YES → ERROR: "Flag {F} set only in branch {branch_id} but
         required by main line scene {scene_id}."
  NO → Is F used in require_flags in another branch?
    YES → WARNING: "Flag {F} creates branch-to-branch dependency."
    NO → PASS (cosmetic flag, OK)
```

#### CHECK 4: Forward Reference Check
```
For each branch B:
  Read 5 scenes forward from merge point on main line.
  For each scene:
    Does dialogue/author_text reference something introduced
    ONLY in branch B?
    YES → ERROR with specific quote.
    NO → PASS.
```

#### CHECK 5: Character Introduction Check
```
For each character C appearing in a branch:
  Is this C's FIRST appearance in the episode?
  YES → ERROR: "Character {C} first appears in branch {branch_id}.
         Main line player hasn't met them."
  NO → PASS
```

#### CHECK 6: Branch Quiz Isolation
```
For each quiz Q in a branch:
  Does Q introduce a new term?
  YES → ERROR: "Quiz in branch introduces term {T}.
         Terms must be introduced on main line."
  NO → PASS
  
  Is Q counted in total_quizzes for the episode?
  YES → ERROR: "Branch quiz counted in total. Branch quizzes
         are bonus — don't count toward required total."
  NO → PASS
```

#### CHECK 7: Narrative Coherence at Merge
```
For each merge point M:
  Read the scene BEFORE the choice (pre-choice).
  Read the merge target scene M.
  
  If a player goes: pre-choice → choice → M (skipping branch):
    Does the transition make narrative sense?
    Is there a jarring jump in location, time, or emotional state?
    YES → WARNING: "Abrupt transition from {choice} to {M}
           when skipping branch. Consider adding a transitional
           sentence to M's author_text."
    NO → PASS
```

### Step 4: Cross-Episode Branch Check
```
For episodes E1, E2 where E2 follows E1:
  For each flag set in a branch of E1:
    Is that flag referenced in E2 (in require_flags or dialogue)?
    YES → Is the flag also settable on E1's main line?
      YES → PASS
      NO → WARNING: "Flag {F} from E1 branch affects E2 but
            not all E1 players will have it."
```

### Step 5: Report

Output format:

```
═══════════════════════════════════════════
QA BRANCHES — ep_NNN: «Title»
═══════════════════════════════════════════

Ветвлений: N
Сцен в ветвях: M
Глубина: 1-3

CHECK 1 — Самодостаточность главной линии
  ✅ PASS | ❌ FAIL: описание проблемы

CHECK 2 — Переход ветка → главная линия
  ✅ PASS | ❌ FAIL: описание проблемы

CHECK 3 — Флаги
  ✅ PASS | ⚠️ WARNING: описание

CHECK 4 — Упреждающие ссылки (5 сцен вперёд)
  ✅ PASS | ❌ FAIL: описание

CHECK 5 — Первое появление персонажей
  ✅ PASS | ❌ FAIL: описание

CHECK 6 — Квизы в ветвях
  ✅ PASS | ❌ FAIL: описание

CHECK 7 — Нарративная связность в точке схождения
  ✅ PASS | ⚠️ WARNING: описание

───────────────────────────────────────────
ИТОГ: X PASS, Y FAIL, Z WARNING
═══════════════════════════════════════════
```

## Common Errors and Fixes

### ERROR: Main line references branch-only content
**Fix:** Either move the reference to the branch, or add a brief version
of the info to the main line (e.g., add one line to author_text of a
main line scene that mentions the same fact).

### ERROR: Character first appears in branch
**Fix:** Add the character to a main line scene before the branch point.
Even a brief mention ("В углу стоял кто-то" → then in branch you
interact with them, on main line you just see them).

### ERROR: Branch flag gates main line
**Fix:** Either make the flag cosmetic (change dialogue tone, not gate),
or add an alternative way to set the flag on main line.

### WARNING: Abrupt transition at merge
**Fix:** Add a transitional sentence to the merge target's `author_text`
that works for both paths. E.g., "Марко вернулся к..." works whether
he explored or went straight.

## Constraints

- This skill does NOT edit episode files — it only reports issues
- The gameflow-branch skill is responsible for fixing reported issues
- Run this AFTER gameflow-branch, BEFORE final build
- Can be run on single episode, range, or all
- Cross-episode checks require both episodes to exist
