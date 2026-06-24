from pathlib import Path
import os
import re
import subprocess

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

app = FastAPI()

LOG_FILE = "/app/logs/ffmpeg.log"
PID_FILE = "/app/logs/ffmpeg.pid"
DASHBOARD_FILE = Path("/app/dashboard.html")


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


def get_source_status():
    ffmpeg_running = is_ffmpeg_running()

    if ffmpeg_running:
        bitrate, speed = extract_ffmpeg_metrics()
    else:
        bitrate, speed = 0.0, 0.0

    cpu = run("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")
    memory = run("free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'")

    return {
        "ffmpeg_running": bool(ffmpeg_running),
        "ffmpeg_bitrate_kbps": bitrate,
        "ffmpeg_speed": speed,
        "cpu_usage_percent": cpu or "0",
        "memory_usage_percent": memory or "0",
    }


@app.get("/", response_class=HTMLResponse)
def root():
    if DASHBOARD_FILE.exists():
        return DASHBOARD_FILE.read_text()
    return "<h1>Dashboard file not found</h1>"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return get_source_status()


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    data = get_source_status()

    ffmpeg_running = 1 if data["ffmpeg_running"] else 0
    srt_caller_process_active = ffmpeg_running

    return (
        f"cpu_usage_percent {data['cpu_usage_percent']}\n"
        f"memory_usage_percent {data['memory_usage_percent']}\n"
        f"ffmpeg_running {ffmpeg_running}\n"
        f"ffmpeg_bitrate_kbps {data['ffmpeg_bitrate_kbps']}\n"
        f"ffmpeg_speed {data['ffmpeg_speed']}\n"
        f"srt_caller_process_active {srt_caller_process_active}\n"
    )
