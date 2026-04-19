# COMPLETE RULES — эпизод YAML → HTML игра

Единый свод правил пайплайна. Здесь всё, чем мы пользуемся:
от исходников через gameflow YAML до рендера HTML и деплоя.

Если правило есть здесь — оно должно быть привязано к инструменту
(валидатор, скилл или рендер). Если привязки нет — это пробел,
его закрываем через новый Check или новый раздел в скилле.

---

## 1. Пайплайн: слои и направление

```
lessons_ru/*.yaml   ─┐
                     ├─► pipeline/source/episodes/day_NN.yaml  (source of truth)
source/ (сюжет)     ─┘         │
                               ▼
                 pipeline/gameflow/episodes/ep_NNN.yaml  (scene-flow)
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
  server/book/           server/game/          pipeline/gameflow/
  ep_NNN.md              ep_NNN.html            visuals/
  (markdown)             (игра)                 (брифы для художки)
```

- **Source of truth** — `pipeline/source/episodes/day_NN.yaml` + `lessons_ru/*.yaml`.
- **Направление однонаправленное**: source → gameflow → book/HTML.
- Gameflow НЕ читает book. Book — человекочитаемая копия, рендерится отдельно.
- Render раздаёт `server/game/` и `server/book/` — Root Directory на Render = `server`.

---

## 2. Язык и имена

Рабочий язык — **русский**. Украинский — только на стадии локализации.

**Имена персонажей:**

| Роль | Русский | Английский |
|---|---|---|
| Протагонист | Марко | Marko |
| Сестра | София | Sofia |
| ИИ в телефоне | Софа | Sofa |
| Двойной агент | Лина | Lina |
| Друг | Макс | Max |
| Антагонист-подросток | Рей | Ray |
| Профессор | Леон | Leon |
| Учительница | Вера Андреевна → Вера | Vera Andreevna → Vera |
| Младший | Сем | Sam |
| Антагонист | Голос | Voice |

**Запрещено:**
- Украинские буквы (і, ї, є, ґ) в русских текстах.
- Украинские формы имён (Віра, Олена вместо Олена — ОК, но Марко в русском не меняется).
- Смешение орфографий: Вера Андреевна, не Віра Андріївна.

---

## 3. Схема сцены (gameflow YAML)

### Поля уровня эпизода

| Поле | Тип | Обязательно | Заметки |
|---|---|---|---|
| `episode_id` | int | да | |
| `episode_title` | string | да | В русской орфографии |
| `lesson` | string | да | «1A.1», «1A.2» |
| `terms_introduced` | list[string] | да | Новые термины этого эпизода |
| `terms_used` | list[string] | да | Термины из предыдущих эпизодов |
| `enter_requires` | dict | опц. | `{flags: [], previous_episode: N}` |
| `previously` | — | **ЗАПРЕЩЕНО** | Check 13 падает на это |

### Поля сцены

