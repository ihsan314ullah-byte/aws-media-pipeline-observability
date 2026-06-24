from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import subprocess
import os
import re

app = FastAPI()

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

LOG_FILE = "/home/ubuntu/streaming-demo/logs/ffmpeg.log"
PID_FILE = "/home/ubuntu/streaming-demo/logs/ffmpeg.pid"


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def run(cmd):
    """Safe shell command runner"""
    try:
        return subprocess.getoutput(cmd)
    except:
        return ""


def extract_ffmpeg_metrics():

    bitrate = 0.0
    speed = 0.0

    if not os.path.exists(LOG_FILE):
        return bitrate, speed

    try:
        with open(LOG_FILE, "r") as f:
            log = f.read()

        # --------------------------------------------------------
        # BITRATE (last occurrence)
        # Example: bitrate=4290.7kbits/s
        # --------------------------------------------------------
        bitrate_matches = re.findall(r'bitrate=\s*([\d\.]+)\s*kbits/s', log)
        if bitrate_matches:
            bitrate = float(bitrate_matches[-1])

        # --------------------------------------------------------
        # SPEED (last occurrence)
        # Example: speed=1x
        # --------------------------------------------------------
        speed_matches = re.findall(r'speed=\s*([\d\.]+)x', log)
        if speed_matches:
            speed = float(speed_matches[-1])

    except:
        pass

    return bitrate, speed


# ------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------
# METRICS
# ------------------------------------------------------------

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():

    # --------------------------------------------------------
    # SYSTEM METRICS
    # --------------------------------------------------------

    cpu = run("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")

    memory = run(
        "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'"
    )

    # --------------------------------------------------------
    # FFMPEG STATE
    # --------------------------------------------------------

    ffmpeg_running = 1 if os.path.exists(PID_FILE) else 0

    # --------------------------------------------------------
    # STREAM QUALITY METRICS (FROM LOG)
    # --------------------------------------------------------

    bitrate, speed = extract_ffmpeg_metrics()

    # --------------------------------------------------------
    # SRT ACTIVITY (basic heuristic)
    # --------------------------------------------------------

    srt_active = 1 if run("ss -anu | grep ':5000'") else 0

    # --------------------------------------------------------
    # OUTPUT PROMETHEUS FORMAT
    # --------------------------------------------------------

    return (
        f"cpu_usage_percent {cpu}\n"
        f"memory_usage_percent {memory}\n"
        f"ffmpeg_running {ffmpeg_running}\n"
        f"ffmpeg_bitrate_kbps {bitrate}\n"
        f"ffmpeg_speed {speed}\n"
        f"srt_active {srt_active}\n"
    )
