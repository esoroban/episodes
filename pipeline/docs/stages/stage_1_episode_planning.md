# Step 1 — Mapping Lessons to Existing Episodes

We don't write the story from scratch. We take the existing plot and decide which lesson weaves into which episode.

## Input
- `source/` — existing plot (read-only)
- `pipeline/source/briefs/brief_XX.yaml` — lesson briefs with blocks (from Step 0)

## Agents

### STORY-READER
Reads the existing story from `source/`, for each episode identifies:
- Who participates
- Where it takes place
- The conflict
- What themes already resonate (even without an explicit lesson)

### EPISODE-MAPPER
Maps lessons to existing episodes:
- For each lesson, finds the episode where its theme already resonates organically or can be easily woven in
- If a lesson doesn't fit any episode — the episode can be split in two or a new one can be added
- The number of episodes may change, but the goal is minimal changes to the existing structure

### QA-COVERAGE
Coverage check:
- Is every lesson mapped to an episode?
- Does every episode contain a lesson?
- Is the mapping organic (the lesson isn't just glued on the side)?

## Output
- `episodes/` — working copy of the plot with annotations: which lesson goes in which episode
- `coverage/coverage.md` — coverage map
