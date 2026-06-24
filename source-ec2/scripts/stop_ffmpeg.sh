#!/bin/bash

# ------------------------------------------------------------
# STOP FFmpeg SRT Caller STREAMING PROCESS
# ------------------------------------------------------------

PID_FILE=/home/ubuntu/streaming-demo/logs/ffmpeg.pid


# Check if PID file exists
if [ -f "$PID_FILE" ]; then

    PID=$(cat "$PID_FILE")

    echo "Stopping FFmpeg PID $PID"

    # Kill process
    kill "$PID"

    # Wait until process fully stops
    while ps -p "$PID" > /dev/null; do
        sleep 1
    done

    # Remove PID file after stopping
    rm "$PID_FILE"

    echo "FFmpeg stopped"

else
    echo "No FFmpeg PID found"
fi
