# Gameflow Episodes

Рабочий каталог игровых scene-flow файлов.

## Формат

Один YAML-файл на эпизод:

```
ep_001.yaml
ep_002.yaml
...
ep_050.yaml
```

## Источник

Каждый файл создаётся на основе:
- `pipeline/episodes/day_NN.yaml` — структура и quiz
- `server/book/ep_NNN.md` — авторский текст

## Схема

См. `pipeline/gameflow/spec/gameflow_schema.md`

## Порядок создания

Эпизоды создаются последовательно, начиная с ep_001. Перед созданием нового эпизода предыдущий должен пройти валидацию.
