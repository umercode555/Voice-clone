# Voicebox Lite

A minimal, free, unlimited local voice-cloning app for old Intel Macs (works fine on
2012 MacBook Pro / Catalina too). Powered by [Coqui XTTS-v2](https://github.com/idiap/coqui-ai-TTS)
running entirely on CPU — no cloud, no account, no usage limits.

This is **not** a clone of Voicebox's Tauri desktop app (that app's build tools require
macOS 13+ and a newer PyTorch than Intel Macs can get). This is the same core idea —
free local zero-shot voice cloning — built with tools that actually run on your machine.

## What you get

- `app.py` — a browser-based UI (drag in a voice sample, type text, get cloned speech)
- `clone_voice.py` — a plain command-line version if you don't want the browser UI
- `run.sh` — one command that sets everything up and launches the UI

## Requirements

- **Python 3.10, 3.11, or 3.12.** Catalina ships an older Python, so install one first:
  ```bash
  brew install pyenv
  pyenv install 3.11.9
  cd voicebox-lite
  pyenv local 3.11.9
  ```
  If Homebrew itself won't install on Catalina anymore, use the
  [python.org 3.11 macOS installer](https://www.python.org/downloads/release/python-3119/) instead —
  it still supports 10.15.
- Xcode Command Line Tools (`xcode-select --install`) — needed to build a couple of
  Python packages from source.
- ~4GB free disk space for the model, and patience: CPU inference on a 2012 machine
  will take roughly 20 seconds to a couple of minutes per sentence. It works, it's just
  not real-time on hardware this old.

## Run it

```bash
cd voicebox-lite
bash run.sh
```

That's it — one command. It creates a virtual environment, installs everything pinned
to versions that still ship macOS x86_64 wheels, downloads the XTTS-v2 model on first
run, and opens the UI in your browser at `http://127.0.0.1:7860`.

Every run after the first is much faster since dependencies and the model are cached.

## Using the command-line version instead

```bash
source venv/bin/activate
python clone_voice.py --text "Hello there" --voice samples/my_voice.wav --lang en --out output/hello.wav
```

## Why versions are pinned the way they are

- `torch==2.2.2` / `torchaudio==2.2.2` — the **last** versions PyTorch published
  official wheels for on Intel macOS. Anything newer won't install without building
  PyTorch from source yourself (a multi-hour, easy-to-fail process).
- `coqui-tts==0.24.2` — a stable point in the actively-maintained XTTS-v2 fork that's
  compatible with torch 2.2.

## Troubleshooting

- **"No Python 3.10-3.12 found"** — see the Requirements section above.
- **pip install fails building a package** — run `xcode-select --install` first.
- **It's really slow** — that's expected on 2012-era CPUs with no GPU. Shorter
  sentences generate faster than long paragraphs.
- **Model download hangs** — it's ~2GB from Hugging Face; check your connection and
  just let `run.sh` finish, it resumes on re-run.
