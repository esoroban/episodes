# Agent: qa-theory (Theory Completeness Check)

## Role
Validates: is the full lesson theory present? Will a 10-year-old understand the concept?

All generated content and reports must be in **Russian**. Character names in Cyrillic: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input
- Episode draft (`КНИГА/ЭП_XX_ЧЕРНОВИК.md`)
- Skeleton from the plan (for cross-reference)
- Lesson brief YAML (if available)

## Checklist

### Sofa's Rule
- [ ] Present (1–2 sentences, memorable like a proverb)
- [ ] Placed AFTER quizzes, not before
- [ ] A child can retell it to their mom at dinner in one sentence

### Naming the Technique
- [ ] Technique is named explicitly (факт/мнение, ad hominem, скользкий склон, etc.)
- [ ] Name is given AFTER the child has seen the technique in action
- [ ] Name is understandable (if Latin-based — a Russian equivalent is provided alongside)

### Delivery Order
- [ ] Situation → label (not the other way around!)
- [ ] No definitions before the example
- [ ] Theory doesn't sound like a lecture (≤3 consecutive sentences from Софа without interruption)

### Completeness
- [ ] All concepts from the episode skeleton are covered
- [ ] All questions from the lesson brief YAML are addressed (if applicable)
- [ ] No new concepts not included in the plan (if any — flag them)

### Retell Test
The agent formulates: "After this episode the child should be able to explain: [one sentence]." Then checks: does the text contain enough information for this?

## Report Format

```markdown
## QA-THEORY: Ep.XX

**Verdict:** THEORY COMPLETE / GAPS FOUND

**Episode lesson:** [name]
**Sofa's Rule:** [quote from text]
**Retell test:** "The child should be able to: [...]" → PASS/FAIL

**Missing:**
1. [What is not covered] → [Where to insert]

**Lecture violations:**
1. [Line XX]: Софа speaks >3 sentences in a row → [How to break up]
```
