#!/bin/bash

set -euo pipefail

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$BASE_DIR/logs/ffmpeg.pid"
LOG_FILE="$BASE_DIR/logs/ffmpeg.log"

echo "================================="
echo "STREAMING PIPELINE STATUS"
echo "================================="
echo ""

# ---------------------------------------------------------------------------
# FFMPEG PROCESS STATUS
# ---------------------------------------------------------------------------
echo "[FFMPEG]"

if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" || true)"

  if [ -n "$PID" ] && ps -p "$PID" > /dev/null; then
    # stat identifies zombie processes; cmd verifies that a reused PID still
    # belongs to FFmpeg rather than an unrelated process.
    PROCESS_STATE="$(ps -p "$PID" -o stat= | awk '{print $1}')"
    PROCESS_CMD="$(ps -p "$PID" -o cmd= || true)"

    if echo "$PROCESS_STATE" | grep -q "Z"; then
      echo "Status: STALE PID FILE"
      echo "PID in file: $PID"
      echo "Reason: FFmpeg process is defunct/zombie"
    elif echo "$PROCESS_CMD" | grep -q "ffmpeg"; then
      echo "Status: RUNNING"
      echo "PID: $PID"
      ps -p "$PID" -o pid,ppid,etime,%cpu,%mem,stat,cmd
    else
      echo "Status: STALE PID FILE"
      echo "PID in file: $PID"
      echo "Reason: PID exists but is not FFmpeg"
    fi
  else
    echo "Status: STALE PID FILE"
    echo "PID in file: $PID"
  fi
else
  echo "Status: NOT RUNNING"
fi

# ---------------------------------------------------------------------------
# HOST RESOURCE SNAPSHOT
# ---------------------------------------------------------------------------
echo ""
echo "[CPU]"
# top reports user and system CPU separately; adding fields 2 and 4 gives the
# combined active percentage used by this human-readable diagnostic.
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
echo "Usage: $CPU %"

echo ""
echo "[MEMORY]"
free -m | awk 'NR==2{ printf "Used: %s MB / %s MB (%.2f%%)\n", $3, $2, $3*100/$2 }'

echo ""
echo "[DISK]"
df -h / | awk 'NR==2{ print "Used:", $3, "/", $2, "(", $5 ")" }'

echo ""
echo "================================="
