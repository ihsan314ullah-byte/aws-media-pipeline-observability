# Code Walkthrough — AWS Media Pipeline Observability

## 1. End-to-end control flow

The MP4 test source is managed by `start_ffmpeg.sh`. FFmpeg reads it in real
time, loops it indefinitely, keeps the original encoded streams with `-c copy`,
wraps them in MPEG-TS, and opens an SRT caller connection to AWS MediaConnect.

FastAPI runs in Docker but FFmpeg runs on the EC2 host. The API container uses
host PID mode, privileged mode, and `nsenter` to invoke the host scripts. This
separation allows containerized observability/control while keeping the media
process directly managed by the host.

## 2. Authentication and RBAC

Protected endpoints declare `Depends(verify_jwt_authorization)`. FastAPI runs
that dependency before the endpoint. The dependency checks the Bearer header,
verifies the HS256 signature/expiry, and then requires `role == "admin"`.
HTTP 401 represents missing/invalid authentication; HTTP 403 represents an
authenticated user who lacks administrator permission.

## 3. FFmpeg state handling

`start_ffmpeg.sh` stores the background process ID in `logs/ffmpeg.pid`.
Before starting another process it verifies whether that PID still identifies
FFmpeg. Stale PID and lock files are removed.

`stop_ffmpeg.sh` first sends SIGTERM and waits up to ten seconds, allowing
FFmpeg to close gracefully. SIGKILL is only the fallback. It also searches for
an SRT FFmpeg command when the PID file is missing.

`status.sh` distinguishes a healthy FFmpeg process from a zombie, a reused PID,
and an absent process. It also prints CPU, memory, and root-disk snapshots.

## 4. Metrics

The API uses psutil for CPU, memory, and process inspection. It scans the last
80 FFmpeg log lines in reverse, using regular expressions to capture the newest
`bitrate=...kbits/s` and `speed=...x` values. When FFmpeg is not running, those
values are reset to zero so old log output does not become misleading.

The `/metrics` route emits Prometheus exposition text. Prometheus discovers the
API through Docker Compose DNS at `metrics-api:8000` and scrapes every five
seconds. Grafana then queries Prometheus and can also use its provisioned
CloudWatch datasource for AWS Media Services metrics.

## 5. Important design trade-offs

- `privileged: true` and host PID access are powerful permissions. They are
  justified here by the host-control design, but the API should be network
  restricted and the JWT secret protected.
- A hard-coded Grafana development password should be replaced with a secret
  for any non-demo deployment.
- The process scan matches any visible FFmpeg process. A stricter production
  version could match the SRT target or the stored PID specifically.
- Runtime configuration is mounted read-only, reducing accidental changes from
  inside the API container.
