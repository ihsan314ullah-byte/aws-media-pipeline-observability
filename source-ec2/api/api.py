"""
AWS Media Pipeline Observability API.

This FastAPI service is the control and observability layer for a host-managed
FFmpeg process. Although the API itself runs inside Docker, selected operations
enter the host namespaces and execute the Bash scripts stored on the EC2 host.

Main responsibilities:
- Serve the browser dashboard.
- Report FFmpeg and EC2 runtime state.
- Start and stop FFmpeg through protected administrator endpoints.
- Read non-secret playback/runtime values from the mounted .env file.
- Expose Prometheus text-format metrics.
"""

# ---------------------------------------------------------------------------
# STANDARD-LIBRARY IMPORTS
# ---------------------------------------------------------------------------
# os reads environment variables supplied by Docker Compose.
# re extracts bitrate and encoding speed from FFmpeg log lines.
# subprocess executes the host-side control scripts.
import os
import re
import subprocess

# pathlib provides platform-friendly file/path handling.
from pathlib import Path

# Type hints document the shape of dictionaries returned by helper functions.
from typing import Any, Dict

# ---------------------------------------------------------------------------
# THIRD-PARTY IMPORTS
# ---------------------------------------------------------------------------
# PyJWT validates signed administrator tokens.
import jwt

# psutil inspects processes and collects CPU/memory measurements.
import psutil

# FastAPI objects define routes, dependencies, headers, and HTTP errors.
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse


# ---------------------------------------------------------------------------
# APPLICATION AND RUNTIME PATH CONFIGURATION
# ---------------------------------------------------------------------------
app = FastAPI(title="AWS Media Pipeline Observability API")

# Resolve files copied beside api.py in the container image.
BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "dashboard.html"

# The API executes scripts in the HOST filesystem, not the container path.
# Docker Compose can override this value when the repository is installed at
# another host location.
HOST_PROJECT_DIR = os.getenv(
    "HOST_PROJECT_DIR",
    "/home/ubuntu/aws-media-pipeline-observability/source-ec2",
)

# The host logs directory is bind-mounted into the container at /app/logs.
LOG_FILE = Path("/app/logs/ffmpeg.log")

# Absolute host paths are passed after entering the host namespaces.
START_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/start_ffmpeg.sh"
STOP_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/stop_ffmpeg.sh"
STATUS_SCRIPT = f"{HOST_PROJECT_DIR}/scripts/status.sh"

# HS256 uses one shared secret for signing and verification. The secret is
# supplied at runtime and must never be committed to the repository.
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# JWT AUTHENTICATION AND ROLE-BASED ACCESS CONTROL
# ---------------------------------------------------------------------------
def verify_jwt_authorization(
    authorization: str = Header(default=""),
) -> Dict[str, Any]:
    """Validate a Bearer JWT and require the administrator role.

    FastAPI runs this function before any route that declares it with Depends.
    Returning the decoded payload lets the route include the authenticated
    subject and role in its response.
    """
    if not JWT_SECRET:
        # A missing server secret is a deployment/configuration failure.
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET is not configured on the server",
        )

    if not authorization.startswith("Bearer "):
        # Protected calls must use: Authorization: Bearer <token>
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.replace("Bearer ", "", 1).strip()

    try:
        # decode verifies the HS256 signature and standard expiry claim.
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        # Authentication alone is insufficient: control operations require an
        # explicit administrator role.
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Administrator privileges required",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# HOST-SCRIPT EXECUTION
# ---------------------------------------------------------------------------
def run_host_script(script_path: str) -> Dict[str, Any]:
    """Run a Bash script inside the EC2 host namespaces.

    PID 1 is the host init process because the container uses host PID mode.
    nsenter joins its mount, UTS, IPC, network, and PID namespaces, allowing
    the script to operate on the real host-managed FFmpeg process.
    """
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
        script_path,
    ]

    # Capture output for API responses and apply a timeout so a hung script
    # cannot occupy an API worker indefinitely.
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


# ---------------------------------------------------------------------------
# SIMPLE .ENV FILE READER
# ---------------------------------------------------------------------------
def load_dotenv_file() -> Dict[str, str]:
    """Read key/value pairs from the read-only .env bind mount.

    A small parser is sufficient because this endpoint only needs generated
    runtime values. Blank lines, comments, and malformed lines are ignored.
    """
    env_file = Path("/app/.env")
    config: Dict[str, str] = {}

    if not env_file.exists():
        return config

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        # Split once so values containing '=' are preserved.
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip().strip('"').strip("'")

    return config


# ---------------------------------------------------------------------------
# FFMPEG PROCESS DISCOVERY
# ---------------------------------------------------------------------------
def is_ffmpeg_running() -> int:
    """Return 1 when any visible process appears to be FFmpeg, otherwise 0.

    Integer output is intentional because Prometheus gauge samples are numeric.
    """
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = proc.info.get("name") or ""
            cmdline = " ".join(proc.info.get("cmdline") or [])

            if "ffmpeg" in name.lower() or "ffmpeg" in cmdline.lower():
                return 1

        # Processes can disappear or become inaccessible during iteration.
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return 0


