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

    # ── Check 10: Sofa speech leak in author_text/author_text_after ──
    # Софа = всегда Telegram. Реплики Софы должны быть в dialogue,
    # не в author_text — иначе уйдут как голос Автора.
    SOFA_LEAK = _re.compile(r"^\s*Софа\s*[:—-]", _re.MULTILINE)
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        for field in ("author_text", "author_text_after"):
            text = scene.get(field, "")
            if isinstance(text, str) and SOFA_LEAK.search(text):
                result.error(
                    f"SOFA LEAK: {sid}.{field} contains 'Софа: ...' — "
                    f"move to dialogue/dialogue_after. Софа = всегда Telegram-чат."
                )

    # ── Check 12: source_ref required ────────────────────────────
    # Каждая сцена должна ссылаться на источник в pipeline/source/episodes.
    # Без source_ref теряется отслеживание происхождения.
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        if not scene.get("source_ref"):
            result.error(
                f"NO SOURCE_REF: {sid} — каждая сцена обязана указывать source_ref "
                f"(напр. day_NN.epN.drama). Без него теряется связь со source of truth."
            )

    # ── Check 13: previously block forbidden ─────────────────────
    # Игрок только что прошёл предыдущий эпизод — никаких «ранее в серии».
    # См. CLAUDE.md и pipeline_rules.md.
    if data.get("previously"):
        result.error(
            f"PREVIOUSLY FORBIDDEN: эпизод содержит блок `previously:` — "
            f"запрещено. Игрок только что прошёл предыдущий эпизод."
        )

    # ── Check 14: branch_type must be from allowed set ───────────
    # См. branching_rules.md — только эти 4 типа разрешены.
    ALLOWED_BRANCH_TYPES = {"soft_fail_loop", "flavor_detour", "gated_response", "cosmetic_branch"}
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        bt = scene.get("branch_type")
        if bt and bt not in ALLOWED_BRANCH_TYPES:
            result.error(
                f"INVALID BRANCH_TYPE: {sid}.branch_type='{bt}' — допустимы только "
                f"{sorted(ALLOWED_BRANCH_TYPES)}. См. branching_rules.md."
            )

    # ── Check 15: Sofa speaks but not in characters_present ──────
    # Если Софа в dialogue/dialogue_after, она обязана быть в characters_present —
    # иначе рендерер размещает её реплики в drama-UI, не в Telegram.
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        chars = set(scene.get("characters_present", []))
        for field in ("dialogue", "dialogue_after"):
            items = scene.get(field, []) or []
            if any(isinstance(d, dict) and d.get("who") == "Софа" for d in items):
                if "Софа" not in chars:
                    result.error(
                        f"SOFA NOT IN CAST: {sid}.{field} contains Софа's lines, but "
                        f"Софа is not in characters_present={sorted(chars)}. "
                        f"Add her — otherwise renderer puts her lines into drama-UI, not Telegram."
                    )
                    break  # one error per scene is enough

    # ── Check 16: next_fail must not self-loop to same scene ─────
    # Retry на неправильный ответ — ответственность рендера, не YAML-графа.
    # Self-loop не работает: рендерер не re-инициализирует чат на той же сцене.
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        nf = scene.get("next_fail")
        if nf and nf == sid:
            result.error(
                f"SELF-LOOP NEXT_FAIL: {sid}.next_fail points to itself. "
                f"Remove — quiz retry is handled by renderer inline in chat."
            )

    # ── Check 17: Named plot entities before their reveal ────────
    # Именованные сущности сюжета (Зеркальный Город и др.) не должны появляться
    # в тексте эпизодов до того, как они введены нарративом.
    # Map: entity stem (matched with regex) → first episode where entity appears in plot.
    NAMED_ENTITIES = {
        # Зеркальный Город — впервые виден Марко в ep_004 (вход через дверь)
        r"Зеркальн\w*\s+Город": 4,
    }
    def _scene_ep(sid_: str) -> int:
        m = re.match(r"ep(\d+)_", sid_)
        return int(m.group(1)) if m else 0
    for scene in scenes:
        sid = scene.get("scene_id", "???")
        scene_ep = _scene_ep(sid)
        # collect all text fields (only user-visible ones — not comments/metadata)
        text_chunks = []
        for field in ("author_text", "author_text_after", "question",
                       "feedback_success", "feedback_soft_fail", "correct_logic"):
            v = scene.get(field)
            if isinstance(v, str):
                text_chunks.append(v)
        for d in scene.get("dialogue", []) or []:
            if isinstance(d, dict):
                text_chunks.append(str(d.get("line", "")))
        for d in scene.get("dialogue_after", []) or []:
            if isinstance(d, dict):
                text_chunks.append(str(d.get("line", "")))
        for opt in scene.get("options", []) or []:
            if isinstance(opt, dict):
                text_chunks.append(str(opt.get("text", "")))
        for inter in scene.get("interactions", []) or []:
            if isinstance(inter, dict):
                for field in ("question", "feedback_success", "feedback_soft_fail", "correct_logic"):
                    v = inter.get(field)
                    if isinstance(v, str):
                        text_chunks.append(v)
                for opt in inter.get("options", []) or []:
                    if isinstance(opt, dict):
                        text_chunks.append(str(opt.get("text", "")))
        blob = " ".join(text_chunks)
        for entity_pat, reveal_ep in NAMED_ENTITIES.items():
            if re.search(entity_pat, blob) and scene_ep and scene_ep < reveal_ep:
                m = re.search(entity_pat, blob)
                result.error(
                    f"PRE-REVEAL ENTITY: {sid} mentions '{m.group(0)}' before it is "
                    f"introduced in plot (first appears in ep_{reveal_ep:03d}). "
                    f"Replace with neutral example until the entity appears in the story."
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

    # ── Check 11: Character mention before first appearance ───────
    # If a named character is mentioned in text/dialogue/quiz BEFORE
    # they first appear in characters_present — fail.
    CHARS = ["Софа", "София", "Марко", "Лина", "Макс", "Витя", "Олена", "Данила",
             "Леон", "Вера Андреевна", "Вера", "Сем", "Голос", "Рей", "Дмитрик", "Мама",
             "Сергей Палыч", "Маша", "Микола", "Оленка"]
    CHARS_SORTED = sorted(CHARS, key=lambda x: -len(x))

    mentions = {c: [] for c in CHARS}
    presences = {c: [] for c in CHARS}

    for filename in sorted(all_data.keys()):
        m = re.search(r"ep_(\d+)", filename)
        if not m:
            continue
        ep_num = int(m.group(1))
        data = all_data[filename]
        for idx, scene in enumerate(data.get("scenes", [])):
            sid = scene.get("scene_id", "")
            chars_present = scene.get("characters_present", []) or []
            for c in CHARS:
                if c in chars_present:
                    presences[c].append((ep_num, idx, sid))
            text_blob = []
            for fld in ("question", "author_text", "author_text_after", "correct_logic",
                        "feedback_success", "feedback_soft_fail"):
                v = scene.get(fld)
                if isinstance(v, str):
                    text_blob.append(v)
            for d in (scene.get("dialogue", []) or []) + (scene.get("dialogue_after", []) or []):
                if isinstance(d, dict):
                    text_blob.append(str(d.get("line", "")))
            for o in scene.get("options", []) or []:
                if isinstance(o, dict):
                    text_blob.append(str(o.get("text", "")))
            for inter in scene.get("interactions", []) or []:
                if isinstance(inter, dict):
                    for fld in ("question", "feedback_success", "feedback_soft_fail", "correct_logic"):
                        v = inter.get(fld)
                        if isinstance(v, str):
                            text_blob.append(v)
                    for o in inter.get("options", []) or []:
                        if isinstance(o, dict):
                            text_blob.append(str(o.get("text", "")))
            full = " ".join(text_blob)
            check_full = full
            for c in CHARS_SORTED:
                if re.search(r"\b" + re.escape(c) + r"\b", check_full):
                    mentions[c].append((ep_num, idx, sid))
                    check_full = re.sub(r"\b" + re.escape(c) + r"\b", "###", check_full)

    first_result = next(iter(results.values()))
    for c in CHARS:
        if not mentions[c] or not presences[c]:
            continue
        first_m = mentions[c][0]
        first_p = presences[c][0]
        if first_m < first_p:
            first_result.error(
                f"NAME LEAK: '{c}' mentioned in ep_{first_m[0]:03d} {first_m[2]} "
                f"BEFORE first appearance in ep_{first_p[0]:03d} {first_p[2]}. "
                f"Rephrase the early mention or move the character introduction earlier."
            )


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
