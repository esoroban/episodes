# Pipeline Rules — Связь gameflow с другими слоями

## Архитектура слоёв

```
pipeline/episodes/          ← source of truth (YAML планы эпизодов)
        ↓
pipeline/gameflow/episodes/ ← игровой scene-flow (этот слой)
        ↓
server/book/                ← человекочитаемый markdown
publish/game/               ← HTML-превью
pipeline/gameflow/visuals/  ← visual briefs для художки
```

## Отношение к pipeline/episodes

| Правило | Описание |
|---------|----------|
| Source of truth | `pipeline/episodes/day_*.yaml` — единственный источник сюжета и уроков |
| Ссылки обязательны | Каждая сцена в gameflow содержит `source_ref`, указывающий на блок в episodes |
| Не дублировать контент | Gameflow не повторяет полный текст из episodes — он структурирует его в сцены |
| Не противоречить | Gameflow не может менять сюжет, порядок терминов или quiz-логику из episodes |

## Что gameflow ДОБАВЛЯЕТ поверх episodes

1. **Разбиение на сцены** — episodes описывают блоки (drama, sofa_block, challenge), gameflow дробит их на отдельные экранные моменты.
2. **Навигация** — `next_default`, `next_fail`, `merge_to` — явный граф переходов.
3. **Ветвления** — soft fail loops, flavor detours (в episodes их нет).
4. **Visual briefs** — конкретные кадры для каждой сцены.
5. **UI-режимы** — `reading`, `quiz`, `choice`, `dialogue`.

## Что gameflow НЕ делает

- Не переписывает авторский текст — берёт из episodes/book.
- Не добавляет новые quiz — только структурирует существующие.
- Не создаёт новых сюжетных поворотов — только декоративные ветвления.
- Не определяет визуальный стиль — только описывает, что рисовать.

## Отношение к server/book

`server/book/ep_*.md` — развёрнутый авторский текст. Gameflow может ссылаться на него для полного текста сцен, но не зависит от него.

Направление: `episodes → gameflow → book` (gameflow не читает book).

## Отношение к publish/game

`publish/game/ep_*.html` — один из возможных рендеров gameflow. HTML генерируется из gameflow, не наоборот.

Направление: `gameflow → publish/game` (однонаправленная генерация).

## Именование

| Слой | Паттерн | Пример |
|------|---------|--------|
| episodes (source) | `day_NN.yaml` | `day_01.yaml` |
| gameflow | `ep_NNN.yaml` | `ep_001.yaml` |
| book | `ep_NNN.md` | `ep_001.md` |
| game HTML | `ep_NNN.html` | `ep_001.html` |

## Порядок работы при создании нового эпизода

1. **Читай** `pipeline/episodes/day_NN.yaml` — найди нужный эпизод.
2. **Читай** `server/book/ep_NNN.md` — возьми развёрнутый текст.
3. **Создай** `pipeline/gameflow/episodes/ep_NNN.yaml` — разбей на сцены.
4. **Проверь**: каждая сцена имеет `source_ref`, каждый quiz из source сохранён, навигация замкнута (нет висячих ссылок).

## Валидация

Gameflow-файл считается валидным, если:

- [ ] Все `scene_id` уникальны внутри файла
- [ ] Все `next_default`, `next_success`, `next_fail`, `merge_to` указывают на существующие `scene_id` (или `ep_NNN+1_s01` для перехода к следующему эпизоду)
- [ ] Каждая сцена имеет `source_ref`
- [ ] Каждая ветка имеет `merge_to`
- [ ] Quiz-сцены имеют `options` с хотя бы одним `correct: true`
- [ ] Нет висячих сцен (к каждой можно добраться из `ep_NNN_s01`)
