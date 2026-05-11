# DECISION LOG — author's decision journal

> Decisions made by the author. The agent does not challenge them without explicit request.
> Format: date | decision | rationale

---

## 2026-04-12

**The story is the foundation — we do not rewrite from scratch.**
The plot (Sofia's disappearance, the Mirror City, the Voice) is already good. We make two passes on top: style + lesson integration.

**Lessons are primary.**
Each episode must develop the lesson's topic. A lesson cannot be removed without breaking the plot.

**Number of episodes is flexible.**
Not fixed at 40. Determined by lesson needs — can be more or fewer.

**Use only ru keys from YAMLs.**
Lessons are trilingual (ru/en/uk), but we work in Russian. Translation is not needed.

**Repetition at the beginning of YAMLs — discard it.**
Often a lesson begins with a review of the previous one. We assign it to the previous lesson or ignore it.

**At least 80% of lesson exercises → into the episode.**
10-15 quizzes per episode.

**Russian text without Ukrainian letters.**
Letters i, yi, ye, g (і, ї, є, ґ) and Ukrainian name spellings are forbidden.

**Vera Andreevna → Vera.**
First mention is the full name, then simply Vera.

**Folders — lowercase English.**
All Russian folder names have been renamed to English lowercase.

**CLAUDE.md — core only.**
Pipeline, rules, details — in separate files under `pipeline/`.

**Pipeline is a draft for now.**
Do not hardcode it into CLAUDE.md. It will change as we work with agents and skills.

**Step 0: lesson briefs instead of cards.**
A lesson is split into theoretical blocks (1 block = 1 new concept + its exercises).
Each block becomes the basis for one episode. Skill: `/lesson-brief`.
Splitting rule: the boundary between blocks is where a new concept is introduced.
Inseparable pairs (fact + opinion) — one block. However many blocks result — that many episodes.

**Step 0.5: mapping lessons to the plot.**
Between the lesson brief and the episode brief, an intermediate layer is needed — transplanting examples from the lesson's generic world into Marko's world. Three principles:

1. Transplantation, not reinvention. Examples from the lesson are preserved as close to the original as possible. An argument about ice cream stays an argument about ice cream — just Marko and Max are arguing instead of generic kids. Change content only if it absolutely doesn't fit.

2. Character replacement. Generic children from the lesson → characters from our plot. Circumstances stay the same — school, recess, classroom. But it's Marko's school.

3. Plot quizzes — the majority. Most quizzes are tied to Marko's world.
   Structure: warmup (2-3 generic) → middle (4-6 plot-based) → finale
   (3-5 provocative from the main storyline). Generic content remains minimal — only
   for warmup at the beginning of a block.

**Mapping format — YAML in `pipeline/mappings/`.**
The document contains: character replacements, story adaptations, all quizzes split into warmup/middle/finale + spoiler_check for plot-based ones.

**Skill `/lesson-map`.**
Pipeline skill for creating mappings. Works on the Explore → Plan → Write cycle.
During the Plan phase, it asks the author specific validation questions.

**Character replacement rules.**
- Do not overload a single character excessively in one lesson.
- Main antagonists — only in finale quizzes.
- For minor roles — unnamed classmates (don't spend main characters).
- Lina — use carefully: don't portray her as unreliable too early.

**Plot quiz rules.**
- Don't spoil twists.
- Don't break characters before the plot does.
- Open-ended questions are more valuable than closed ones.
- Cumulative terms (only those already introduced).

**Episode limit: max 4 per day (A+B combined).**
13 days x 4 = 52 episodes maximum. Actually 70 blocks → merging needed.

**Two-pass mapping (option D).**
Pass 1 — rough grid (`/story-grid`): all blocks → days → story acts.
Pass 2 — detailed plan (`/episode-plan`): by day, in parallel.
Quiz mapping (`/lesson-map`) — AFTER episode-plan, not before grid.

**QA validation is mandatory after each mass step.**
Script `tools/qa_briefs.py`, skill `/qa-briefs`. Gate: cannot proceed without PASS.

**Skills in folder format.**
`.claude/skills/{skill-name}/SKILL.md` + `templates/` + `references/`.
Not flat files.

**Pipeline is universal.**
Must work with any plot + lessons. Skills are reusable.

**Term order — CRITICAL check in episode-plan.**
Bug during pilot: episode 1 contained quizzes with the option "untruth", but that term is only introduced in episode 2. The rule "a term cannot be used before introduction" was mentioned in 7 files but was never checked algorithmically. Fixed: in episode-plan/SKILL.md, a mandatory check algorithm with a cumulative terms_available list was added. The check runs BEFORE showing to the author, not after.

**Future-lesson leak check — third critical check.**
Bug during pilot QA: «если не съешь суп — заболеешь» was used in Day 1 as «неправда».
But this phrase is actually fear manipulation (lesson 8B) and a scary chain (lesson 9A).
Classifying it as simple «неправда» in Day 1 is a gross simplification — the child
doesn't have the tools to properly understand it yet. Rule: if an example requires
a concept from a FUTURE lesson for correct understanding — do not use it in the current
episode. Move it to the day where the right tool is introduced.
Source: the phrase exists in brief_1A.yaml (sc10 final quiz) as a deliberate trap.

**«Мой папа самый сильный» = неправда (confirmed by author).**
Can be measured with a strength meter → verifiable → not confirmed → неправда.

**Content correctness check — second critical check in episode-plan.**
Bug during pilot: Sofa says "'You're overtired' — you can verify with a doctor", but "overtired" is an opinion (there's no "tiredness meter"). Subjective assessments = ALWAYS opinion.
A check algorithm was added: each quiz and each explanation is checked for answer unambiguity against the lesson's definitions. Borderline cases — in favor of unambiguity. The check runs BEFORE showing to the author.

**Язык файлов: служебные — английский, вычитка — русский.**
Все служебные файлы (YAML, стейджи, скиллы, pipeline) — на английском.
Файлы для вычитки автором (HTML-ревью) — ТОЛЬКО на русском.
HTML-ревью включает навигацию с кнопками по эпизодам и секциям.

**`/lesson-map` replaced by `/episode-map`.**
lesson-map worked per lesson (1A → mapping_1A.yaml). But after episode-plan exists,
mapping needs to work per episode — because each episode has specific drama context
(who's in the scene, what conflict, what gut feeling). episode-map takes episode plan +
brief + source and produces mapped quizzes tied to the story scene, not generic examples.
Old lesson-map kept for reference but no longer in active pipeline.

**Генератор и валидатор — отдельные агенты.**
Проверять свою работу самому — плохо (доказано пилотом: два бага прошли мимо
собственных проверок генератора). `/qa-episodes` — отдельный агент-валидатор.
Два gate: после episode-plan (qa-episodes plan) и после episode-map (qa-episodes map).
Без PASS — пайплайн не продвигается.

**Skill `/episode-plan` created.**
Detailed episode plans for one day. Parallelizable by day (13 sub-agents).
Stage: `pipeline/stages/stage_2_episode_plan.md`.
Input: grid.yaml + day's briefs + source. Output: `pipeline/episodes/day_NN.yaml`.

---

## 2026-05-11 — Day 13 финал (ep_049 + ep_050)

**ep_049 — Сем заменён Софией в вечерней ссоре.**
Сем (8-летний младший с ep_017+) НЕ одноклассник и не родственник
Марко — ему нечего делать в чужой кухне. Семейный совет вечером:
Марко + София + мама. Спор «рассказывать ли всем» — это история
Софии, у неё право голоса требовать. Мама сидит рядом с Софией,
как взрослый-посредник.

**ep_049 s07 — дуэль с Реем (взрослый, около 30).**
Рей не подросток. В школу зашёл по делу. Пробует на Марко три
приёма за одну речь (поспешное обобщение, ложная дилемма, ложный
авторитет). Марко режет каждый по имени. Драма-перевал бывших
противников.

**ep_049 — мама не монстр.**
Старое «Я боялась за себя» → «Я боялась НЕ за себя — за Софию.
Голос мне сказал: будешь помнить — заберёт её насовсем. Я выбрала
забыть.» Мать — жертва торга, не предательница.

**ep_049 — Марко и София соседние парты.**
Близнецы 11 лет, одноклассники 5-Б с первого класса. Восстановлено
после ошибки «София этажом ниже».

**ep_050 — Сем → Данила в классе.**
Сем не одноклассник 5-Б. Заменён на Данилу (одноклассник из ep_001,
тот, кто сказал «тебе приснилось»). Закрытие арки скептик → союзник:
Данила первый встаёт рядом и узнаёт ложный авторитет на доске.

**ep_050 — PURE DRAMA без квизов.**
Финал сезона. Курс детям 8-12 завершён за 24 предыдущих урока.
47 сцен → 16, 2168 строк → 905.
- 8 battle-квизов свёрнуты в одну narrative s05.
- 8 sofa-блок квизов свёрнуты в одну сцену s07 (друзья дают опору
  фразами-спасателями в живом разговоре).
- 5 практик-вопросов свёрнуты в s12 (Марко рассказывает классу).
- Финальный quiz «сестра или гордость» убран.
- Никаких ответов от игрока. Cosmetic_branch на s06b для валидатора.

**ep_050 — шантаж переделан (стёртых уже нет).**
Стёртые возвращены в ep_048 (пароль → команда восстановления).
Утверждённый вариант D автора: Голос хочет ИМЯ Марко. «Когда приду
в другой город — позволь сказать "Я был у Марко. Марко согласен."»
Это ровно ЛОЖНЫЙ АВТОРИТЕТ — пятое имя на доске. Голос применяет
лично тот приём, который Марко только что разобрал. Данила
показывает на доску. Марко: «Имя — не торг и не гордость. Имя —
это я. И я тебе его не дам.» Голос уходит с угрозой «сделаю жизнь
опасной» — без имени Марко работать в других городах через слова
не сможет, только через ОПАСНОСТЬ. Мост в сезон 2.

**ep_050 — лейтмотив сменён.**
Старый «защитим Софию» закрыт в ep_048. Новый: «прогнать Голос,
чтобы он не захватил всех снова». София физически в классе (за
соседней партой, иммунитет — её уже стирали), говорит первой:
«Имя не продают. Прогоним его — паузой.» Соратник в битве, не приз.

**Рей переутверждён 30-летним.**
Image_pack.yaml (рендер) держал «about 30 years old». CLAUDE.md и
gameflow держали «15 лет». Автор утвердил 30.
Синхронизировано: CLAUDE.md:41, ep_014.yaml RU+UK, book/ep_014.md,
qa/needed_images.md, docs/rules/content_rules.md.
Read-only с устаревшим возрастом 15 (требуют ручной правки):
source/ПЕРСОНАЖИ.md, source/СИЛА_СЛОВА_40_ЭПИЗОДОВ.md,
pipeline/source/episodes/day_04.yaml, day_13.yaml,
pipeline/source/grid.yaml.

**ep_050 вопрос-ловушка переформулирован.**
Старая «Хотите, чтобы дети учились без присмотра?!» — риторический
вопрос. Новая: «Скажи всем — давно ты сбиваешь одноклассников с
толку?» — спрятано допущение «ты виноват».

**Бальная система оценок убрана.**
«Дети с пятёрками» → «счастливые дети». Бальные системы в странах
разные.

**Русский → английский в школе ep_049 s06.**
«Уроки: Русский. Математика.» → «Английский. Математика.» Действие
в нейтральной стране (для UK-аудитории русский как предмет
триггерит).

**Контраст drama-квизов фикс в build_game.py.**
CSS `.quiz-question { color: #000 }` → `.bubble .quiz-question`
(scoping к чат-пузырям). До фикса квизы вне чата (битва у доски)
рендерились чёрным на тёмном.