| Поле | Тип | Обязательно | Значения |
|---|---|---|---|
| `scene_id` | string | да | `epNNN_sNN[суффикс]` |
| `episode_id` | int | да | |
| `source_ref` | string | да | `day_NN.epN.{block}` — Check 12 |
| `scene_type` | enum | да | narrative, dialogue, quiz, choice, feedback, transition, cliffhanger |
| `location` | string | да | «Школа, коридор» |
| `time` | string | да | «утро», «после школы» |
| `characters_present` | list | да | Кто на сцене |
| `next_default` | string | да* | Куда идти дальше (кроме cliffhanger) |
| `author_text` | string | опц. | Нарратив перед диалогом/квизом |
| `dialogue` | list[{who, line}] | опц. | Прямые реплики |
| `author_text_after` | string | опц. | Нарратив после квиза/диалога |
| `dialogue_after` | list[{who, line}] | опц. | Реплики после квиза |
| `mood` | string | опц. | «напряжение», «тихая радость» |
| `question` | string | для quiz | Формулировка вопроса |
| `options` | list[{id, text, correct?, next?}] | для quiz/choice | Варианты |
| `interactions` | list[dict] | опц. | Батч-квизы в одной сцене |
| `followup_interaction` | dict | опц. | Второй квиз после первого |
| `correct_logic` | string | для quiz | Объяснение (скрыто в UI) |
| `feedback_success` | string | для quiz | Реакция Софы на правильный |
| `feedback_soft_fail` | string | для quiz | Подсказка при ошибке |
| `next_success` | string | опц. | Явный переход при правильном |
| `next_fail` | string | опц. | Явный переход при ошибке (обычно сама сцена — soft fail) |
| `merge_to` | string | для веток | Куда схлопывается ветка |
| `branch_type` | enum | для веток | soft_fail_loop / flavor_detour / gated_response / cosmetic_branch — Check 14 |
| `set_flags` | list | опц. | Что эта сцена устанавливает |
| `require_flags` | list | опц. | Условия входа |
| `require_flags_absent` | list | опц. | Условия через отсутствие |
| `unlock_button` | dict | опц. | `{text, reveals: {type, who, line, duration}}` |
| `visual_brief` | dict | рекомендуется | Мета для художки |

---

## 4. Правила контента: кто говорит, кто слышит

### Софа — всегда Telegram-чат

**Правило:** если Софа в `characters_present` и говорит где-либо
(`dialogue`, `dialogue_after`, `interactions`, `followup_interaction`,
`unlock_button`) — сцена ОБЯЗАТЕЛЬНО рендерится как Telegram-чат.
Софа никогда не появляется в drama-режиме.

**Почему:** Софа — ИИ в треснутом телефоне. У неё нет голоса,
она только текст на экране.

**Запреты в репликах Софы** (Check 9):
- «слышишь», «услышишь», «слышно», «треск», «электронный», «шипение»
- «голос Софы», «мой голос», «твой голос»
- Вместо: «читаешь», «видишь», описание поведения экрана.

**Запрет утечки в нарратив** (Check 10):
- Любое «Софа: ...» в `author_text` или `author_text_after` = ERROR.
- Реплики Софы ТОЛЬКО в `dialogue`, `dialogue_after`, `unlock_button.reveals`.

**Префикс в feedback** (Check 7):
- Не писать «Софа: «...»» в `feedback_success`/`feedback_soft_fail`.
  Рендерер сам прикрепит реплику к имени Софы — получится тавтология.

### Автор — всегда voice-over

- `who: автор` в `dialogue` → voice-over карточка между пузырями чата.
- `author_text` в чат-сцене → voice-over плашка в ленте.
- `author_text` в драма-сцене → курсивный абзац на экране (для озвучания).
- Автор никогда не виден как персонаж в интерфейсе.

### Марко — условный канал

- Софа в сцене → Марко пишет в чат (text-пузырь).
- Софы в сцене нет → Марко говорит вслух (voice-over).

### Остальные персонажи — всегда voice

Лина, Макс, Вера, Леон, Рей, Сем, мама, одноклассники — всегда озвучка.
Никогда в чате как пузыри.

### voice_message — исключение

`unlock_button.reveals.type: voice_message` разблокирует голосовое
от Софии (не Софы) или от другого персонажа.

**Обязательные поля** (Check 8):
- `who` — кто говорит
- `line` — субтитр (для вычитки до записи)
- `duration` — секунды («0:03» или просто 3)

---

## 5. Ветвления

### Четыре разрешённых типа (Check 14)

| Тип | Когда | Глубина | merge_to |
|---|---|---|---|
| `soft_fail_loop` | игрок ошибся на квизе | 1 сцена | возврат к тому же вопросу |
| `flavor_detour` | выбор «осмотреться / поговорить» | 1–3 сцены | следующий узел main line |
| `gated_response` | флаг меняет одну реплику | 0 (разные варианты dialogue) | общий next |
| `cosmetic_branch` | выбор влияет на тон, не на сюжет | 0 (только set_flags) | общий next |

