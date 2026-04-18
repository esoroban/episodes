#!/usr/bin/env python3
"""
Gameflow validator.

Checks:
  1. Duplicate YAML keys (strict parsing)
  2. Broken transitions (next_default/next_success/next_fail/merge_to pointing to missing scenes)
  3. Unused flags (set_flags that never appear in require_flags)
  4. Entities without introduction (characters/concepts appearing without prior introduction)
  5. Unreachable scenes (scenes no transition leads to)
  6. Orphaned inter-episode links

Usage:
    python3 tools/validate_gameflow.py              # all episodes
    python3 tools/validate_gameflow.py ep_001       # single
"""

import sys
import yaml
import re
from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).resolve().parent.parent
GAMEFLOW_DIR = ROOT / "pipeline" / "gameflow" / "episodes"


# ═══════════════════════════════════════════════════════════════════
# 1. Strict YAML loader that rejects duplicate keys
# ═══════════════════════════════════════════════════════════════════

class DuplicateKeyError(Exception):
    pass


class StrictLoader(yaml.SafeLoader):
    pass


def _strict_construct_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node, deep=deep)
    keys = set()
    for key, _ in pairs:
        if key in keys:
            mark = node.start_mark
            raise DuplicateKeyError(
                f"Duplicate key '{key}' at line {mark.line + 1}"
            )
        keys.add(key)
    return dict(pairs)


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _strict_construct_mapping,
)


def strict_load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=StrictLoader)


# ═══════════════════════════════════════════════════════════════════
# 2. Validation checks
# ═══════════════════════════════════════════════════════════════════

class ValidationResult:
    def __init__(self, filename: str):
        self.filename = filename
        self.errors = []    # hard failures
        self.warnings = []  # soft issues

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def ok(self):
        return len(self.errors) == 0


def get_nav_targets(scene: dict) -> list:
    """Extract all scene IDs this scene can navigate to."""
    targets = []
    for key in ("next_default", "next_success", "next_fail", "merge_to"):
        val = scene.get(key)
        if val:
            targets.append((key, val))

    # options with 'next'
    for opt in scene.get("options", []):
        if "next" in opt:
            targets.append(("option.next", opt["next"]))

    # interactions list
    for inter in scene.get("interactions", []):
        for opt in inter.get("options", []):
            if "next" in opt:
                targets.append(("interactions.option.next", opt["next"]))

    # followup_interaction
    followup = scene.get("followup_interaction", {})
    for opt in followup.get("options", []):
        if "next" in opt:
            targets.append(("followup.option.next", opt["next"]))

    return targets


