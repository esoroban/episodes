# Gameflow Schema — Спецификация игровой сцены

## Что такое gameflow

Gameflow — промежуточный слой между `pipeline/episodes` (source of truth) и рендерами (`publish/game`, visual briefs и др.). Он описывает эпизод не как текст, а как последовательность **игровых сцен** с чёткой структурой: кто, где, что происходит, какой выбор, куда дальше.

## Поля уровня эпизода

Каждый YAML-файл начинается с метаданных эпизода:

| Поле | Тип | Описание |
|------|-----|----------|
| `episode_id` | int | Номер эпизода |
| `episode_title` | string | Название |
| `lesson` | string | Урок: `1A.1`, `1B.2` |
| `terms_introduced` | list[string] | Новые термины, вводимые в этом эпизоде |
| `terms_used` | list[string] | Термины из предыдущих эпизодов |
| `enter_requires` | object | Требования для входа в эпизод (см. ниже) |
| `previously` | string | Краткий recap предыдущих событий для standalone preview |

### enter_requires

Определяет, что должно быть выполнено перед запуском этого эпизода.

```yaml
enter_requires:
  flags: [sofa_activated]      # обязательные флаги из предыдущих эпизодов
  previous_episode: 1          # номер предыдущего эпизода
```

Если эпизод 1 — `enter_requires` не нужен.

### previously

Текстовый recap для случаев, когда эпизод открывается отдельно (standalone preview, тестирование, jump-in). Описывает ключевые события, без которых сцены эпизода не имеют смысла.

## Единица слоя — сцена (scene)

Один YAML-файл на эпизод содержит массив сцен. Каждая сцена — один «экран» или «момент» игры.

## Обязательные поля сцены

| Поле | Тип | Описание |
|------|-----|----------|
| `scene_id` | string | Уникальный ID: `ep001_s01`, `ep001_s02_fail` |
| `episode_id` | int | Номер эпизода |
| `source_ref` | string | Ссылка на блок в `pipeline/episodes`: `day_01.ep1.drama`, `day_01.ep1.sofa_block` |
| `scene_type` | enum | `narrative`, `dialogue`, `quiz`, `choice`, `feedback`, `transition`, `cliffhanger` |
| `location` | string | Где происходит: `Квартира Марко, комната` |
| `time` | string | Время суток / время в истории: `утро`, `после школы` |
| `characters_present` | list[string] | Кто на экране: `[Марко, Софа]` |
| `next_default` | string | ID следующей сцены по умолчанию |

## Контентные поля (минимум одно обязательно)

| Поле | Тип | Описание |
|------|-----|----------|
| `author_text` | string | Авторский текст (описание, нарратив, внутренний монолог) |
| `dialogue` | list[object] | Реплики: `[{who: Марко, line: "Мам, где фотки?"}]` |
| `mood` | string | Эмоциональная окраска: `тревога`, `надежда`, `напряжение` |

## Поля взаимодействия (опциональны)

Простой случай — одно взаимодействие на сцену:

| Поле | Тип | Описание |
|------|-----|----------|
| `interaction_type` | enum | `vote`, `choice`, `open_question`, `none` |
| `question` | string | Вопрос к игроку |
| `options` | list[object] | Варианты: `[{id: a, text: "Факт", correct: true}, ...]` |
| `correct_logic` | string | Пояснение правильного ответа |
| `feedback_success` | string | Реакция на правильный ответ |
| `feedback_soft_fail` | string | Реакция на ошибку (мягкий тупик) |

### Несколько взаимодействий в одной сцене

Если в сцене сначала quiz, потом choice (или наоборот), используй `interactions` list.
**ВАЖНО:** YAML не допускает дублирование ключей. Нельзя писать два `interaction_type` или два `options` в одном маппинге.

```yaml
interactions:
  - interaction_type: vote
    question: "Факт или мнение?"
    options:
      - {id: a, text: "Факт", correct: true}
      - {id: b, text: "Мнение", correct: false}
    correct_logic: "..."
    feedback_success: "..."
    feedback_soft_fail: "..."
  - interaction_type: choice
    question: "Что делать дальше?"
    options:
      - {id: x, text: "Осмотреть", next: ep001_s03_detour}
      - {id: y, text: "Идти дальше", next: ep001_s04}
```

