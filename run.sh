#!/bin/bash
# Voicebox Lite — one command to set up and launch.
set -e
cd "$(dirname "$0")"

echo "== Voicebox Lite setup =="

# Find a usable Python (XTTS needs 3.10, 3.11 or 3.12 — Catalina ships 3.9 or older, so we search)
PYBIN=""
for cand in python3.11 python3.10 python3.12 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    ver=$("$cand" -c 'import sys; print(sys.version_info[0], sys.version_info[1])' 2>/dev/null || echo "0 0")
    major=$(echo "$ver" | cut -d" " -f1)
    minor=$(echo "$ver" | cut -d" " -f2)
    if [ "$major" = "3" ] && [ "$minor" -ge 10 ] && [ "$minor" -le 12 ]; then
      PYBIN="$cand"
      break
    fi
  fi
done

if [ -z "$PYBIN" ]; then
  echo ""
  echo "!! No Python 3.10-3.12 found on this system."
  echo "   Catalina ships an older Python. Install a compatible one first, e.g.:"
  echo ""
  echo "     brew install pyenv"
  echo "     pyenv install 3.11.9"
  echo "     pyenv local 3.11.9"
  echo ""
  echo "   Then re-run:  bash run.sh"
  echo ""
  exit 1
fi

echo "Using $PYBIN ($($PYBIN --version))"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  "$PYBIN" -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies (this can take a few minutes on first run)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo ""
echo "== Launching Voicebox Lite =="
echo "First launch also downloads the XTTS-v2 model (~2GB) — be patient."
echo ""

export COQUI_TOS_AGREED=1
python app.py