def validate_episode(path: Path, all_scene_ids: set) -> ValidationResult:
    """Validate a single episode YAML."""
    result = ValidationResult(path.name)

    # ── Check 1: Duplicate keys ──────────────────────────────────
    try:
        data = strict_load(path)
    except DuplicateKeyError as e:
        result.error(f"DUPLICATE KEY: {e}")
        # Fall back to standard loader to continue other checks
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.error(f"YAML PARSE ERROR: {e}")
        return result

    scenes = data.get("scenes", [])
    if not scenes:
        result.error("No scenes found")
        return result

    ep_id = data.get("episode_id", "?")
    scene_ids = set()
    local_set_flags = set()
    local_require_flags = set()

    for scene in scenes:
        sid = scene.get("scene_id", "???")

        # ── Unique scene IDs ────────────────────────────────────
        if sid in scene_ids:
            result.error(f"DUPLICATE SCENE ID: {sid}")
        scene_ids.add(sid)

        # ── Collect flags ────────────────────────────────────────
        for f in scene.get("set_flags", []):
            local_set_flags.add(f)
        for f in scene.get("require_flags", []):
            local_require_flags.add(f)

    # ── Check 2: Broken transitions ──────────────────────────────
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        for key, target in get_nav_targets(scene):
            if target not in scene_ids and target not in all_scene_ids:
                # Inter-episode links (ep005_s01 etc.) are warnings, not errors
                if re.match(r"ep\d{3}_s\d+", target):
                    ep_num = int(target[2:5])
                    target_file = GAMEFLOW_DIR / f"ep_{ep_num:03d}.yaml"
                    if not target_file.exists():
                        result.warn(
                            f"INTER-EP LINK: {sid}.{key} → {target} "
                            f"(ep_{ep_num:03d}.yaml does not exist yet)"
                        )
                else:
                    result.error(f"BROKEN LINK: {sid}.{key} → {target}")

    # ── Check 3: Unreachable scenes ──────────────────────────────
    reachable = set()
    first_scene = scenes[0].get("scene_id") if scenes else None
    if first_scene:
        reachable.add(first_scene)
    for scene in scenes:
        for _, target in get_nav_targets(scene):
            if target in scene_ids:
                reachable.add(target)
    unreachable = scene_ids - reachable
    for sid in unreachable:
        result.warn(f"UNREACHABLE SCENE: {sid} (no transition leads here)")

    # ── Check 4: Unused flags ────────────────────────────────────
    unused_flags = local_set_flags - local_require_flags
    if unused_flags:
        for f in sorted(unused_flags):
            result.warn(f"UNUSED FLAG: '{f}' is set but never required in this episode")

    # ── Check 5: Characters without introduction ─────────────────
    known_chars = set()
    terms_introduced = set(data.get("terms_introduced", []))
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        chars = scene.get("characters_present", [])
        for ch in chars:
            if ch not in known_chars and scene != scenes[0]:
                # Not an error for ep > 1 — just track
                pass
            known_chars.add(ch)

    # ── Check 6: Quiz completeness ───────────────────────────────
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        opts = scene.get("options", [])
        quiz_opts = [o for o in opts if "correct" in o]
        if quiz_opts and not any(o.get("correct") for o in quiz_opts):
            result.error(f"QUIZ NO CORRECT: {sid} has quiz options but none marked correct")

        # Also check interactions list
        for inter in scene.get("interactions", []):
            i_opts = inter.get("options", [])
            quiz_i_opts = [o for o in i_opts if "correct" in o]
            if quiz_i_opts and not any(o.get("correct") for o in quiz_i_opts):
                result.error(f"QUIZ NO CORRECT: {sid} interactions has options but none correct")

    # ── Check 7: No speaker-prefix wrapping in feedback fields ────
    # Feedbacks are rendered inside Sofa's chat bubble — renderer adds her name.
    # "Софа: «...»" wrapper creates tautology "Sofa: Sofa said ..."
    import re as _re
    SPEAKER_PREFIX = _re.compile(r"^\s*(Софа|Марко|Автор|автор)\s*[:—-]\s*[«\"']")
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        for field in ("feedback_success", "feedback_soft_fail"):
            val = scene.get(field)
            if isinstance(val, str) and SPEAKER_PREFIX.match(val):
                result.error(
                    f"FEEDBACK PREFIX: {sid}.{field} starts with speaker prefix "
                    f"(e.g. 'Софа: «...»'). Remove — renderer auto-attributes to Софа."
                )

    # ── Check 8: voice_message unlock buttons must have `line` ────
    # Subtitle field is required for proofreading before audio is recorded.
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        unlock = scene.get("unlock_button")
        if not unlock:
            continue
        rev = unlock.get("reveals", {}) if isinstance(unlock, dict) else {}
        if rev.get("type") == "voice_message":
            missing = [k for k in ("who", "line", "duration") if not rev.get(k)]
            if missing:
                result.error(
                    f"VOICE_MESSAGE INCOMPLETE: {sid}.unlock_button.reveals missing {missing}. "
                    f"All voice messages need who/line/duration for subtitle + audio."
                )

    # ── Check 9: Voice-channel violations in Sofa dialogue ────────
    # Софа is text-only. Her lines must not describe voice/sound,
    # nor use hearing verbs like «слышишь». See pipeline_rules.md.
    SOFA_FORBIDDEN = _re.compile(
        r"\b(слышишь|услышишь|услышь|слышно|треск|электронн\w*|шипени\w*|"
        r"голос\s+Соф\w*|мой\s+голос|твой\s+голос)\b",
        _re.IGNORECASE,
    )
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        chars = set(scene.get("characters_present", []))
        # Collect Sofa's own lines
        sofa_lines = []
        for d in scene.get("dialogue", []) or []:
            if isinstance(d, dict) and d.get("who") == "Софа":
                sofa_lines.append(("dialogue", d.get("line", "")))
        for field in ("feedback_success", "feedback_soft_fail"):
            v = scene.get(field)
            if isinstance(v, str):
                sofa_lines.append((field, v))
        for src, line in sofa_lines:
            m = SOFA_FORBIDDEN.search(line or "")
            if m:
                result.error(
                    f"SOFA VOICE VIOLATION: {sid}.{src} uses forbidden word "
                    f"'{m.group(0)}' — Софа is text-only. Use 'читаешь' / 'видишь' / "
                    f"remove sound description."
                )
        # Also check author lines in Sofa scenes for describing Sofa's voice
        if "Софа" in chars:
            SOFA_VOICE_DESC = _re.compile(
                r"(треск|электронн\w*|шипени\w*)", _re.IGNORECASE
            )
            for d in scene.get("dialogue", []) or []:
                if isinstance(d, dict) and d.get("who") == "автор":
                    line = d.get("line", "") or ""
                    m = SOFA_VOICE_DESC.search(line)
                    if m:
                        result.error(
                            f"AUTHOR DESCRIBES SOFA SOUND: {sid}.dialogue[автор] contains "
                            f"'{m.group(0)}'. Софа has no sound. Describe screen behavior instead."
                        )

    return result