Альтернатива — `followup_interaction` для вторичного взаимодействия:

```yaml
interaction_type: vote
question: "..."
options: [...]
followup_interaction:
  interaction_type: choice
  question: "..."
  options: [...]
```

### Дополнительный авторский текст после диалога

Если между диалогом и quiz нужен авторский текст, используй `author_text_after`:

```yaml
author_text: "Текст ДО диалога."
dialogue: [...]
author_text_after: "Текст ПОСЛЕ диалога, перед quiz."
```

## Поля навигации (опциональны)

| Поле | Тип | Описание |
|------|-----|----------|
| `next_success` | string | Куда при правильном ответе (если отличается от default) |
| `next_fail` | string | Куда при ошибке (soft fail loop) |
| `merge_to` | string | Куда сливается ветка обратно в main line |
| `branch_type` | enum | `soft_fail_loop`, `flavor_detour`, `gated_response`, `cosmetic_branch` |

## Поля флагов (опциональны)

| Поле | Тип | Описание |
|------|-----|----------|
| `set_flags` | list[string] | Флаги, которые ставятся: `[marko_found_diary]` |
| `require_flags` | list[string] | Флаги, необходимые для доступа к сцене |

## Visual brief (опционально, но рекомендуется)

| Поле | Тип | Описание |
|------|-----|----------|
| `visual_brief.background` | string | Задний план: `Комната Марко, утренний свет` |
| `visual_brief.camera` | string | Ракурс: `close-up`, `wide`, `over-shoulder` |
| `visual_brief.characters` | list[object] | `[{who: Марко, expression: растерянность, pose: сидит на кровати}]` |
| `visual_brief.props` | list[string] | Важные предметы: `[пустые рамки, телефон с трещиной]` |
| `visual_brief.focus_object` | string | На чём фокус: `треснутый телефон` |
| `visual_brief.atmosphere` | string | Общее ощущение: `тихое утро, что-то не так` |
| `visual_brief.ui_mode` | string | Режим UI: `reading`, `quiz`, `choice`, `dialogue` |

## Допустимые значения enum

### scene_type
- `narrative` — авторский текст, описание
- `dialogue` — диалог между персонажами
- `quiz` — вопрос с вариантами ответа
- `choice` — выбор игрока (не quiz, а сюжетный)
- `feedback` — реакция системы на действие игрока
- `transition` — переход между локациями / сценами
- `cliffhanger` — финал эпизода

### interaction_type
- `vote` — голосование (факт/мнение/неправда)
- `choice` — сюжетный выбор
- `open_question` — открытый вопрос (будущее)
- `none` — нет взаимодействия

### branch_type
- `soft_fail_loop` — ошибся → подсказка → вернулся
- `flavor_detour` — бонусная сцена/атмосфера
- `gated_response` — разная реакция по флагу, один следующий узел
- `cosmetic_branch` — меняется тон, но не структура

## Именование файлов

```
pipeline/gameflow/episodes/ep_001.yaml
pipeline/gameflow/episodes/ep_002.yaml
...
```

## Пример минимальной сцены

```yaml
- scene_id: ep001_s01
  episode_id: 1
  source_ref: day_01.ep1.drama
  scene_type: narrative
  location: "Квартира Марко, комната"
  time: "утро"
  characters_present: [Марко]
  author_text: >
    Марко открывает глаза. Кровать напротив — пуста.
  mood: "тревога"
  next_default: ep001_s02
  visual_brief:
    background: "Детская комната, утренний свет сквозь шторы"
    camera: "close-up"
    characters:
      - who: Марко
        expression: сонная растерянность
        pose: сидит на кровати
    props: [пустая кровать напротив, пустые рамки на стене]
    atmosphere: "тихо, но что-то не так"
    ui_mode: reading
```
