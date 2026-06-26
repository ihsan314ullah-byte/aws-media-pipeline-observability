import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict

import jwt
import psutil
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse


app = FastAPI(title="AWS Media Pipeline Observability API")

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "dashboard.html"

HOST_PROJECT_DIR = os.getenv(
    "HOST_PROJECT_DIR",
    "/home/ubuntu/aws-media-pipeline-observability/source-ec2"
)

LOG_FILE = Path("/app/logs/ffmpeg.log")

START_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/start_ffmpeg.sh"
STOP_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/stop_ffmpeg.sh"
STATUS_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/status.sh"

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"


def verify_jwt_authorization(authorization: str = Header(default="")) -> Dict[str, Any]:
    if not JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET is not configured on the server"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.replace("Bearer ", "", 1).strip()

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Administrator privileges required"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def run_host_script(script_path: str) -> Dict[str, Any]:
    command = [
        "nsenter",
        "--target",
        "1",
        "--mount",
        "--uts",
        "--ipc",
        "--net",
        "--pid",
        "bash",
        script_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }


def load_dotenv_file() -> Dict[str, str]:
    env_file = Path("/app/.env")
    config = {}

    if not env_file.exists():
        return config

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        config[key.strip()] = value.strip().strip('"').strip("'")

    return config


def is_ffmpeg_running() -> int:
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = proc.info.get("name") or ""
            cmdline = " ".join(proc.info.get("cmdline") or [])

            if "ffmpeg" in name.lower() or "ffmpeg" in cmdline.lower():
                return 1

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return 0


def parse_ffmpeg_log() -> Dict[str, float]:
    bitrate_kbps = 0.0
    speed = 0.0

    if not LOG_FILE.exists():
        return {
            "ffmpeg_bitrate_kbps": bitrate_kbps,
            "ffmpeg_speed": speed
        }

    try:
        lines = LOG_FILE.read_text(errors="ignore").splitlines()[-80:]

    except Exception:
        return {
            "ffmpeg_bitrate_kbps": bitrate_kbps,
            "ffmpeg_speed": speed
        }

    for line in reversed(lines):
        bitrate_match = re.search(r"bitrate=\s*([\d.]+)kbits/s", line)
        speed_match = re.search(r"speed=\s*([\d.]+)x", line)

        if bitrate_match and bitrate_kbps == 0.0:
            bitrate_kbps = float(bitrate_match.group(1))

        if speed_match and speed == 0.0:
            speed = float(speed_match.group(1))

        if bitrate_kbps and speed:
            break

    if not is_ffmpeg_running():
        bitrate_kbps = 0.0
        speed = 0.0

    return {
        "ffmpeg_bitrate_kbps": bitrate_kbps,
        "ffmpeg_speed": speed
    }


def get_status_payload() -> Dict[str, Any]:
    log_metrics = parse_ffmpeg_log()

    return {
        "service": "aws-media-pipeline-observability",
        "ffmpeg_running": is_ffmpeg_running(),
        "ffmpeg_bitrate_kbps": log_metrics["ffmpeg_bitrate_kbps"],
        "ffmpeg_speed": log_metrics["ffmpeg_speed"],
        "cpu_usage_percent": psutil.cpu_percent(interval=0.2),
        "memory_usage_percent": psutil.virtual_memory().percent
    }


@app.get("/")
def root():
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_FILE)


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/dashboard")
def dashboard():
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_FILE)


@app.get("/status")
def status():
    return get_status_payload()


@app.get("/ffmpeg/status")
def ffmpeg_status():
    result = run_host_script(STATUS_SCRIPT)

    return {
        "script": "status.sh",
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"]
    }


@app.post("/ffmpeg/start")
def start_ffmpeg(auth: Dict[str, Any] = Depends(verify_jwt_authorization)):
    result = run_host_script(START_SCRIPT)

    if result["returncode"] != 0:
        raise HTTPException(
            status_code=500,
            detail=result
        )

    return {
        "message": "FFmpeg start command executed",
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role"),
        "result": result
    }


@app.post("/ffmpeg/stop")
def stop_ffmpeg(auth: Dict[str, Any] = Depends(verify_jwt_authorization)):
    result = run_host_script(STOP_SCRIPT)

    if result["returncode"] != 0:
        raise HTTPException(
            status_code=500,
            detail=result
        )

    return {
        "message": "FFmpeg stop command executed",
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role"),
        "result": result
    }


@app.get("/runtime-config")
def runtime_config(auth: Dict[str, Any] = Depends(verify_jwt_authorization)):
    config = load_dotenv_file()

    return {
        "srt_target_ip": config.get("SRT_TARGET_IP", ""),
        "srt_target_port": config.get("SRT_TARGET_PORT", ""),
        "srt_latency_ms": config.get("SRT_LATENCY_MS", ""),
        "hls_url": config.get("HLS_URL", ""),
        "dash_url": config.get("DASH_URL", ""),
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role")
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    payload = get_status_payload()

    metrics_text = f"""# HELP cpu_usage_percent Host CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {payload["cpu_usage_percent"]}

# HELP memory_usage_percent Host memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent {payload["memory_usage_percent"]}

# HELP ffmpeg_running Whether FFmpeg is running on the host
# TYPE ffmpeg_running gauge
ffmpeg_running {payload["ffmpeg_running"]}

# HELP ffmpeg_bitrate_kbps FFmpeg output bitrate in kbps
# TYPE ffmpeg_bitrate_kbps gauge
ffmpeg_bitrate_kbps {payload["ffmpeg_bitrate_kbps"]}

# HELP ffmpeg_speed FFmpeg encoding speed multiplier
# TYPE ffmpeg_speed gauge
ffmpeg_speed {payload["ffmpeg_speed"]}

# HELP srt_caller_process_active Whether the SRT caller process is active
# TYPE srt_caller_process_active gauge
srt_caller_process_active {payload["ffmpeg_running"]}
"""

    return metrics_text
