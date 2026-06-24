#!/bin/bash

# ------------------------------------------------------------
# STREAMING SYSTEM STATUS SCRIPT
# ------------------------------------------------------------

# Path to FFmpeg PID file
PID_FILE=/home/ubuntu/streaming-demo/logs/ffmpeg.pid


echo "================================="
echo "STREAMING PIPELINE STATUS"
echo "================================="


# ------------------------------------------------------------
# FFmpeg STATUS CHECK
# ------------------------------------------------------------
echo ""
echo "[FFMPEG]"

# If PID file exists, we assume FFmpeg is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Status: RUNNING"
    echo "PID: $PID"
else
    echo "Status: NOT RUNNING"
fi


# ------------------------------------------------------------
# CPU USAGE
# ------------------------------------------------------------
echo ""
echo "[CPU]"

# top snapshot, extract CPU usage
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
echo "Usage: $CPU %"


# ------------------------------------------------------------
# MEMORY USAGE
# ------------------------------------------------------------
echo ""
echo "[MEMORY]"

# free memory calculation
free -m | awk 'NR==2{
    printf "Used: %s MB / %s MB (%.2f%%)\n", $3, $2, $3*100/$2
}'


# ------------------------------------------------------------
# DISK USAGE
# ------------------------------------------------------------
echo ""
echo "[DISK]"

df -h / | awk 'NR==2{
    print "Used:", $3, "/", $2, "(", $5 ")"
}'


# ------------------------------------------------------------
# NETWORK CHECK
# ------------------------------------------------------------
echo ""
echo "[NETWORK]"

# simple connectivity test using Google DNS
curl -s https://www.google.com > /dev/null

if [ $? -eq 0 ]; then
    echo "Internet: OK"
else
    echo "Internet: DOWN"
fi


echo ""
echo "================================="