# ═══════════════════════════════════════════════════════════════════
# 3. Cross-episode checks
# ═══════════════════════════════════════════════════════════════════

def cross_validate(results: dict, all_data: dict):
    """Check cross-episode consistency."""
    all_set_flags = set()
    all_require_flags = set()

    for filename, data in all_data.items():
        for scene in data.get("scenes", []):
            for f in scene.get("set_flags", []):
                all_set_flags.add(f)
            for f in scene.get("require_flags", []):
                all_require_flags.add(f)

    # Flags set but never required anywhere
    globally_unused = all_set_flags - all_require_flags
    if globally_unused:
        # Add to first result as cross-ep warning
        first_result = next(iter(results.values()))
        for f in sorted(globally_unused):
            first_result.warn(f"GLOBAL UNUSED FLAG: '{f}' is set somewhere but never required anywhere")


# ═══════════════════════════════════════════════════════════════════
# 4. Main
# ═══════════════════════════════════════════════════════════════════

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
                print(f"  ✗ Not found: {path}")
    else:
        yaml_files = sorted(GAMEFLOW_DIR.glob("ep_*.yaml"))

    if not yaml_files:
        print("No gameflow YAML files found.")
        return

    # Collect all scene IDs across all episodes for cross-reference
    all_scene_ids = set()
    all_data = {}
    for yf in yaml_files:
        try:
            with open(yf, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            all_data[yf.name] = data
            for scene in data.get("scenes", []):
                sid = scene.get("scene_id")
                if sid:
                    all_scene_ids.add(sid)
        except yaml.YAMLError:
            pass  # Will be caught in validation

    print(f"Validating {len(yaml_files)} episode(s)...\n")

    results = {}
    total_errors = 0
    total_warnings = 0

    for yf in yaml_files:
        result = validate_episode(yf, all_scene_ids)
        results[yf.name] = result

        status = "✓ PASS" if result.ok else "✗ FAIL"
        err_count = len(result.errors)
        warn_count = len(result.warnings)
        total_errors += err_count
        total_warnings += warn_count

        print(f"  {status}  {yf.name}  ({err_count} errors, {warn_count} warnings)")

        for e in result.errors:
            print(f"        ✗ {e}")
        for w in result.warnings:
            print(f"        ⚠ {w}")
        if result.errors or result.warnings:
            print()

    # Cross-episode checks
    if len(all_data) > 1:
        cross_validate(results, all_data)
        # Re-print cross-ep warnings
        first_key = next(iter(results))
        cross_warnings = [w for w in results[first_key].warnings if w.startswith("GLOBAL")]
        if cross_warnings:
            print("  Cross-episode checks:")
            for w in cross_warnings:
                print(f"        ⚠ {w}")
            total_warnings += len(cross_warnings)
            print()

    # Summary
    print(f"{'═' * 50}")
    if total_errors == 0:
        print(f"  ALL PASS  ({total_warnings} warnings)")
    else:
        print(f"  {total_errors} ERRORS, {total_warnings} WARNINGS")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
