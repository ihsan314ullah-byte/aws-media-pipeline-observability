#!/bin/bash

set -euo pipefail

# ---------------------------------------------------------------------------
# PATH RESOLUTION AND STATE FILES
# ---------------------------------------------------------------------------
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
PID_FILE="$LOG_DIR/ffmpeg.pid"
LOCK_FILE="$LOG_DIR/ffmpeg.lock"

mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# RECOVERY WHEN THE PID FILE IS MISSING
# ---------------------------------------------------------------------------
# A process may still exist if the PID file was manually removed or a previous
# operation was interrupted. Limit the fallback match to FFmpeg SRT commands.
if [ ! -f "$PID_FILE" ]; then
  echo "No FFmpeg PID file found."
  RUNNING_PIDS="$(pgrep -f "ffmpeg.*srt://" || true)"

  if [ -n "$RUNNING_PIDS" ]; then
    echo "Found FFmpeg SRT processes without PID file:"
    echo "$RUNNING_PIDS"
    echo "Stopping them..."

    # First request graceful shutdown, then force-kill remaining processes.
    pkill -TERM -f "ffmpeg.*srt://" || true
    sleep 3
    pkill -KILL -f "ffmpeg.*srt://" || true
  fi

  rm -f "$LOCK_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE" || true)"

# ---------------------------------------------------------------------------
# CLEAN STALE OR INVALID STATE
# ---------------------------------------------------------------------------
if [ -z "$PID" ]; then
  echo "PID file is empty. Cleaning up."
  rm -f "$PID_FILE" "$LOCK_FILE"
  exit 0
fi

if ! ps -p "$PID" > /dev/null; then
  echo "FFmpeg PID $PID is not running. Cleaning stale PID file."
  rm -f "$PID_FILE" "$LOCK_FILE"
  exit 0
fi

# ---------------------------------------------------------------------------
# GRACEFUL SHUTDOWN WITH FORCED FALLBACK
# ---------------------------------------------------------------------------
echo "Stopping FFmpeg PID $PID gracefully..."
kill -TERM "$PID" || true

# Wait up to ten seconds for FFmpeg to flush/close cleanly.
for i in {1..10}; do
  if ! ps -p "$PID" > /dev/null; then
    echo "FFmpeg stopped gracefully."
    rm -f "$PID_FILE" "$LOCK_FILE"
    exit 0
  fi

  sleep 1
done

echo "FFmpeg did not stop after 10 seconds. Force killing..."
kill -KILL "$PID" || true
sleep 1

rm -f "$PID_FILE" "$LOCK_FILE"
echo "FFmpeg stopped."