### Что МОЖНО в ветке

- Атмосфера, лор, эмоциональные детали.
- Характерные особенности персонажей.
- 1–2 бонус-квиза (не в `total_quizzes`).
- Косметические флаги (меняют строчку дальше, но не гейтят сцены).

### Что НЕЛЬЗЯ в ветке (qa-branches)

- Сюжетные повороты, которые нужны на main line.
- Первое появление персонажа (Check 5 падает, если Марко увидит Лину
  только в ветке — те, кто пропустят, потеряются).
- Введение нового термина.
- Флаг, который гейтит main-line сцену (если не настраивается и на main).

### Замкнутость

- Каждая ветка имеет `merge_to` — существующую сцену на main line.
- Последняя сцена ветки: `next_default = merge_to`.
- Глубина ≤ 3 сцен.
- Главная линия самодостаточна без ветки.

Проверяется скиллом **qa-branches**.

---

## 6. Рендер YAML → HTML (tools/build_game.py)

### Определение режима сцены

```
is_sofa_chat_scene(scene):
  Софа ∈ characters_present  И
  (dialogue ∨ dialogue_after ∨ unlock_button ∨
   quiz_options_with_correct ∨ interactions_with_correct ∨
   followup_with_correct)
  → Telegram-режим

иначе → drama-режим
```

### Telegram-режим

- iPhone-подобный фрейм. Имя «Софа», аватарка, синий хедер.
- Сообщения появляются по одному, typing-анимация.
- **Входящие** (от Софы): серый пузырь слева.
- **Исходящие** (Марко в ответ): синий пузырь справа.
- **Автор**: system-message по центру, курсив.
- **Voice-over других**: карточка `.voice-row` (тёмный фон, имя, italic-текст, иконка микрофона, длительность).

### Phone chains

Подряд идущие Софа-сцены на одной локации сливаются в одну цепь —
один экран Telegram, одна шапка, прокрутка чата.

- Разрыв цепи: смена `location`, Софа ушла из `characters_present`,
  `branch_type` появился.
- **Количественного лимита длины цепи нет.** Пока идёт Софа и драма
  не требует разрыва — цепь любой длины.
- soft_fail_loop и flavor_detour поглощаются в цепь (их контент уже
  встроен в quiz-JSON как wq:true feedback messages).

### Квиз = Telegram-бот inline keyboard

- Вопрос → серый пузырь от Софы.
- Варианты → кнопки под пузырём (синие `#3390ec`).
- Тап → правильный зелёный `#4caf50`, неправильный красный `#ef5350`.
- После ответа: `feedback_success` (правильно) или `feedback_soft_fail` (ошибка)
  → новый пузырь Софы.
- `correct_logic` НЕ рендерится в чат — хранится в скрытом `quiz-explanation`
  для автора/QA.

### Drama-режим

- Отдельный экран на место будущей иллюстрации.
- `author_text` → курсивный абзац (`.author-text p { font-style: italic }`).
- Диалог персонажей → реплики с подписями.
- `visual_brief` → скрытый блок, раскрывается кнопкой для художки.

### voice_message

- Кнопка разблокировки в чате.
- После тапа: плашка с длительностью, play-иконкой, `line` как субтитр
  (видим в debug, скрыт в production).

---

## 7. Автоматическая валидация (`python3 tools/validate_gameflow.py`)

**14 проверок.** При ошибке деплой не проходит.

