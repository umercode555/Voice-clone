"""
Command-line voice cloning with XTTS-v2. No browser UI needed.

Usage:
  python clone_voice.py --text "Hello there" --voice samples/my_voice.wav --lang en --out output/hello.wav
"""

import os
import argparse

os.environ.setdefault("COQUI_TOS_AGREED", "1")

import torch
from TTS.api import TTS

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"


def main():
    parser = argparse.ArgumentParser(description="Clone a voice and generate speech with XTTS-v2.")
    parser.add_argument("--text", required=True, help="Text to speak")
    parser.add_argument("--voice", required=True, help="Path to a reference voice .wav file (5-15s, clean audio)")
    parser.add_argument("--lang", default="en", help="Language code, e.g. en, es, fr, de, ja, zh-cn")
    parser.add_argument("--out", default="output/clone.wav", help="Output .wav path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading XTTS-v2 on {device} (first run downloads ~2GB)...")
    tts = TTS(MODEL_NAME).to(device)

    print("Generating...")
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.voice,
        language=args.lang,
        file_path=args.out,
    )
    print(f"Done -> {args.out}")


if __name__ == "__main__":
    main()
