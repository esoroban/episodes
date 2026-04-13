#!/usr/bin/env python3
"""
Converter from MD files to audiobook via ElevenLabs API.

Usage:
    # Single file
    python md_to_audiobook.py BOOK/EP_01.md -o AUDIO/ep01.mp3

    # Batch: all episodes
    python md_to_audiobook.py --batch BOOK/EP_01.md BOOK/EP_02.md ... --outdir AUDIO/

    # List voices
    python md_to_audiobook.py --list-voices

API key is read from the .env file (ELEVENLABS_API_KEY=...)
"""

import argparse
import os
import re
import sys
import time

import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

API_BASE = "https://api.elevenlabs.io/v1"
MODEL_ID = "eleven_multilingual_v2"
DEFAULT_VOICE_ID = "Ntd0iVwICtUtA6Fvx27M"  # Evgeniy Shevchenko
MAX_CHUNK_CHARS = 4500


def load_api_key():
    """Reads ELEVENLABS_API_KEY from the .env file in the project root."""
    if not os.path.exists(ENV_FILE):
        sys.exit(f"Error: file {ENV_FILE} not found. Create it with ELEVENLABS_API_KEY=...")
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("Error: ELEVENLABS_API_KEY not found in the .env file")


def strip_markdown(text: str) -> str:
    """Strips MD markup, leaving clean text for voice synthesis.
    Italics (inner thoughts) are converted to pauses around the text.
    """
    # Remove heading lines entirely (episode title, lesson)
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    # Remove lesson emoji marker line
    text = re.sub(r"^🎓.*$", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^---\s*$", "", text, flags=re.MULTILINE)
    # Remove emojis
    text = re.sub(r"[📱⚡🎓🔥💡🎯✅❌🧠📋🔒🔑💬🎶🎵👀🤔😊😢😡🙄💪🌟⭐🏠🚪🪞🔮📖📝🎮🎲🃏🗡️🛡️⚔️🏰🌙☀️🌅🌊🔔📞💻🖥️🎭🎪🎨🎬📺📻🕐🕑🕒]", "", text)
    # Bold -> plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Italics (inner thoughts) -> pause ... text ...
    text = re.sub(r"\*(.+?)\*", r"... \1 ...", text)
    # Underline
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # Links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # List markers
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Splits text into chunks by paragraphs, not exceeding max_chars."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)
    return chunks


def list_voices(api_key: str):
    """Lists available voices."""
    resp = requests.get(f"{API_BASE}/voices", headers={"xi-api-key": api_key})
    resp.raise_for_status()
    voices = resp.json()["voices"]
    print(f"\nAvailable voices: {len(voices)}\n")
    for v in voices:
        labels = ", ".join(f"{k}: {val}" for k, val in (v.get("labels") or {}).items())
        print(f"  {v['name']:25s}  ID: {v['voice_id']}  [{labels}]")
    print()


def synthesize_chunk(api_key: str, text: str, voice_id: str) -> bytes:
    """Sends text to ElevenLabs and returns audio (MP3)."""
    url = f"{API_BASE}/text-to-speech/{voice_id}/stream"
    resp = requests.post(
        url,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        params={"output_format": "mp3_44100_128"},
        stream=True,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        sys.exit(f"API error ({resp.status_code}): {detail}")

    audio = b""
    for chunk in resp.iter_content(chunk_size=4096):
        if chunk:
            audio += chunk
    return audio


def process_file(api_key: str, md_path: str, output_path: str, voice_id: str):
    """Processes a single MD file -> MP3."""
    with open(md_path, "r", encoding="utf-8") as f:
        raw = f.read()

    text = strip_markdown(raw)
    if not text:
        print(f"  Warning: skipping {md_path} — empty after cleanup")
        return

    chunks = split_into_chunks(text)
    total = len(chunks)
    print(f"  {len(text)} characters -> {total} chunks")

    audio_data = b""
    for i, chunk in enumerate(chunks, 1):
        print(f"    [{i}/{total}] {len(chunk)} chars...", end=" ", flush=True)
        audio = synthesize_chunk(api_key, chunk, voice_id)
        audio_data += audio
        print(f"done, {len(audio)} bytes")
        if i < total:
            time.sleep(0.5)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_data)

    size_mb = len(audio_data) / (1024 * 1024)
    print(f"  -> {output_path} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="MD -> audiobook via ElevenLabs")
    parser.add_argument("md_files", nargs="*", help="Path to MD file(s)")
    parser.add_argument("--voice", default=DEFAULT_VOICE_ID, help="Voice ID")
    parser.add_argument("--output", "-o", default=None, help="Output MP3 (for a single file)")
    parser.add_argument("--outdir", default=None, help="Output directory (batch mode)")
    parser.add_argument("--list-voices", action="store_true", help="Show available voices")
    args = parser.parse_args()

    api_key = load_api_key()

    if args.list_voices:
        list_voices(api_key)
        return

    if not args.md_files:
        parser.error("Specify MD file(s) or --list-voices")

    if len(args.md_files) == 1 and not args.outdir:
        # Single file
        md_path = os.path.abspath(args.md_files[0])
        if not os.path.exists(md_path):
            sys.exit(f"File not found: {md_path}")
        if args.output:
            output_path = os.path.abspath(args.output)
        else:
            base = os.path.splitext(os.path.basename(md_path))[0]
            output_path = os.path.join(os.path.dirname(md_path), f"{base}.mp3")
        print(f"> {os.path.basename(md_path)}")
        process_file(api_key, md_path, output_path, args.voice)
    else:
        # Batch mode
        outdir = os.path.abspath(args.outdir) if args.outdir else os.path.join(PROJECT_ROOT, "AUDIO")
        os.makedirs(outdir, exist_ok=True)
        total_files = len(args.md_files)
        for idx, md_file in enumerate(args.md_files, 1):
            md_path = os.path.abspath(md_file)
            if not os.path.exists(md_path):
                print(f"Warning: skipping {md_path} — not found")
                continue
            base = os.path.splitext(os.path.basename(md_path))[0]
            # EP_01 -> ep01
            ep_match = re.search(r"(\d+)", base)
            if ep_match:
                out_name = f"ep{ep_match.group(1).zfill(2)}.mp3"
            else:
                out_name = f"{base}.mp3"
            output_path = os.path.join(outdir, out_name)
            print(f"\n[{idx}/{total_files}] > {os.path.basename(md_path)}")
            process_file(api_key, md_path, output_path, args.voice)

    print("\nAll done!")


if __name__ == "__main__":
    main()
