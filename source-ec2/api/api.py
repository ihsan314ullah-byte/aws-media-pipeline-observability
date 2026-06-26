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

START_SCRIPT = "/app/scripts/start_ffmpeg.sh"
STOP_SCRIPT = "/app/scripts/stop_ffmpeg.sh"
STATUS_SCRIPT = "/app/scripts/status.sh"


def load_env_file(path="/app/.env"):
    if not os.path.exists(path):
        return

    with open(path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()


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

        stat_file = f"/proc/{pid}/stat"

        if not os.path.exists(stat_file):
            return 0

        with open(stat_file, "r", errors="ignore") as f:
            stat = f.read()

        parts = stat.split()

        if len(parts) > 2 and parts[2] == "Z":
            return 0

        cmdline_file = f"/proc/{pid}/cmdline"

        if os.path.exists(cmdline_file):
            with open(cmdline_file, "r", errors="ignore") as f:
                cmdline = f.read().replace("\x00", " ")

            if "ffmpeg" in cmdline:
                return 1

        return 0

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


def run_script(script_path, timeout_seconds=20):
    try:
        host_project_dir = os.getenv(
            "HOST_PROJECT_DIR",
            "/home/ubuntu/aws-media-pipeline-observability/source-ec2",
        )

        script_name = os.path.basename(script_path)
        host_script = f"{host_project_dir}/scripts/{script_name}"

        result = subprocess.run(
            [
                "nsenter",
                "--target",
                "1",
                "--mount",
                "--uts",
                "--ipc",
                "--net",
                "--pid",
                "--",
                "bash",
                "-lc",
                f"cd {host_project_dir} && {host_script}",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False,
        }

    except subprocess.TimeoutExpired as e:
        return {
            "returncode": 124,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "Command timed out",
            "timed_out": True,
        }

    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "timed_out": False,
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


@app.get("/runtime-config")
def runtime_config():
    return {
        "hls_url": os.getenv("HLS_URL", ""),
        "dash_url": os.getenv("DASH_URL", ""),
    }


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


@app.post("/ffmpeg/start")
def ffmpeg_start():
    result = run_script(START_SCRIPT, timeout_seconds=20)

    return {
        "action": "start",
        **result,
        "status": get_source_status(),
    }


@app.post("/ffmpeg/stop")
def ffmpeg_stop():
    result = run_script(STOP_SCRIPT, timeout_seconds=20)

    return {
        "action": "stop",
        **result,
        "status": get_source_status(),
    }


@app.get("/ffmpeg/status")
def ffmpeg_status():
    result = run_script(STATUS_SCRIPT, timeout_seconds=20)

    return {
        "action": "status",
        **result,
        "status": get_source_status(),
    }
