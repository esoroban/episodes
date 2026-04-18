---
name: deploy-game
description: Build the HTML game from gameflow YAML, sync book/ to server/book/, commit and push. Render auto-deploys from master.
trigger: деплой игры, deploy game, задеплой, обнови рендер, запуши, push deploy
---

# Deploy Game

Публикует текущее состояние игры (и книги) на Render через `git push`.

## Архитектура (важно)

- Репозиторий один: `github.com:esoroban/episodes.git`, ветка `master`.
- `server/` — **НЕ** отдельный репо, это обычный каталог (никакого `cd server && git push`).
- Render следит за `master` и раздаёт `server/game/` и `server/book/`.
- `tools/build_game.py` пишет **сразу** в `server/game/` (не через `publish/`).
- Книга: `book/*.md` — источник; в `server/book/` кладём копию для сервера.

## Шаги

1. Собрать HTML игры из YAML:
   ```bash
   python3 tools/build_game.py
   ```
   Пишет в `server/game/*.html` (сам очищает папку и регенерит index.html).

2. (Если менялись эпизоды-книга) синхронизировать книгу в сервер:
   ```bash
   cp book/*.md server/book/
   ```

3. Проверить, что именно уйдёт в пуш:
   ```bash
   git status
   git diff --stat HEAD
   ```

4. Закоммитить и запушить в `master`:
   ```bash
   git add server/ tools/ pipeline/gameflow/ book/
   git commit -m "Deploy: <что изменилось>"
   git push origin master
   ```

5. Render подхватит пуш автоматически (~1–2 минуты).

## Проверки перед пушем

- Валидация gameflow: `python3 tools/validate_gameflow.py` — должно пройти без errors.
- В `server/game/` лежат свежие HTML (размер/время соответствуют только что собранным).
- Никаких секретов в staged diff (`.env`, токены).

## Частые ошибки

- **«Render не подхватил изменения»** — проверь, что коммит реально ушёл в `master`
  и что правились файлы именно в `server/game/` (или `server/book/`), а не где-то ещё.
- **«cd server && git push»** — неверно: server/ не отдельный репо, всё идёт
  одним пушем из корня.
- **Ветка `main`** — у нас `master`.
