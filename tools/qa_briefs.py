#!/usr/bin/env python3
"""
QA script for validating lesson briefs (step 0).
Compares data from YAML lessons with data from briefs.

Checks:
1. Vote completeness — all vote steps from YAML are present in the brief
2. Blocks without terms — suspicious (pure practice)
3. Empty fields — summary, key_material
4. Overall summary
"""

import yaml
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LESSONS_DIR = ROOT / "lessons_ru"
BRIEFS_DIR = ROOT / "pipeline" / "briefs"


def count_votes_in_yaml(lesson_path: Path) -> dict:
    """Counts vote steps in a YAML lesson."""
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
    """Parses a lesson brief."""
    with open(brief_path, "r", encoding="utf-8") as f:
        # Skip comment lines before YAML
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

        # Check: block without terms
        if not block_terms or block_terms == []:
            issues.append(f"  WARN: block {block_id} has no new terms")

        # Check: empty summary
        summary = block.get("summary", "")
        if not summary or summary.strip() == "":
            issues.append(f"  WARN: block {block_id} — empty summary")

        # Check: empty key_material
        key_material = block.get("key_material", [])
        if not key_material:
            issues.append(f"  WARN: block {block_id} — empty key_material")

        block_info.append({
            "id": block_id,
            "title": block_title,
            "votes": votes,
            "terms": block_terms,
        })

    # Global terms
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
    # Collect all lessons
    lesson_files = sorted(LESSONS_DIR.glob("lesson_*.yaml"))
    brief_files = {
        f.stem.replace("brief_", ""): f
        for f in sorted(BRIEFS_DIR.glob("brief_*.yaml"))
    }

    print("=" * 78)
    print("QA BRIEFS — Lesson brief validation")
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

        # Parse YAML
        yaml_data = count_votes_in_yaml(lesson_file)
        total_yaml_votes += yaml_data["total_votes"]

        if not brief_path or not brief_path.exists():
            print(f"  {lesson_id}: BRIEF NOT FOUND")
            problems.append(f"{lesson_id}: brief missing")
            continue

        # Parse brief
        brief_data = parse_brief(brief_path)
        total_brief_votes += brief_data["total_votes"]
        total_blocks += brief_data["block_count"]

        # Vote delta
        delta = brief_data["total_votes"] - yaml_data["total_votes"]
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        status = "OK" if delta == 0 else "DELTA"

        # Collect by days
        day_num = lesson_id[:-1]  # "1A" -> "1"
        if day_num not in day_blocks:
            day_blocks[day_num] = 0
        day_blocks[day_num] += brief_data["block_count"]

        # Output
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

    # Summary
    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"  Lessons (YAML):     {len(lesson_files)}")
    print(f"  Briefs:             {len(brief_files)}")
    print(f"  Total blocks:       {total_blocks}")
    print(f"  Votes in YAML:      {total_yaml_votes}")
    print(f"  Votes in briefs:    {total_brief_votes}")
    print(f"  Global delta:       {total_brief_votes - total_yaml_votes}")
    print()

    # Blocks per day table
    print("BLOCKS PER DAY (limit 4):")
    print("-" * 40)
    for day in sorted(day_blocks.keys(), key=lambda x: int(x)):
        blocks = day_blocks[day]
        over = f"  +{blocks - 4}" if blocks > 4 else ""
        bar = "#" * blocks
        print(f"  Day {day:2s}: {blocks} blocks {bar}{over}")
    print(f"  TOTAL: {total_blocks} blocks")
    print()

    # Problems
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        print("-" * 40)
        for p in problems:
            print(f"  - {p}")
    else:
        print("NO PROBLEMS FOUND")

    print()
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