| # | Чек | Что ловит |
|---|---|---|
| 1 | DUPLICATE KEY | Дубликаты ключей в YAML |
| 2 | BROKEN LINK | `next_default` / `next_fail` / `merge_to` → несуществующая сцена |
| 3 | UNREACHABLE | Сцена, до которой нельзя дойти из `s01` |
| 4 | UNUSED FLAG | `set_flags` без парного `require_flags` (warning) |
| 5 | CHARACTER NO INTRO | Персонаж в `characters_present` без введения |
| 6 | QUIZ NO CORRECT | Квиз без ни одной `correct: true` опции |
| 7 | FEEDBACK PREFIX | «Софа: ...» в `feedback_success` / `feedback_soft_fail` |
| 8 | VOICE_MESSAGE INCOMPLETE | `voice_message` без `who` / `line` / `duration` |
| 9 | SOFA VOICE VIOLATION | Софа описывает звук («слышишь», «треск») |
| 10 | SOFA LEAK | «Софа: ...» в `author_text` / `author_text_after` |
| 11 | NAME LEAK (cross-ep) | Персонаж упомянут ДО первого появления в `characters_present` |
| 12 | NO SOURCE_REF | Сцена без `source_ref` |
| 13 | PREVIOUSLY FORBIDDEN | Блок `previously:` в эпизоде |
| 14 | INVALID BRANCH_TYPE | `branch_type` ∉ 4 разрешённых значений |

Плюс cross-episode: глобально неиспользуемые флаги (warning).

---

## 8. Карта скиллов: когда что вызывать

Два режима работы:

**Новый курс с нуля** — полный путь от уроков:
**Активная работа с SylaSlovaDramma** — начинаем с `gameflow-build`
(планы 50 эпизодов уже лежат в `pipeline/source/episodes/day_*.yaml`).

```
═══ LEGACY (неактивно для SylaSlovaDramma, архив для новых курсов) ═══
lesson-brief  →  lesson-map  →  story-grid  →  episode-plan  →  episode-map
                                                                       │
═══ АКТИВНЫЙ ПАЙПЛАЙН ═════════════════════════════════════════════════
                                                                       ▼
                                                              gameflow-build
                                                                       │
                                                                       ▼
                                                              gameflow-drama
                                                                       │
                                                                       ▼
                                                             gameflow-branch
                                                                       │
                                                       ┌───────────────┼───────────────┐
                                                       ▼               ▼               ▼
                                                qa-references    qa-branches     qa-episodes
                                                       │               │               │
                                                       └───────────────┼───────────────┘
                                                                       ▼
                                                             validate_gameflow.py
                                                                       │
                                                                       ▼
                                                              build_game.py
                                                                       │
                                                                       ▼
                                                              deploy-game
```

| Скилл | Триггер-фраза | Когда запускать |
|---|---|---|
| `lesson-brief` | «lesson brief», «brief 1A.1» | Урок → бриф блока |
| `lesson-map` | «lesson map» | Бриф → привязка к сюжету |
| `story-grid` | «story grid» | Раскидать блоки по дням |
| `episode-plan` | «episode plan», «plan day 2» | День → YAML-план эпизода |
| `episode-map` | «episode map» | Привязать квизы к сюжетным триггерам |
| `gameflow-build` | «gameflow», «build day N» | План → первичный gameflow YAML |
| `gameflow-drama` | «restore drama», «fix drama» | Вернуть драму из book, если ушла |
| `gameflow-branch` | «add branches» | Добавить ветвления |
| `qa-references` | «qa references» | После любой правки текста |
| `qa-branches` | «qa branches» | После gameflow-branch |
| `qa-episodes` | «qa episodes» | Финальный контент-QA |
| `qa-briefs` | «qa briefs» | После lesson-brief |
| `deploy-game` | «deploy» | После всех QA |

Триггер-фразы — в `description:` файла `SKILL.md` каждого скилла.

---

## 9. Deploy

### Архитектура

- Один репозиторий: `github.com:esoroban/episodes.git`, ветка `main`.
- `server/` — обычный каталог в репо, не отдельный remote.
- `tools/build_game.py` пишет напрямую в `server/game/`.
- Render следит за `main`, раздаёт `server/game/` и `server/book/`.

### Настройки Render (обязательно)

