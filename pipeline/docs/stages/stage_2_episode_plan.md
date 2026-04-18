# Step 2 — Episode Plan (detailed episode plans)

Two-pass mapping of lesson blocks to the plot.
Pass 1: rough grid (step 1, completed).
Pass 2: detailed episode plans (this step).

## Why

The grid gave us: "Day 3 = episodes 9-12, blocks 3A.1, 3A.2, 3B.1+3B.2, 3B.3, source ep.7-8."
Episode Plan gives us: what specifically happens scene by scene — drama, sofa block,
challenge, cliffhanger, quiz distribution.

## Input

- `pipeline/source/grid.yaml` — rough grid (after QA)
- `pipeline/source/briefs/*.yaml` — all briefs (after QA)
- `source/` — plot (read-only)
- `pipeline/docs/style_profile.yaml` — style (if available)

## Output

- `pipeline/source/episodes/day_01.yaml` ... `pipeline/source/episodes/day_13.yaml`

## Skill

`.claude/skills/episode-plan/SKILL.md`
Invocation: `/episode-plan 3` (one day) or `/episode-plan all` (all days in parallel)

## What the episode plan does

### 1. Expands each episode into 4 parts

Each grid episode is expanded into a structure:
- **DRAMA** (3-4 min): plot, characters, conflict, gut feeling hint, Marko's flaw
- **SOFA BLOCK** (4-5 min): term introduction, quizzes, Sofa's rule, "real life" question
- **CHALLENGE** (5-6 min): application in action, plot quizzes
- **CLIFFHANGER** (1-2 min): twist, connector

### 2. Distributes quizzes

Votes are taken from briefs. Distribution:
- SOFA BLOCK: ~40% (theory + initial practice)
- CHALLENGE: ~60% (application)
- Target: 10-15 quizzes per episode
- If < 10 → add plot-based ones (marked as added)
- If > 15 → move to extra

### 3. Checks term order

A term cannot be used before its introduction. Episode plan checks:
- Order within the day (ep.1 → ep.2 → ep.3 → ep.4)
- Dependencies from previous days (terms_used)

## Parallelization

Days are independent → 13 sub-agents can be launched in parallel.
Each sub-agent works only with its own day:
- Reads its section of grid.yaml
- Reads only its briefs (day's lessons)
- Reads only its source_episodes

## Validation

### Before showing to the author (required)

**Term order check (CRITICAL):**
- [ ] For each episode — a cumulative terms_available list is built
- [ ] No quiz offers an answer option from a future term
- [ ] No explanation references a future term
- [ ] If ep.1 has only "fact, opinion" — quizzes are binary, without "falsehood"
- [ ] Sofa's rule uses only introduced terms

**Quiz check:**
- [ ] Each episode: 10–15 quizzes
- [ ] Extra quizzes are separated out
- [ ] Source of each quiz: brief (from brief) or added (plot-based)

### After approval — show to the author

1. Compact table: day / episode / terms_available / quizzes / story_beat
2. Issues: episodes with < 10 or > 15 quizzes
3. Term order check result: PASS or list of violations

## Status

- [x] Skill created: `.claude/skills/episode-plan/SKILL.md`
- [x] Template: `.claude/skills/episode-plan/templates/day_template.yaml`
- [ ] Episode plans — NOT CREATED
