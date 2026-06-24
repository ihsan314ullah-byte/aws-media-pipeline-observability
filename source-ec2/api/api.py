from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import subprocess
import os
import re

app = FastAPI()

LOG_FILE = "/app/logs/ffmpeg.log"
PID_FILE = "/app/logs/ffmpeg.pid"


def run(cmd):
    try:
        return subprocess.getoutput(cmd).strip()
    except Exception:
        return ""


def extract_ffmpeg_metrics():
    bitrate = 0.0
    speed = 0.0

    if not os.path.exists(LOG_FILE):
        return bitrate, speed

    try:
        with open(LOG_FILE, "r", errors="ignore") as f:
            log = f.read()

        bitrate_matches = re.findall(r"bitrate=\s*([\d\.]+)\s*kbits/s", log)
        if bitrate_matches:
            bitrate = float(bitrate_matches[-1])

        speed_matches = re.findall(r"speed=\s*([\d\.]+)x", log)
        if speed_matches:
            speed = float(speed_matches[-1])
    except Exception:
        pass

    return bitrate, speed


def is_ffmpeg_running():
    if not os.path.exists(PID_FILE):
        return 0

    try:
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()

        if not pid.isdigit():
            return 0

        return 1 if os.path.exists(f"/host/proc/{pid}") else 0
    except Exception:
        return 0


@app.get("/")
def root():
    return {
        "service": "EC2 FFmpeg SRT Source Metrics API",
        "health": "/health",
        "status": "/status",
        "metrics": "/metrics",
    }


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():

    ffmpeg_running = is_ffmpeg_running()

    if ffmpeg_running:
        bitrate, speed = extract_ffmpeg_metrics()
    else:
        bitrate, speed = 0.0, 0.0

    cpu = run("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")

    memory = run(
        "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'"
    )

    return {
        "ffmpeg_running": bool(ffmpeg_running),
        "ffmpeg_bitrate_kbps": bitrate,
        "ffmpeg_speed": speed,
        "cpu_usage_percent": cpu,
        "memory_usage_percent": memory
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    cpu = run("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")
    memory = run("free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'")

    ffmpeg_running = is_ffmpeg_running()

    if ffmpeg_running:
        bitrate, speed = extract_ffmpeg_metrics()
    else:
        bitrate, speed = 0.0, 0.0

    srt_caller_process_active = ffmpeg_running
    
    return (
        f"cpu_usage_percent {cpu or 0}\n"
        f"memory_usage_percent {memory or 0}\n"
        f"ffmpeg_running {ffmpeg_running}\n"
        f"ffmpeg_bitrate_kbps {bitrate}\n"
        f"ffmpeg_speed {speed}\n"
        f"srt_caller_process_active {srt_caller_process_active}\n"
    )
