#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PID_FILE="$BASE_DIR/logs/ffmpeg.pid"
LOG_FILE="$BASE_DIR/logs/ffmpeg.log"

echo "================================="
echo "STREAMING PIPELINE STATUS"
echo "================================="

echo ""
echo "[FFMPEG]"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE" || true)"

    if [ -n "$PID" ] && ps -p "$PID" > /dev/null; then
        echo "Status: RUNNING"
        echo "PID: $PID"
        ps -p "$PID" -o pid,ppid,etime,%cpu,%mem,cmd
    else
        echo "Status: STALE PID FILE"
        echo "PID in file: $PID"
    fi
else
    echo "Status: NOT RUNNING"
fi

echo ""
echo "[CPU]"
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
echo "Usage: $CPU %"

echo ""
echo "[MEMORY]"
free -m | awk 'NR==2{
    printf "Used: %s MB / %s MB (%.2f%%)\n", $3, $2, $3*100/$2
}'

echo ""
echo "[DISK]"
df -h / | awk 'NR==2{
    print "Used:", $3, "/", $2, "(", $5 ")"
}'

echo ""
echo "================================="
