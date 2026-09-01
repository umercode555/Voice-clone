#!/bin/bash
# ONE-TIME SETUP. After this, Voicebox Lite Cloud starts automatically every
# time you log into this Mac, and restarts itself automatically if it ever
# crashes. You never need to open VS Code, Terminal, or run any command
# again to use it.
#
# The only things that stop it: the Mac being fully powered off, or asleep.
# Sleep isn't something any app can override - macOS itself pauses
# everything when the lid closes without power+external display. When the
# Mac wakes back up or you log back in, this restarts itself with no action
# from you.

set -e
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
PLIST="$HOME/Library/LaunchAgents/com.voiceboxlite.cloud.plist"

if [ -z "$HF_TOKEN" ]; then
  echo "!! HF_TOKEN is not set in this shell."
  echo "   Run:  export HF_TOKEN=your_token_here"
  echo "   then re-run this installer (one time only)."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.voiceboxlite.cloud</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_DIR}/venv/bin/python</string>
        <string>${PROJECT_DIR}/app_cloud.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HF_TOKEN</key>
        <string>${HF_TOKEN}</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/cloud.log</string>

    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/cloud.log</string>
</dict>
</plist>
EOF

# Free the port in case something old is still running, then load the service
lsof -ti:7861 | xargs kill -9 2>/dev/null || true
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

sleep 2
echo ""
echo "Installed and running permanently."
echo "It will now auto-start every time you log into this Mac, forever, and"
echo "auto-restart itself if it ever crashes. No further action needed."
echo ""
echo "Open it any time at:  http://127.0.0.1:7861"
echo "Logs:                 ${PROJECT_DIR}/cloud.log"
echo ""
echo "(Only needed if something goes wrong: to stop it permanently, run"
echo " launchctl unload ~/Library/LaunchAgents/com.voiceboxlite.cloud.plist)"