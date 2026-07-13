#!/bin/bash

# Fail on command errors, undefined variables, and failures inside pipelines.
# This prevents a partially configured stream from being launched.
set -euo pipefail

# ---------------------------------------------------------------------------
# PROJECT PATHS AND RUNTIME FILES
# ---------------------------------------------------------------------------
# BASH_SOURCE points to this script. Moving one directory upward resolves the
# source-ec2 project root regardless of the caller's current working directory.
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

VIDEO="$BASE_DIR/input/tempest_input.mp4"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/ffmpeg.log"
PID_FILE="$LOG_DIR/ffmpeg.pid"
LOCK_FILE="$LOG_DIR/ffmpeg.lock"
ENV_FILE="$BASE_DIR/.env"

# ---------------------------------------------------------------------------
# LOAD GENERATED RUNTIME CONFIGURATION
# ---------------------------------------------------------------------------
# set -a automatically exports variables loaded with source so the launched
# FFmpeg process receives them. set +a restores normal shell behavior.
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

# Apply safe defaults while requiring Terraform's target IP.
SRT_TARGET_IP="${SRT_TARGET_IP:-}"
SRT_TARGET_PORT="${SRT_TARGET_PORT:-5000}"
SRT_LATENCY_US="${SRT_LATENCY_US:-2000000}"

# FFmpeg's SRT latency URL option is expressed in microseconds here:
# 2,000,000 microseconds = 2 seconds.
if [ -z "$SRT_TARGET_IP" ]; then
  echo "ERROR: SRT_TARGET_IP is not set."
  echo "Create source-ec2/.env from source-ec2/.env.example and set Terraform output source_ingest_ip."
  exit 1
fi

# caller mode makes this EC2 host initiate the SRT connection to MediaConnect.
SRT_TARGET="srt://${SRT_TARGET_IP}:${SRT_TARGET_PORT}?mode=caller&latency=${SRT_LATENCY_US}"

mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# PRE-FLIGHT VALIDATION
# ---------------------------------------------------------------------------
if [ ! -f "$VIDEO" ]; then
  echo "ERROR: Input video not found: $VIDEO"
  exit 1
fi

# Prevent duplicate FFmpeg processes. A PID file is trusted only when that PID
# still belongs to an FFmpeg process; otherwise it is stale and removed.
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

# A lock left behind by an interrupted earlier launch must not block recovery.
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

# Truncate the previous run's log so displayed metrics belong to this launch.
: > "$LOG_FILE"

# ---------------------------------------------------------------------------
# BACKGROUND FFMPEG LAUNCH
# ---------------------------------------------------------------------------
# -re: read input at its native rate rather than as fast as possible.
# -stream_loop -1: replay the test asset forever.
# -c copy: remux existing streams without CPU-expensive re-encoding.
# -f mpegts: package the stream as MPEG-TS for SRT transport.
# nohup + &: keep FFmpeg alive after the API/script process exits.
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

# Give FFmpeg enough time to fail fast on invalid input/network configuration.
sleep 2

if ps -p "$PID" > /dev/null; then
  echo "FFmpeg started successfully with PID $PID"
else
  echo "ERROR: FFmpeg failed to start."
  echo "Last log lines:"
  tail -30 "$LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
fi
