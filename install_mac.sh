#!/bin/bash
# Mac（予備）：毎時 11 分に動き、Windows が 70 分以上作業していないときだけ更新する。
# このフォルダのターミナルで実行： bash install_mac.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3)"
"$PY" -m pip install -q --user -r "$DIR/requirements.txt"
PLIST="$HOME/Library/LaunchAgents/com.course-progress.mac.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.course-progress.mac</string>
  <key>ProgramArguments</key><array>
    <string>$PY</string><string>$DIR/sync.py</string><string>--role</string><string>mac</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>StartCalendarInterval</key><dict><key>Minute</key><integer>11</integer></dict>
  <key>StandardOutPath</key><string>$DIR/mac.log</string>
  <key>StandardErrorPath</key><string>$DIR/mac.log</string>
</dict></plist>
EOF
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "入れました（毎時11分に確認します）。"
