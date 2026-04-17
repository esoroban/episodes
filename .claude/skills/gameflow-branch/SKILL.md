---
name: gameflow-branch
description: |
  Creates branch scenes for gameflow episodes.
  Reads episode YAML, finds drama scenes, designs 2-3 scene branch loops.
  Triggers: "branch", "add branches", "gameflow-branch", "branches for ep 5".
  Argument: episode number (1–50), range ("ep 5-8"), or "all".
  Without argument — asks which episode.
---

# Gameflow Branch — Add Interactive Branches to Episodes (Step 4b)

You add interactive branch scenes (flavor detours, investigation loops,
conversation forks, observation chains) to existing gameflow YAML episodes.
Branches are loops that ALWAYS return to the main line.

## Language

All instructions in this file are in English.
All generated output (scenes, dialogue, choices) must be in **Russian**.
Character names in output: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input

- `pipeline/gameflow/episodes/ep_NNN.yaml` — existing episode to add branches to
- `pipeline/gameflow/branches/branch_patterns.md` — catalog of branch patterns
- `pipeline/gameflow/branches/ep_NNN_branches.md` — branch plan for this episode (if exists)
- `pipeline/gameflow/spec/branching_rules.md` — allowed branch types and merge rules

## Output

- Updated `pipeline/gameflow/episodes/ep_NNN.yaml` — with new branch scenes inserted
- Updated or created `pipeline/gameflow/branches/ep_NNN_branches.md` — branch documentation

## Algorithm

### Phase 1: Explore

1. Read `pipeline/gameflow/branches/branch_patterns.md` — know the 7 patterns
2. Read `pipeline/gameflow/spec/branching_rules.md` — know the rules
3. Read the target episode YAML — identify all scenes
4. Identify drama scenes (non-quiz, non-phone-chain) — these are branch candidates
5. Read the branch plan file if it exists (`pipeline/gameflow/branches/ep_NNN_branches.md`)
6. Read the day plan (`pipeline/episodes/day_NN.yaml`) — know the story context

### Phase 2: Plan (STOP — show author)

For each proposed branch, produce:

```
Branch N.M — [Pattern Name] (depth: X scenes)
  Location: after scene sNN
  Choice text: "Option A" / "Option B"
  Path A: sNNd1 → sNNd2 [→ sNNd3] → merge_to: sNN+1
  Path B: (main line, no extra scenes) OR sNNb1 → sNNb2 → merge_to: sNN+1
  Content: what the player discovers/experiences
  Info continuity: what info exists on main line vs branch
```

**STOP. Show the branch plan to the author. Wait for approval.**

### Phase 3: Write

After approval:

1. Write branch scenes into the episode YAML at the correct positions
2. Update the choice scene to include `interaction_type: choice` with options
3. Set `branch_type: flavor_detour` on detour scenes
4. Set `merge_to` on last scene of each branch
5. Update flow comment at top of YAML file
6. Write/update `pipeline/gameflow/branches/ep_NNN_branches.md`

## Branch Patterns (reference — full catalog in branch_patterns.md)

| Pattern | Depth | Description |
|---------|-------|-------------|
| Peek | 1 | Quick look, one scene |
| Investigation Loop | 2 | Discover → react |
| Conversation Fork | 2+2 | Two dialogue paths, same destination |
| Emotional Spiral | 2 | Emotional choice → consequence |
| Observation Chain | 3 | Progressive discovery, 3 observations |
| Try-and-Learn | 2 | Attempt → unexpected result |
| Parallel Discovery | 2+2 | Two ways to learn same fact |

## Branch Placement Rules

### Where to place branches

1. **Before phone chain 1** — in drama/setup scenes (s01–s03 range)
2. **Between phone chains** — in the narrative break scene
3. **Before cliffhanger** — in post-challenge drama scenes
4. **NEVER inside a phone chain** — quiz chains must be uninterrupted

### How many per episode

- Minimum: 2 branches per episode
- Maximum: 4 branches per episode
- At least one branch with depth 2+ scenes
- Target: ~5-8 extra scenes per episode from branches

## CRITICAL: Information Continuity Rule

**The main line must be self-contained.** A player who skips ALL branches
must still understand the full story. Branches add DEPTH, not PLOT.

### What branches CAN contain (bonus content)

- Atmosphere, world-building, lore
- Character depth (backstory, emotions, observations)
- Clues and hints (foreshadowing, not plot-critical reveals)
- Small bonus quizzes (1-2, NOT counted in total_quizzes)
- Short dialogues with characters
- Environmental observations

### What branches MUST NOT contain (plot-critical)

- Key plot twists or reveals
- Information required to understand the next scene
- Character introductions (first appearance of a named character)
- Quiz answers or term definitions needed for main line quizzes
- Flags that gate future main-line scenes (unless also settable on main line)

### Merge Point Validation

At every `merge_to` target scene, check:

1. **Read the merge target scene.** Does it reference any fact, character,
   or item that was ONLY introduced in the branch?
   - YES → ERROR. Move that info to main line, or remove the reference.
   - NO → OK.

2. **Read forward 3 scenes from merge.** Same check.
   - If main line says "Марко вспомнил карту" but the map was only
     shown in a branch → ERROR.

3. **Check flags.** If a branch sets a flag, that flag must EITHER:
   - Be purely cosmetic (changes a line of dialogue later, not gates a scene)
   - OR be settable on the main line too

### Branch Quiz Rules

- Branches CAN contain 1-2 bonus quizzes
- These quizzes are NOT counted in `total_quizzes` from the day plan
- They use previously introduced terms only (no new terms in branches)
- They follow the same format as main line quizzes
- `next_fail` loops back to the same quiz scene (soft fail)
- The quiz result does NOT affect the merge point

## Scene ID Naming

Branch scenes use the parent scene ID + suffix:

| Pattern | Naming |
|---------|--------|
| Single path | `ep001_s03d1`, `ep001_s03d2`, `ep001_s03d3` |
| Fork path A | `ep001_s03a1`, `ep001_s03a2` |
| Fork path B | `ep001_s03b1`, `ep001_s03b2` |

## YAML Structure for Choice + Branch

```yaml
# Choice point
- scene_id: ep001_s03
  scene_type: narrative
  interaction_type: choice
  question: "Что делает Марко?"
  options:
    - id: explore
      text: "Осмотреть комнату"
      next: ep001_s03d1
    - id: continue
      text: "Идти дальше"
      next: ep001_s04
  next_default: ep001_s04

# Branch scene 1
- scene_id: ep001_s03d1
  scene_type: narrative
  branch_type: flavor_detour
  author_text: "..."
  next_default: ep001_s03d2

# Branch scene 2 (last in branch)
- scene_id: ep001_s03d2
  scene_type: dialogue
  branch_type: flavor_detour
  dialogue: [...]
  merge_to: ep001_s04
  next_default: ep001_s04
```

## Validation

After writing branches:

1. Run `python3 tools/validate_gameflow.py` — fix ERRORS
2. Run `python3 tools/build_game.py` — rebuild HTML
3. Verify main line quiz counts unchanged
4. **Run qa-branches skill** — check information continuity

## Constraints

- DO NOT add branches inside phone chains (quiz sequences)
- DO NOT move main line content into branches
- DO NOT add new terms or term definitions in branches
- DO NOT create branches deeper than 3 scenes
- DO NOT create branches that skip main line scenes (branches are ADDITIONS)
- CAN add 1-2 bonus quizzes per branch (not counted in total)
- CAN add dialogues, observations, emotional beats
- CAN set cosmetic flags in branches
- CAN use any of the 7 branch patterns
