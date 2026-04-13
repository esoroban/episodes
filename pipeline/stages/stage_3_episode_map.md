# Step 3 — Episode Map (quiz and theory transplantation)

Takes generic lesson content and transplants it into the specific story context
of each episode. The bridge between episode structure (step 2) and final prose (step 4).

## Why

Episode plan says: "Episode 1 has 6 sofa quizzes and 9 challenge quizzes about fact/opinion."
Episode map says: "Quiz 1: 'Mom says you have no sister. Fact or opinion?' Answer: fact (verifiable)."

Without this step, writing would use generic examples (Vitya and the magic stone)
instead of story-specific ones (Mom and the missing sister).

## Input

- `pipeline/episodes/day_{NN}.yaml` — episode plans (from step 2)
- `pipeline/briefs/*.yaml` — lesson briefs
- `lessons_ru/*.yaml` — original quiz texts (read-only, ru keys only)
- `source/` — plot (read-only)
- `pipeline/grid.yaml` — terms and story beats
- `pipeline/style_profile.yaml` — style

## Output

- `pipeline/mapped/ep_{NNN}.yaml` (NNN = 001..050)

## Skill

`.claude/skills/episode-map/SKILL.md`
Invocation: `/episode-map 1` (one episode) or `/episode-map day 1` (all episodes of a day)

## What episode map does

### 1. Transplants quizzes

Each generic quiz from the brief gets a decision:
- **generic** — kept as-is (warmup, first contact with term)
- **story** — rewritten with story characters and current scene context
- **plot** — tied to the main storyline tension
- **added** — new quiz created for the story context

Distribution: sofa block ~40% (mix of generic + story), challenge ~60% (all story/plot).

### 2. Transplants theory delivery

How Sofa introduces each term:
- Which moment from the drama triggers the concept
- Generic story from the lesson: kept as analogy or replaced with scene
- Rule formulation tied to what Marko just experienced

### 3. Validates everything

Three critical checks before showing to author:
- **Term order**: only terms_available used in quiz options
- **Content correctness**: every answer unambiguous per lesson definitions
- **Spoiler check**: no future plot reveals in quiz content

## Parallelization

Episodes within a day are sequential (terms_available is cumulative).
Days are independent — can run in parallel.

## Status

- [x] Skill created: `.claude/skills/episode-map/SKILL.md`
- [x] Template: `.claude/skills/episode-map/templates/episode_map_template.yaml`
- [ ] Mapped episodes — NOT CREATED
