#!/usr/bin/env python3
"""
Consistency checker for gameflow episodes.

Checks narrative flow between consecutive scenes:
- Location jumps without transition
- Characters appearing without introduction
- author_text that references dialogue (should be author_text_after)
- Missing setup when scene context changes

Usage:
    python3 tools/check_consistency.py              # all episodes
    python3 tools/check_consistency.py ep_001       # single episode
"""

import sys
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMEFLOW_DIR = ROOT / "pipeline" / "gameflow" / "episodes"

PRONOUN_HINTS = [
    "она", "он ", "он.", "он,", "они", "его ", "её ", "ее ",
    "ему", "ей ", "им ", "них", "говорит это", "отвечает",
]

REACTION_HINTS = [
    "говорит это", "сказала это", "произнес", "ответил",
    "спокойно", "уверенно", "тихо", "резко",
    "почти верит", "не верит", "соглашается",
]


def load_episode(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_episode(path: Path) -> list:
    """Check a single episode for consistency issues."""
    data = load_episode(path)
    scenes = data.get("scenes", [])
    issues = []
    ep_name = path.stem

    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", f"scene_{i}")
        location = scene.get("location", "")
        chars = scene.get("characters_present", [])
        author_text = str(scene.get("author_text", "")).strip()
        dialogue = scene.get("dialogue", [])
        stype = scene.get("scene_type", "")
        branch_type = scene.get("branch_type", "")

        # ── Check 1: author_text that looks like a reaction to dialogue ──
        if author_text and dialogue:
            at_lower = author_text.lower()
            for hint in REACTION_HINTS:
                if hint in at_lower:
                    issues.append({
                        "level": "WARNING",
                        "scene": sid,
                        "check": "REACTION_BEFORE_DIALOGUE",
                        "msg": (
                            f"author_text contains '{hint}' — likely a reaction "
                            f"to dialogue. Should this be author_text_after?"
                        ),
                        "snippet": author_text[:80],
                    })
                    break

        # ── Check 2: author_text starts with pronoun (no antecedent) ──
        if author_text and i > 0:
            first_word = author_text.split()[0].lower() if author_text.split() else ""
            if first_word in ("она", "он", "они", "его", "её", "ее"):
                prev_scene = scenes[i - 1]
                prev_chars = prev_scene.get("characters_present", [])
                # If the pronoun doesn't have an obvious antecedent from same scene
                if not dialogue:
                    issues.append({
                        "level": "WARNING",
                        "scene": sid,
                        "check": "PRONOUN_WITHOUT_ANTECEDENT",
                        "msg": (
                            f"author_text starts with pronoun '{first_word}' "
                            f"but scene has no dialogue to establish who this is"
                        ),
                        "snippet": author_text[:80],
                    })

        # ── Check 3: Location jump between consecutive main-line scenes ──
        if i > 0 and not branch_type:
            prev = scenes[i - 1]
            prev_loc = prev.get("location", "")
            prev_branch = prev.get("branch_type", "")
            if (
                prev_loc
                and location
                and prev_loc != location
                and not prev_branch
                and stype != "transition"
            ):
                # Check if any setup text mentions the new location
                has_transition_text = False
                if author_text:
                    loc_words = location.lower().split(",")[0].split()
                    for w in loc_words:
                        if len(w) > 3 and w.lower() in author_text.lower():
                            has_transition_text = True
                            break

                if not has_transition_text:
                    issues.append({
                        "level": "INFO",
                        "scene": sid,
                        "check": "LOCATION_JUMP",
                        "msg": (
                            f"Location changes from '{prev_loc}' → '{location}' "
                            f"without transition scene or setup text"
                        ),
                    })

        # ── Check 4: New character appears without introduction ──
        if i > 0 and not branch_type:
            prev = scenes[i - 1]
            prev_chars = set(c.lower() for c in prev.get("characters_present", []))
            curr_chars = set(c.lower() for c in chars)
            new_chars = curr_chars - prev_chars
            # Skip "автор" and similar non-character entries
            new_chars -= {"автор", "author"}

            for nc in new_chars:
                # Check if the new character is mentioned in author_text
                mentioned = False
                if author_text and nc in author_text.lower():
                    mentioned = True
                for d in dialogue:
                    if isinstance(d, dict) and nc in str(d.get("line", "")).lower():
                        mentioned = True

                if not mentioned and nc not in ("марко", "marko"):
                    issues.append({
                        "level": "INFO",
                        "scene": sid,
                        "check": "NEW_CHARACTER",
                        "msg": (
                            f"'{nc}' appears in characters_present but wasn't "
                            f"in previous scene and isn't introduced in text"
                        ),
                    })

        # ── Check 5: Dialogue without any speaker context ──
        if dialogue and not author_text and not scene.get("author_text_after") and i > 0:
            prev = scenes[i - 1]
            prev_loc = prev.get("location", "")
            if prev_loc != location:
                issues.append({
                    "level": "INFO",
                    "scene": sid,
                    "check": "DIALOGUE_NO_SETUP",
                    "msg": (
                        "Scene starts directly with dialogue after a location "
                        "change — consider adding setup text"
                    ),
                })

        # ── Check 6: Scene ends abruptly (cliffhanger without mood/text) ──
        if stype == "cliffhanger" and not author_text and not dialogue:
            issues.append({
                "level": "WARNING",
                "scene": sid,
                "check": "EMPTY_CLIFFHANGER",
                "msg": "Cliffhanger scene has no text or dialogue",
            })

    return issues


def main():
    args = sys.argv[1:]

    if args:
        yaml_files = []
        for arg in args:
            name = arg if arg.endswith(".yaml") else f"{arg}.yaml"
            path = GAMEFLOW_DIR / name
            if path.exists():
                yaml_files.append(path)
            else:
                print(f"  \u2717 Not found: {path}")
    else:
        yaml_files = sorted(GAMEFLOW_DIR.glob("ep_*.yaml"))

    if not yaml_files:
        print("No gameflow YAML files found.")
        return

    print(f"Checking consistency for {len(yaml_files)} episode(s)...\n")

    total_warnings = 0
    total_infos = 0

    for yf in yaml_files:
        issues = check_episode(yf)
        warnings = [i for i in issues if i["level"] == "WARNING"]
        infos = [i for i in issues if i["level"] == "INFO"]
        total_warnings += len(warnings)
        total_infos += len(infos)

        if issues:
            print(f"  \u26a0 {yf.name}  ({len(warnings)} warnings, {len(infos)} info)")
            for issue in issues:
                icon = "\u26a0" if issue["level"] == "WARNING" else "\u2139\ufe0f"
                print(f"        {icon} {issue['scene']}: {issue['check']}")
                print(f"           {issue['msg']}")
                if "snippet" in issue:
                    print(f"           \u00bb {issue['snippet']}...")
        else:
            print(f"  \u2713 {yf.name}  (clean)")

    print(f"\n{'=' * 50}")
    print(f"  {total_warnings} warnings, {total_infos} info")


if __name__ == "__main__":
    main()
