#!/usr/bin/env python3
"""
QA-скрипт для валидации брифов уроков (шаг 0).
Сравнивает данные из YAML-уроков с данными из брифов.

Проверки:
1. Полнота votes — все vote-шаги из YAML попали в бриф
2. Блоки без терминов — подозрительные (чистая практика)
3. Пустые поля — summary, key_material
4. Общая сводка
"""

import yaml
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LESSONS_DIR = ROOT / "lessons_ru"
BRIEFS_DIR = ROOT / "pipeline" / "briefs"


def count_votes_in_yaml(lesson_path: Path) -> dict:
    """Считает vote-шаги в YAML-уроке."""
    with open(lesson_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    lesson = data.get("lesson", data)
    scenes = lesson.get("scenes", [])

    total_votes = 0
    scene_votes = {}

    for scene in scenes:
        scene_id = scene.get("scene_id", "?")
        steps = scene.get("steps", [])
        votes = sum(
            1
            for s in steps
            if s.get("type", "").startswith("vote")
        )
        scene_votes[scene_id] = votes
        total_votes += votes

    return {
        "total_votes": total_votes,
        "scene_votes": scene_votes,
        "scene_count": len(scenes),
    }


def parse_brief(brief_path: Path) -> dict:
    """Парсит бриф урока."""
    with open(brief_path, "r", encoding="utf-8") as f:
        # Пропускаем строки-комментарии перед YAML
        content = f.read()

    data = yaml.safe_load(content)
    if data is None:
        return {"blocks": [], "total_votes": 0, "terms": []}

    blocks = data.get("blocks", [])
    total_votes = 0
    terms = []
    block_info = []
    issues = []

    for block in blocks:
        block_id = block.get("id", "?")
        block_title = block.get("title", "?")
        votes = block.get("votes", 0)
        total_votes += votes

        block_terms = block.get("terms_introduced", [])
        terms.extend(block_terms)

        # Проверка: блок без терминов
        if not block_terms or block_terms == []:
            issues.append(f"  WARN: блок {block_id} без новых терминов")

        # Проверка: пустой summary
        summary = block.get("summary", "")
        if not summary or summary.strip() == "":
            issues.append(f"  WARN: блок {block_id} — пустой summary")

        # Проверка: пустой key_material
        key_material = block.get("key_material", [])
        if not key_material:
            issues.append(f"  WARN: блок {block_id} — пустой key_material")

        block_info.append({
            "id": block_id,
            "title": block_title,
            "votes": votes,
            "terms": block_terms,
        })

    # Глобальные термины
    global_terms = data.get("terms_introduced", [])

    return {
        "blocks": block_info,
        "block_count": len(blocks),
        "total_votes": total_votes,
        "terms": terms,
        "global_terms": global_terms,
        "issues": issues,
    }


def main():
    # Собираем все уроки
    lesson_files = sorted(LESSONS_DIR.glob("lesson_*.yaml"))
    brief_files = {
        f.stem.replace("brief_", ""): f
        for f in sorted(BRIEFS_DIR.glob("brief_*.yaml"))
    }

    print("=" * 78)
    print("QA BRIEFS — Валидация брифов уроков")
    print("=" * 78)
    print()

    total_yaml_votes = 0
    total_brief_votes = 0
    total_blocks = 0
    problems = []
    day_blocks = {}

    for lesson_file in lesson_files:
        lesson_id = lesson_file.stem.replace("lesson_", "")
        brief_path = brief_files.get(lesson_id)

        # Парсим YAML
        yaml_data = count_votes_in_yaml(lesson_file)
        total_yaml_votes += yaml_data["total_votes"]

        if not brief_path or not brief_path.exists():
            print(f"  {lesson_id}: БРИФ НЕ НАЙДЕН")
            problems.append(f"{lesson_id}: бриф отсутствует")
            continue

        # Парсим бриф
        brief_data = parse_brief(brief_path)
        total_brief_votes += brief_data["total_votes"]
        total_blocks += brief_data["block_count"]

        # Дельта votes
        delta = brief_data["total_votes"] - yaml_data["total_votes"]
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        status = "OK" if delta == 0 else "DELTA"

        # Собираем по дням
        day_num = lesson_id[:-1]  # "1A" -> "1"
        if day_num not in day_blocks:
            day_blocks[day_num] = 0
        day_blocks[day_num] += brief_data["block_count"]

        # Вывод
        block_details = " + ".join(
            f'{b["id"]}({b["votes"]}v)'
            for b in brief_data["blocks"]
        )
        print(
            f"  {lesson_id:4s} | "
            f"yaml={yaml_data['total_votes']:3d}v | "
            f"brief={brief_data['total_votes']:3d}v | "
            f"delta={delta_str:4s} | "
            f"blocks={brief_data['block_count']} | "
            f"{block_details}"
        )

        if status == "DELTA":
            problems.append(
                f"{lesson_id}: votes delta={delta_str} "
                f"(yaml={yaml_data['total_votes']}, brief={brief_data['total_votes']})"
            )

        for issue in brief_data.get("issues", []):
            print(issue)
            problems.append(f"{lesson_id}: {issue.strip()}")

    # Сводка
    print()
    print("=" * 78)
    print("СВОДКА")
    print("=" * 78)
    print(f"  Уроков (YAML):      {len(lesson_files)}")
    print(f"  Брифов:             {len(brief_files)}")
    print(f"  Блоков всего:       {total_blocks}")
    print(f"  Votes в YAML:       {total_yaml_votes}")
    print(f"  Votes в брифах:     {total_brief_votes}")
    print(f"  Глобальная дельта:  {total_brief_votes - total_yaml_votes}")
    print()

    # Таблица по дням
    print("БЛОКИ ПО ДНЯМ (лимит 4):")
    print("-" * 40)
    for day in sorted(day_blocks.keys(), key=lambda x: int(x)):
        blocks = day_blocks[day]
        over = f"  +{blocks - 4}" if blocks > 4 else ""
        bar = "#" * blocks
        print(f"  День {day:2s}: {blocks} блоков {bar}{over}")
    print(f"  ИТОГО: {total_blocks} блоков")
    print()

    # Проблемы
    if problems:
        print(f"ПРОБЛЕМЫ ({len(problems)}):")
        print("-" * 40)
        for p in problems:
            print(f"  - {p}")
    else:
        print("ПРОБЛЕМ НЕ ОБНАРУЖЕНО")

    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
