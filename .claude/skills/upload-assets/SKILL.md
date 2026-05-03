---
name: upload-assets
description: Uploads episode images and audio (combined_output) to the Cloudflare R2 bucket (sylaslovaassets). Use this whenever the user wants to publish a new episode's assets to R2 so that the v2 (combined) HTML game can load them from CDN. Argument — episode number, range (e.g. "ep 1-12"), or "all". Without argument — asks which episodes.
trigger: upload assets, залей ассеты, upload image and voice, upload to r2, залей в r2, upload ep, r2 upload, залей эпизод, upload combined, залей картинки и звук
---

# Upload Assets to Cloudflare R2

Заливает **картинки** и **аудио** одного или нескольких эпизодов в R2-бакет `sylaslovaassets`. После аплоада эти файлы доступны публично на CDN и используются HTML-эпизодами в v2-рендере (`server/v2/uk/`).

**Язык.** Текущий источник `combined_output` — **украинский**. В R2 ассеты лежат в плоской схеме `ep_NNN/...` (без префикса языка), потому что голоса и картинки сейчас существуют только в UK-версии. Если когда-нибудь появится RU-сборка (отдельные voice_prompts для RU) — надо будет перейти на `uk/ep_NNN/...` и `ru/ep_NNN/...` в бакете и пересобрать HTML с новыми путями.

## Когда используется

- После того как для эпизода собраны ассеты в `/Users/iuriinovosolov/Documents/image_prompts_experiment/combined_output/ep_NNN/`
- Перед тем как собирать v2-HTML (который ссылается на CDN URL)
- Для повторной заливки: rclone идемпотентен — одинаковые файлы пропускаются

## Архитектура

```
Локальные ассеты (симлинки)                     Cloudflare R2 (sylaslovaassets)
─────────────────────────────                   ─────────────────────────────────
combined_output/ep_NNN/images        ──┐        ep_NNN/images/ep001_s01.png
  → image_prompts_experiment/           ├── rclone ──→ ep_NNN/images/...
    output/ep_NNN/images               │
                                       │
combined_output/ep_NNN/audio         ──┤        ep_NNN/audio/ep001_s01_text_01.wav
  → voice_prompts_experiment/           ├── rclone ──→ ep_NNN/audio/...
    output/ep_NNN/audio                │
                                       │
combined_output/ep_NNN/chat_images   ──┤        ep_NNN/chat_images/ep001_s05_chat.png
  → image_prompts_experiment/           └── rclone ──→ ep_NNN/chat_images/...
    output/ep_NNN/chat_images
   (опционально — есть не у всех эпизодов)

Публичный URL:
  https://pub-77b6fd849494491a8cd26f9e0df3db3f.r2.dev/ep_NNN/images/...
  https://pub-77b6fd849494491a8cd26f9e0df3db3f.r2.dev/ep_NNN/audio/...
  https://pub-77b6fd849494491a8cd26f9e0df3db3f.r2.dev/ep_NNN/chat_images/...
```

**chat_images** (иконки внутри Telegram-чата) — отдельный слой ассетов,
возникает только в эпизодах, где Софа отправляет картинку-эскиз внутри
чата (вместо иллюстрации сцены). Combine-сборщик с 2026-05-03 симлинкает
`chat_images/` рядом с `audio/` и `images/`, поэтому стандартный rclone-цикл
ниже их подхватывает автоматически. Если у эпизода chat_images нет —
директории просто не будет, цикл `if [ -d ... ]` пропустит.

## Конфиг — источники правды

| Что | Где |
|-----|-----|
| Публичный URL, имя бакета, account id, endpoint | `pipeline/gameflow/spec/r2_config.yaml` (коммитится) |
| Access Key ID, Secret Access Key, API Token | `server/.env` (в .gitignore, локально) и Render Dashboard |
| Rclone remote `r2:` | `~/.config/rclone/rclone.conf` (локально, НЕ коммитится) |

Если `rclone.conf` отсутствует — создай его, прочитав ключи из `server/.env`:
```ini
[r2]
type = s3
provider = Cloudflare
access_key_id = <R2_ACCESS_KEY_ID из server/.env>
secret_access_key = <R2_SECRET_ACCESS_KEY из server/.env>
endpoint = <R2_ENDPOINT из server/.env>
acl = private
no_check_bucket = true
```

## Препчеки (перед запуском)

