#!/bin/bash

# ------------------------------------------------------------
# START FFmpeg SRT Caller STREAMING PROCESS
# ------------------------------------------------------------

BASE_DIR=/home/ubuntu/streaming-demo

# Input video file
VIDEO="$BASE_DIR/input/tempest_input.mp4"

# Log file for FFmpeg output
LOG="$BASE_DIR/logs/ffmpeg.log"

# PID file to track running process
PID_FILE="$BASE_DIR/logs/ffmpeg.pid"

# SRT streaming target
SRT_TARGET="srt://100.25.160.219:5000?mode=caller"


# ------------------------------------------------------------
# PREVENT DUPLICATE RUNS
# ------------------------------------------------------------
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")

    # If process exists, don't start again
    if ps -p "$PID" > /dev/null; then
        echo "FFmpeg already running with PID $PID"
        exit 0
    fi
fi


# ------------------------------------------------------------
# START FFmpeg PROCESS
# ------------------------------------------------------------
echo "Starting FFmpeg SRT caller..."

nohup ffmpeg -re -stream_loop -1 \
    -i "$VIDEO" \
    -c copy \
    -f mpegts \
    "$SRT_TARGET" \
    > "$LOG" 2>&1 &


# Save process ID
echo $! > "$PID_FILE"

echo "FFmpeg started with PID $(cat "$PID_FILE")"
echo "Logs: $LOG"