# ---------------------------------------------------------------------------
# FFMPEG LOG METRIC EXTRACTION
# ---------------------------------------------------------------------------
def parse_ffmpeg_log() -> Dict[str, float]:
    """Extract the newest bitrate and speed values from FFmpeg progress logs."""
    bitrate_kbps = 0.0
    speed = 0.0

    if not LOG_FILE.exists():
        return {
            "ffmpeg_bitrate_kbps": bitrate_kbps,
            "ffmpeg_speed": speed,
        }

    try:
        # Reading only the tail limits work as the continuously written log
        # grows. Invalid byte sequences are ignored rather than failing status.
        lines = LOG_FILE.read_text(errors="ignore").splitlines()[-80:]
    except Exception:
        return {
            "ffmpeg_bitrate_kbps": bitrate_kbps,
            "ffmpeg_speed": speed,
        }

    # Search newest-to-oldest and stop after both measurements are found.
    for line in reversed(lines):
        bitrate_match = re.search(r"bitrate=\s*([\d.]+)kbits/s", line)
        speed_match = re.search(r"speed=\s*([\d.]+)x", line)

        if bitrate_match and bitrate_kbps == 0.0:
            bitrate_kbps = float(bitrate_match.group(1))

        if speed_match and speed == 0.0:
            speed = float(speed_match.group(1))

        if bitrate_kbps and speed:
            break

    # Old log values must not make a stopped stream look active.
    if not is_ffmpeg_running():
        bitrate_kbps = 0.0
        speed = 0.0

    return {
        "ffmpeg_bitrate_kbps": bitrate_kbps,
        "ffmpeg_speed": speed,
    }


# ---------------------------------------------------------------------------
# SHARED STATUS PAYLOAD
# ---------------------------------------------------------------------------
def get_status_payload() -> Dict[str, Any]:
    """Build the status object used by both JSON and Prometheus endpoints."""
    log_metrics = parse_ffmpeg_log()

    return {
        "service": "aws-media-pipeline-observability",
        "ffmpeg_running": is_ffmpeg_running(),
        "ffmpeg_bitrate_kbps": log_metrics["ffmpeg_bitrate_kbps"],
        "ffmpeg_speed": log_metrics["ffmpeg_speed"],
        # A short interval produces a current CPU percentage instead of the
        # first-call placeholder returned by a zero-length sample.
        "cpu_usage_percent": psutil.cpu_percent(interval=0.2),
        "memory_usage_percent": psutil.virtual_memory().percent,
    }


# ---------------------------------------------------------------------------
# PUBLIC DASHBOARD AND HEALTH ROUTES
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """Serve the operations dashboard at the API root."""
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_FILE)


@app.get("/health")
def health():
    """Lightweight container/orchestrator health response."""
    return {"status": "healthy"}


@app.get("/dashboard")
def dashboard():
    """Serve the same dashboard through an explicit route."""
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_FILE)


# ---------------------------------------------------------------------------
# PUBLIC STATUS ROUTES
# ---------------------------------------------------------------------------
@app.get("/status")
def status():
    """Return machine-readable runtime metrics for the dashboard."""
    return get_status_payload()


@app.get("/ffmpeg/status")
def ffmpeg_status():
    """Return the detailed, human-readable output of status.sh."""
    result = run_host_script(STATUS_SCRIPT)

    return {
        "script": "status.sh",
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


# ---------------------------------------------------------------------------
# ADMINISTRATOR-ONLY CONTROL ROUTES
# ---------------------------------------------------------------------------
@app.post("/ffmpeg/start")
def start_ffmpeg(
    auth: Dict[str, Any] = Depends(verify_jwt_authorization),
):
    """Start the host-managed FFmpeg process after JWT/RBAC validation."""
    result = run_host_script(START_SCRIPT)

    if result["returncode"] != 0:
        raise HTTPException(status_code=500, detail=result)

    return {
        "message": "FFmpeg start command executed",
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role"),
        "result": result,
    }


@app.post("/ffmpeg/stop")
def stop_ffmpeg(
    auth: Dict[str, Any] = Depends(verify_jwt_authorization),
):
    """Stop the host-managed FFmpeg process after JWT/RBAC validation."""
    result = run_host_script(STOP_SCRIPT)

    if result["returncode"] != 0:
        raise HTTPException(status_code=500, detail=result)

    return {
        "message": "FFmpeg stop command executed",
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role"),
        "result": result,
    }


@app.get("/runtime-config")
def runtime_config(
    auth: Dict[str, Any] = Depends(verify_jwt_authorization),
):
    """Return generated connection/playback values to an authorized dashboard."""
    config = load_dotenv_file()

    return {
        "srt_target_ip": config.get("SRT_TARGET_IP", ""),
        "srt_target_port": config.get("SRT_TARGET_PORT", ""),
        "srt_latency_ms": config.get("SRT_LATENCY_MS", ""),
        "hls_url": config.get("HLS_URL", ""),
        "dash_url": config.get("DASH_URL", ""),
        "auth_subject": auth.get("sub"),
        "auth_role": auth.get("role"),
    }


# ---------------------------------------------------------------------------
# PROMETHEUS SCRAPE ENDPOINT
# ---------------------------------------------------------------------------
@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Render runtime values in Prometheus exposition text format."""
    payload = get_status_payload()

    # HELP explains a series and TYPE identifies gauge semantics. Each sample
    # remains on its own line because Prometheus parses this response as text.
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
