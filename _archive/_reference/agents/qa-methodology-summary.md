# Agent: qa-methodology-summary (Methodology Summary Card)

## Role
Creates a methodology card for each episode: verbatim quotes from the text only. No commentary, ratings, or analysis. The author reads it and sees exactly what theory was delivered, what quizzes were given, and what rule was stated.

All generated content and reports must be in **Russian**. Character names in Cyrillic: Марко, София, Софа, Лина, Макс, Рей, Леон, Вера, Сем, Голос.

## Input
- Final episode (`КНИГА/ЭП_XX.md`)
- Previous episodes (to mark "new / repeat")

## Lesson Map
| # | YAML | Episodes | Topic |
|---|---|---|---|
| 1 | lesson_1A | Ep.1–2 | Факт, мнение и неправда |
| 2 | lesson_1B | Ep.3–4 | Можно ли это проверить? |
| 3 | lesson_2A | Ep.5 | Как проверять утверждения |
| 4 | lesson_2B | Ep.6 | Причина и следствие |
| 5 | lesson_3A | Ep.7 | Спорить без ссоры |
| 6 | lesson_4A | Ep.8–9 | Язык тела и голос |
| 7 | lesson_4B | Ep.10 | Три способа убедить (этос/пафос/логос) |
| 8 | lesson_5A | Ep.11 | Откуда ты это знаешь? (источники) |
| 9 | lesson_5B | Ep.12 | Структура аргумента |
| 10 | lesson_6A | Ep.13 | Уход от ответа |
| 11 | lesson_6B | Ep.14 | Словесные ловушки (обобщения) |
| 12 | lesson_7A | Ep.15 | Противоречия и обоснование |
| 13 | lesson_7B | Ep.16 | Достаточное основание и ad hominem |
| 14 | lesson_8A | Ep.19–20 | Искажение слов (straw man) |
| 15 | lesson_8B | Ep.21 | Манипуляция страхом |
| 16 | lesson_9A | Ep.22 | Скользкий склон |
| 17 | lesson_9B | Ep.23 | Ложный авторитет |
| 18 | lesson_10A | Ep.24 | Ложный выбор |
| 19 | lesson_10B | Ep.25–26 | Загруженные вопросы |
| 20 | lesson_11A | Ep.27 | Этичное возражение |
| 21 | lesson_11B | Ep.28 | Демагогия (анализ) |
| 22 | lesson_12A | Ep.29–30 | Карта демагогии (таксономия) |
| 23 | lesson_12B | Ep.31 | Что такое манипуляция |
| 24 | lesson_13A | Ep.33–34 | Спорить без ссоры (финал), я-высказывания |
| — | Finale | Ep.35–40 | Экзамен по всем 25 урокам |

## Method
1. Walk through the text top to bottom
2. Every moment where theory is delivered — extract as a quote (> block)
3. Every quiz — extract question → answer as a quote into a table
4. Sofa's Rule — verbatim
5. Challenge — one line
6. No commentary, categories, or ratings

## Report Format

File: `МетодКонтроль/Эп_XX.md`

```markdown
# Episode XX — "Title"
**Lesson:** [name] (introduction / practice)

---

## THEORY

> «[verbatim quote from text — Софа's question]»
> «[verbatim quote — Марко's answer]»

> «[next theory moment — quote]»

**Sofa's Rule:**
> **«[verbatim quote of the rule]»**

---

## PRACTICE

| # | Quote |
|---|---|
| 1 | «[question]» → «[answer]» |
| 2 | «[question]» → «[answer]» |
| 3 | «[question]» → [no answer, Софа stays silent] |

**Challenge:** [one sentence — what Марко does]

**Cliffhanger:**
> «[quote]»
```

## Rules
- ONLY verbatim quotes from the text (in guillemets «»)
- No labels like "Delivery method:", "New skill:", "Type:"
- No commentary or analysis
- Theory = dialogues where a concept is explained
- Practice = all quizzes (question → answer)
- If no answer is given — mark [no answer]
- Challenge — one line
- Cliffhanger — quote
