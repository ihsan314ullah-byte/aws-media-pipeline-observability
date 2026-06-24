#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VIDEO="$BASE_DIR/input/tempest_input.mp4"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/ffmpeg.log"
PID_FILE="$LOG_DIR/ffmpeg.pid"
LOCK_FILE="$LOG_DIR/ffmpeg.lock"

SRT_TARGET="srt://98.88.202.73:5000?mode=caller&latency=2000"

mkdir -p "$LOG_DIR"

if [ ! -f "$VIDEO" ]; then
    echo "ERROR: Input video not found: $VIDEO"
    exit 1
fi

if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" || true)"
    if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" -o comm= | grep -q "ffmpeg"; then
        echo "FFmpeg already running with PID $OLD_PID"
        exit 0
    else
        echo "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

if [ -f "$LOCK_FILE" ]; then
    echo "Removing stale lock file"
    rm -f "$LOCK_FILE"
fi

touch "$LOCK_FILE"

echo "Starting FFmpeg SRT caller..."
echo "Base dir: $BASE_DIR"
echo "Video: $VIDEO"
echo "Target: $SRT_TARGET"
echo "Log: $LOG_FILE"

: > "$LOG_FILE"

nohup ffmpeg -hide_banner -nostdin \
    -re \
    -stream_loop -1 \
    -i "$VIDEO" \
    -c copy \
    -f mpegts \
    "$SRT_TARGET" \
    >> "$LOG_FILE" 2>&1 &

PID=$!
echo "$PID" > "$PID_FILE"
rm -f "$LOCK_FILE"

sleep 2

if ps -p "$PID" > /dev/null; then
    echo "FFmpeg started successfully with PID $PID"
else
    echo "ERROR: FFmpeg failed to start. Last log lines:"
    tail -30 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
