---
name: deploy-game
description: Build the HTML game from gameflow YAML, sync book/ to server/book/, commit and push. Render auto-deploys from main.
trigger: деплой игры, deploy game, задеплой, обнови рендер, запуши, push deploy
---

# Deploy Game

Публикует текущее состояние игры (и книги) на Render через `git push`.

## Архитектура (важно)

- Репозиторий один: `github.com:esoroban/episodes.git`, ветка `main`.
- `server/` — **НЕ** отдельный репо, это обычный каталог (никакого `cd server && git push`).
- Render следит за `main` и раздаёт `server/game/` и `server/book/`.
- `tools/build_game.py` пишет **сразу** в `server/game/` (не через `publish/`).
- Книга: `book/*.md` — источник; в `server/book/` кладём копию для сервера.

## Настройки Render-сервиса (обязательно)

Node.js-приложение живёт в подкаталоге `server/`, поэтому в дашборде Render
должны стоять:

| Настройка | Значение |
|-----------|----------|
| **Root Directory** | `server` |
| **Build Command** | `npm install` |
| **Start Command** | `node server.js` (или `npm start`) |
| **Branch** | `main` |

Без `Root Directory = server` билд упадёт с
`ENOENT: package.json` — Render будет искать `package.json` в корне репо,
где его нет. Это не чинится из репо — только из дашборда Render.

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

4. Закоммитить и запушить в `main`:
   ```bash
   git add server/ tools/ pipeline/gameflow/ book/
   git commit -m "Deploy: <что изменилось>"
   git push origin main
   ```

5. Render подхватит пуш автоматически (~1–2 минуты).

## Проверки перед пушем

- Валидация gameflow: `python3 tools/validate_gameflow.py` — должно пройти без errors.
- В `server/game/` лежат свежие HTML (размер/время соответствуют только что собранным).
- Никаких секретов в staged diff (`.env`, токены).

## Частые ошибки

- **«Render не подхватил изменения»** — проверь, что коммит реально ушёл в `main`
  и что правились файлы именно в `server/game/` (или `server/book/`), а не где-то ещё.
- **«cd server && git push»** — неверно: server/ не отдельный репо, всё идёт
  одним пушем из корня.
- **Ветка — только `main`**. `master` в репозитории нет (удалён). Если по привычке
  пишешь `git push origin master` — получишь `error: src refspec master does not match any`.
- **`Build failed: ENOENT package.json`** — у Render-сервиса сброшена настройка
  **Root Directory**. Должна быть `server`. Чинится только в дашборде Render
  (Settings → Build & Deploy → Root Directory → `server` → Save →
  Manual Deploy → Clear build cache & deploy). Коммитом в репо не решается.