| Параметр | Значение |
|---|---|
| Root Directory | `server` |
| Build Command | `npm install` |
| Start Command | `node server.js` |
| Branch | `main` |

Без `Root Directory = server` падает с `ENOENT: package.json`.
Чинится только в дашборде Render.

### Команды деплоя

```bash
python3 tools/validate_gameflow.py          # должно быть ALL PASS
python3 tools/build_game.py                 # собирает server/game/*.html
cp book/*.md server/book/                   # если менялась книга
git add server/ tools/ pipeline/gameflow/ book/
git commit -m "Deploy: <что изменилось>"
git push origin main                        # Render подхватит за 1–2 мин
```

---

## 10. Запреты (короткий список)

1. **`previously:` блоки** — игрок только что прошёл предыдущий эпизод.
2. **«Софа: ...» в `author_text*`** — реплики Софы только в dialogue.
3. **Софа описывает звук** — у Софы нет голоса.
4. **Префикс «Софа: ...» в feedback** — рендерер прикрепит сам.
5. **voice_message без line/duration** — субтитр нужен для вычитки.
6. **Персонаж в тексте до первого появления** — ни по имени, ни как реплика.
7. **Термин до `terms_introduced`** — теория всегда перед квизом.
8. **Lesson-характеры как known** — Дмитрик, Витя и т.д. рассказываются
   заново, никаких «помнишь?».
9. **Квиз без правильного ответа** — минимум один `correct: true`.
10. **Broken links** — `next_default` / `merge_to` должны существовать.
11. **Unreachable сцены** — каждая сцена достижима из `s01`.
12. **Первое появление персонажа в ветке** — только на main line.
13. **Plot-critical информация в ветке** — ветка = атмосфера, не сюжет.
14. **Новый термин в ветке** — только в main line.
15. **Количественный лимит на phone chain** — нет лимита. Разрыв только
    когда драма требует сюжетно.
16. **Другие персонажи в Telegram-чате** — только Софа, Марко и автор.
17. **Изобретение квизов** — квизы только из `day_NN.yaml`.
18. **Пропуск контента из book** — 100% переносим; опускать нельзя.
19. **Редактирование `source/`, `lessons_ru/`, `vision_lock.md`** —
    read-only.
20. **Украинские буквы в русском тексте** — только русская орфография.

---

## 11. Где искать что

| Нужно | Где |
|---|---|
| Изменить правило доставки (voice/text) | `pipeline/gameflow/spec/pipeline_rules.md` + валидатор |
| Изменить схему сцены | `pipeline/gameflow/spec/gameflow_schema.md` |
| Добавить тип ветвления | `pipeline/gameflow/spec/branching_rules.md` + Check 14 в валидаторе |
| Изменить рендер | `tools/build_game.py` |
| Добавить авто-проверку | `tools/validate_gameflow.py` |
| Новый скилл | `.claude/skills/<name>/SKILL.md` |
| Переделать деплой | `.claude/skills/deploy-game/SKILL.md` |
| Карта правило → инструмент | этот файл (COMPLETE_RULES.md) |
| Будущие слои (image/voice промпты) | `pipeline/gameflow/spec/ROADMAP.md` |

Если правило применяется, но здесь его нет — добавить сюда
и привязать к инструменту. Недокументированных правил быть не должно.

---

## 12. Будущее (см. ROADMAP.md)

HTML — **текущий** рендер, но не единственный будущий. На горизонте:

- **Image prompts** для drama-сцен → Google image-модель.
- **Voice prompts** (text + эмоциональная директива) → современные TTS.
- Эти слои становятся новым **источником истины**; HTML превращается
  в один из равноправных рендеров, а не единственный выход.

Чтобы переезд был дешёвым, уже сейчас: `mood` заполняется всегда,
`visual_brief` обязателен для drama, «как сказать» (эмоция/тон) хранится
отдельным полем, не в строке реплики.

Детали и что пока НЕ делать — [ROADMAP.md](ROADMAP.md).