1. **Часы**: `sntp time.apple.com` — смещение должно быть < 15 секунд. S3 API режет запросы с большим skew-ом ("RequestTimeTooSkewed").
2. **rclone**: `rclone lsd r2:sylaslovaassets` — должен вернуть exit 0 (список каталогов; может быть пустым).
3. **Источник**: для каждого запрошенного эпизода проверь, что существуют реальные пути (следуй симлинкам):
   - `combined_output/ep_NNN/images` → `image_prompts_experiment/output/ep_NNN/images`
   - `combined_output/ep_NNN/audio` → `voice_prompts_experiment/output/ep_NNN/audio`
   - `combined_output/ep_NNN/chat_images` → `image_prompts_experiment/output/ep_NNN/chat_images` *(опционально)*

   Если симлинка `chat_images` нет, а в источнике директория есть — пересобери: `python -m factory combine ep_NNN`.

## Процесс (на один эпизод)

```bash
SRC=/Users/iuriinovosolov/Documents/image_prompts_experiment/combined_output
BUCKET=sylaslovaassets
NNN=001   # подставить

# Копируем, следуя симлинкам (-L), с прогрессом, параллельно
rclone copy "$SRC/ep_$NNN/images" "r2:$BUCKET/ep_$NNN/images" \
  --copy-links --transfers=8 --checkers=16 --progress

rclone copy "$SRC/ep_$NNN/audio"  "r2:$BUCKET/ep_$NNN/audio" \
  --copy-links --transfers=8 --checkers=16 --progress

# chat_images — заливаем только если симлинк есть (не у всех эпизодов)
if [ -d "$SRC/ep_$NNN/chat_images" ]; then
  rclone copy "$SRC/ep_$NNN/chat_images" "r2:$BUCKET/ep_$NNN/chat_images" \
    --copy-links --transfers=8 --checkers=16 --progress
fi
```

Для батча эпизодов — цикл `for NNN in 001 002 ... 012`.

## Пост-чек (после каждого эпизода)

```bash
# Сколько объектов залито
rclone ls "r2:$BUCKET/ep_$NNN/images" | wc -l
rclone ls "r2:$BUCKET/ep_$NNN/audio"  | wc -l
[ -d "$SRC/ep_$NNN/chat_images" ] && rclone ls "r2:$BUCKET/ep_$NNN/chat_images" | wc -l

# Сверить с локалью (должны совпасть)
ls "$SRC/ep_$NNN/images" | wc -l
ls "$SRC/ep_$NNN/audio"  | wc -l
[ -d "$SRC/ep_$NNN/chat_images" ] && ls "$SRC/ep_$NNN/chat_images" | wc -l
```

## Отчёт пользователю (обязательно)

После успешного аплоада вернуть:

1. **Счётчики**: сколько эпизодов / файлов / МБ залито.
2. **Sample URL** для проверки в браузере:
   `https://pub-77b6fd849494491a8cd26f9e0df3db3f.r2.dev/ep_001/images/ep001_s01.png`
3. **Dashboard URL** для визуальной проверки:
   `https://dash.cloudflare.com/11f288deeb77883244e15ded2e5c55d8/r2/default/buckets/sylaslovaassets/objects`
4. **Что дальше**: v2-HTML ещё не собран — пути в HTML пока относительные. Следующий шаг — скилл `build-v2` (когда будет).

## Известные ограничения и решения

- **WAV, не MP3.** Аудио пока грузим как .wav. Компрессия через ffmpeg будет добавлена, когда будет рабочий ffmpeg (на этой машине сломан x264-линковкой; `brew reinstall ffmpeg` чинит). После перехода на mp3 — HTML нужно пересобирать с новыми путями.
- **~60–80 МБ аудио на эпизод.** Аплоад 12 эпизодов = ~800 МБ, займёт 5–15 минут на обычном канале.
- **Идемпотентность.** Повторный запуск скилла для того же эпизода — rclone сравнит по размеру/времени и пропустит неизменённое.
- **Не удаляет**. Скилл только добавляет/обновляет. Удалять старые файлы руками через `rclone delete r2:sylaslovaassets/ep_NNN/...` или в дашборде.

## Prohibitions

- Не коммитить `rclone.conf`.
- Не коммитить `server/.env`.
- Не класть `Secret Access Key` в `pipeline/gameflow/spec/r2_config.yaml` — он публичный (коммитится).
- Не менять layout ключей (`ep_NNN/{images,audio}/<file>`) — на них завязан build v2-HTML.
