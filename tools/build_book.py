#!/usr/bin/env python3
"""
build_book.py — Конвертер эпизодов в чистую читаемую книгу.

Вход:  book/ep_NNN.md  (рабочий исходник с разметкой)
Выход: publish/book/ep_NNN.md  (чистая проза без квизов и блок-маркеров)

Что удаляется:
  - Блок-заголовки: [ДРАМА], [СОФА-БЛОК], [ИСПЫТАНИЕ], КЛИФФХЭНГЕР
  - Метаданные урока (🎓 **Урок:**)
  - Маркеры квизов → и ✎ (превращаются в текст)
  - Технические разделители ---
  - Emoji 📱

Что остаётся: чистая проза, диалоги, монологи.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK_SRC = ROOT / "book"
BOOK_OUT = ROOT / "publish" / "book"


def clean_episode(text: str) -> str:
    lines = text.split("\n")
    out = []
    skip_next_blank = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # --- Удаляем метаданные урока ---
        if stripped.startswith("🎓"):
            i += 1
            skip_next_blank = True
            continue

        # --- Удаляем блок-заголовки ---
        if re.match(r"^\*\*\[(ДРАМА|СОФА-БЛОК|ИСПЫТАНИЕ)\]\*\*$", stripped):
            i += 1
            skip_next_blank = True
            continue

        if re.match(r"^⚡\s*\*\*КЛИФФХЭНГЕР:\*\*$", stripped):
            i += 1
            skip_next_blank = True
            continue

        # --- Удаляем горизонтальные разделители ---
        if stripped == "---":
            # Заменяем на пустую строку (разделитель сцен)
            if out and out[-1] != "":
                out.append("")
            i += 1
            skip_next_blank = True
            continue

        # --- Пропускаем пустые строки после удалённых элементов ---
        if skip_next_blank and stripped == "":
            i += 1
            skip_next_blank = False
            continue
        skip_next_blank = False

        # --- Строки "→ разблокирует:" — это нарратив, пропускаем ---
        if stripped.startswith("→ разблокирует"):
            i += 1
            continue

        # --- Закрытые квизы (→) — превращаем в текст ---
        if stripped.startswith("→"):
            converted = convert_closed_quiz(stripped)
            if converted:
                out.append(converted)
            i += 1
            continue

        # --- Открытые вопросы (✎) — превращаем в текст ---
        if stripped.startswith("✎"):
            # Собираем блок: вопрос + подсказка + пример
            block_lines = [stripped]
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("*Подсказка:") or nxt.startswith("*Пример:"):
                    block_lines.append(nxt)
                    i += 1
                elif nxt == "":
                    # Пустая строка внутри блока — проверяем следующую
                    if i + 1 < len(lines) and (
                        lines[i + 1].strip().startswith("*Подсказка:")
                        or lines[i + 1].strip().startswith("*Пример:")
                    ):
                        i += 1
                        continue
                    else:
                        break
                else:
                    break
            converted = convert_open_quiz(block_lines)
            if converted:
                out.append(converted)
            continue

        # --- Убираем 📱 маркер, оставляем текст ---
        if "📱" in line:
            line = line.replace("📱", "").strip()
            if not line:
                i += 1
                continue

        # --- Убираем строки вида "Марко отвечает правильно →" ---
        if re.match(r"^.+→\s*$", stripped) and not stripped.startswith("→"):
            # Narrative arrow — keep text, remove arrow
            line = stripped.rstrip("→ ").strip()
            if line:
                out.append(line)
            i += 1
            continue

        out.append(line)
        i += 1

    # Убираем множественные пустые строки
    result = []
    for line in out:
        if line.strip() == "" and result and result[-1].strip() == "":
            continue
        result.append(line)

    # Убираем пустые строки в начале и конце
    while result and result[0].strip() == "":
        result.pop(0)
    while result and result[-1].strip() == "":
        result.pop()

    return "\n".join(result) + "\n"


def convert_closed_quiz(line: str) -> str:
    """Превращает строку → квиза в книжный текст."""
    # Убираем начальный →
    line = line.lstrip("→").strip()

    # Паттерн: **вопрос** → ответ *(объяснение)*
    m = re.match(
        r"\*\*(.+?)\*\*\s*→\s*(.+?)(?:\s*\*\((.+?)\)\*)?$",
        line,
    )
    if m:
        question = m.group(1).strip()
        answer = m.group(2).strip().rstrip("*").strip()
        explanation = m.group(3)
        if explanation:
            return f"*{question}* {answer.capitalize()} — {explanation.rstrip('.')}."
        else:
            return f"*{question}* {answer.capitalize()}."

    # Паттерн: **вопрос** *(ответ/объяснение)*
    m = re.match(r"\*\*(.+?)\*\*\s*\*\((.+?)\)\*$", line)
    if m:
        question = m.group(1).strip()
        raw = m.group(2).strip()
        # Если есть / — это "опции — объяснение", берём последний элемент
        if "/" in raw:
            parts = raw.split("/")
            last = parts[-1].strip()
            # Разделяем ответ и объяснение по тире
            dash = re.split(r"\s*[—–-]\s*", last, maxsplit=1)
            answer = dash[0].strip()
            explanation = dash[1].strip() if len(dash) > 1 else ""
            if explanation:
                return f"*{question}* {answer.capitalize()} — {explanation.rstrip('.')}."
            return f"*{question}* {answer.capitalize()}."
        return f"*{question}* {raw.capitalize().rstrip('.')}."

    # Паттерн без болда: «текст» → ответ *(объяснение)*
    m = re.match(r"[«\"'](.+?)[»\"']\s*→\s*(.+?)(?:\s*\*\((.+?)\)\*)?$", line)
    if m:
        statement = m.group(1).strip()
        answer = m.group(2).strip()
        explanation = m.group(3)
        if explanation:
            return f"*«{statement}»* — {answer}. {explanation.capitalize().rstrip('.')}."
        else:
            return f"*«{statement}»* — {answer}."

    # Фоллбэк: просто убираем → и форматирование
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    cleaned = re.sub(r"\*\((.+?)\)\*", r"(\1)", cleaned)
    cleaned = cleaned.replace("→", "—").strip()
    if cleaned:
        return f"*{cleaned}*"
    return None


def convert_open_quiz(block_lines: list) -> str:
    """Превращает блок ✎ в книжный текст."""
    question = block_lines[0].lstrip("✎").strip()
    # Убираем болд
    question = re.sub(r"\*\*(.+?)\*\*", r"\1", question)

    parts = [f"*{question}*"]

    for line in block_lines[1:]:
        line = line.strip().strip("*").strip()
        if line:
            parts.append(f"*{line}*")

    return "\n\n".join(parts)


def process_file(src: Path, dst: Path):
    text = src.read_text(encoding="utf-8")
    cleaned = clean_episode(text)
    dst.write_text(cleaned, encoding="utf-8")
    print(f"  {src.name} → {dst.name}")


def main():
    BOOK_OUT.mkdir(parents=True, exist_ok=True)

    # Определяем, какие файлы обрабатывать
    if len(sys.argv) > 1:
        # Конкретные номера эпизодов
        episodes = []
        for arg in sys.argv[1:]:
            try:
                n = int(arg)
                episodes.append(n)
            except ValueError:
                # Может быть диапазон "1-3"
                if "-" in arg:
                    start, end = arg.split("-")
                    episodes.extend(range(int(start), int(end) + 1))
        files = [BOOK_SRC / f"ep_{n:03d}.md" for n in episodes]
    else:
        files = sorted(BOOK_SRC.glob("ep_*.md"))

    if not files:
        print("Нет файлов для обработки.")
        return

    print(f"Конвертация в книгу: {len(files)} эпизодов")
    for src in files:
        if src.exists():
            dst = BOOK_OUT / src.name
            process_file(src, dst)
        else:
            print(f"  Пропуск: {src.name} не найден")

    print(f"\nРезультат: {BOOK_OUT}/")


if __name__ == "__main__":
    main()
