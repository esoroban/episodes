---
name: deploy-episodes
description: "Копирует эпизоды из book/ в server/book/, коммитит и пушит в GitHub. Render подхватит автоматически."
trigger: "деплой эпизодов, deploy episodes, запуши эпизоды, обнови сервер"
---

# Deploy Episodes

Деплоит обновлённые эпизоды на Render через GitHub.

## Шаги

1. Скопировать все файлы из `book/` в `server/book/` (перезаписать):
   ```
   cp -r book/* server/book/
   ```

2. Перейти в `server/` и проверить изменения:
   ```
   cd server && git status
   ```

3. Если есть изменения — закоммитить и запушить:
   ```
   git add book/
   git commit -m "Update episodes"
   git push origin main
   ```

4. Render подхватит пуш автоматически — деплой займёт ~1-2 минуты.

## Важно

- Токен GitHub хранится в remote URL (настроен при инициализации)
- `.env` и `node_modules/` защищены `.gitignore`
- Если изменились файлы сервера (server.js, стили, шаблоны) — добавить их тоже
