# Step 2-QA / Step 3-QA — QA Episodes (validation gate)

Independent validator agent. Checks outputs of episode-plan (step 2) and
episode-map (step 3) before allowing progression to the next step.

## Why

The generator agent and the validator agent must be separate.
Self-checking doesn't catch systematic blind spots (proven by pilot:
term-order and content-correctness bugs both passed the generator's
own checks).

## Gates

```
Step 2 (episode-plan) → qa-episodes plan → Step 3 (episode-map)
Step 3 (episode-map)  → qa-episodes map  → Step 4 (writing)
```

Without PASS, the pipeline does not proceed.

## Three Checks

1. **Term order** — cumulative terms_available, no future terms in quiz options/explanations
2. **Content correctness** — every answer unambiguous per lesson definitions
3. **Spoiler check** — no future plot reveals in story quizzes

## Invocation

- `/qa-episodes plan` — validate episode plans
- `/qa-episodes map` — validate episode maps
- `/qa-episodes all` — both
- `/qa-episodes plan day 1` — validate one day's plans

## Output

Verdict: PASS or FAIL with detailed error list.
No files modified — read-only validation.

## Status

- [x] Skill created: `.claude/skills/qa-episodes/SKILL.md`
- [ ] First run — NOT YET
