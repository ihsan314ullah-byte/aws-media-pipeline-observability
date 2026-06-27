# AWS Media Pipeline Observability Lab

End-to-end live streaming and observability lab using AWS Media Services, FFmpeg, FastAPI, Prometheus, Grafana, CloudWatch, JWT authentication, and RBAC.

## What This Project Demonstrates

This project shows how to operate and monitor a live media pipeline using both custom runtime metrics and AWS service metrics.

The pipeline includes:

* EC2-hosted FFmpeg source
* SRT caller ingest
* AWS MediaConnect SRT listener
* AWS MediaLive processing
* AWS MediaPackage HLS/DASH delivery
* FastAPI operations dashboard
* Prometheus runtime metrics
* Grafana dashboards
* CloudWatch metrics for AWS Media Services
* JWT authentication
* Role-Based Access Control

## Companion Infrastructure Repository

AWS infrastructure is maintained in the companion Terraform repository:

```text
https://github.com/ihsan314ullah-byte/terraform-aws-mediaservices
```

That repository is responsible for:

* MediaConnect
* MediaLive
* MediaPackage
* HLS endpoint
* DASH endpoint
* IAM resources
* Terraform outputs
* Runtime `.env` generation

## Architecture

```text
OBS / Video File
        |
        v
FFmpeg on EC2
        |
        v
SRT Caller
        |
        v
AWS MediaConnect SRT Listener
        |
        v
AWS MediaLive
        |
        v
AWS MediaPackage
        |
        v
HLS / DASH ABR Playback
```

## Observability Flow

```text
Host Runtime Metrics
FFmpeg + EC2 + FastAPI
        |
        v
Prometheus
        |
        v
Grafana
```

```text
AWS Media Service Metrics
MediaConnect + MediaLive + MediaPackage
        |
        v
CloudWatch
        |
        v
Grafana
```

## Project Structure

```text
aws-media-pipeline-observability/
├── README.md
├── dashboards/
├── docs/
├── scripts/
└── source-ec2/
    ├── api/
    │   ├── api.py
    │   ├── dashboard.html
    │   ├── Dockerfile
    │   └── requirements.txt
    ├── docker-compose.yml
    ├── grafana/
    │   ├── dashboards/
    │   └── provisioning/
    ├── input/
    │   └── tempest_input.mp4
    ├── logs/
    ├── prometheus/
    │   └── prometheus.yml
    └── scripts/
        ├── start_ffmpeg.sh
        ├── stop_ffmpeg.sh
        └── status.sh
```

## Runtime Components

| Component      | Purpose                                            |
| -------------- | -------------------------------------------------- |
| FFmpeg         | Sends video as SRT caller to MediaConnect          |
| FastAPI        | Provides dashboard, control endpoints, and metrics |
| Prometheus     | Scrapes FastAPI runtime metrics                    |
| Grafana        | Visualizes Prometheus and CloudWatch metrics       |
| CloudWatch     | Provides AWS Media Services metrics                |
| Docker Compose | Runs FastAPI, Prometheus, and Grafana              |

## Fresh EC2 Setup

Install base packages:

```bash
sudo apt update
sudo apt install -y git ffmpeg tree curl unzip
```

Install Docker:

```bash
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

Log out and log back in after adding the `ubuntu` user to the Docker group.

Clone the repository:

```bash
cd ~
git clone https://github.com/ihsan314ullah-byte/aws-media-pipeline-observability.git
cd aws-media-pipeline-observability/source-ec2
```

Ensure scripts are executable:

```bash
chmod +x scripts/*.sh
```

Create required runtime directories if missing:

```bash
mkdir -p logs data
```

## Runtime Configuration

After provisioning AWS Media Services from the Terraform repository, generate the runtime `.env` file there and copy it into:

```text
source-ec2/.env
```

The `.env` file should include values such as:

```text
SRT_TARGET_IP=
SRT_TARGET_PORT=5000
SRT_LATENCY_MS=2000
HLS_URL=
DASH_URL=
JWT_SECRET=
```

## Start the Runtime Stack

From the `source-ec2` directory:

```bash
cd ~/aws-media-pipeline-observability/source-ec2
docker compose up -d
docker compose ps
```

Expected services:

```text
metrics-api
prometheus
grafana
```

## Main URLs

Replace `<EC2_PUBLIC_IP>` with the public IP of the source EC2 instance.

| Service           | URL                                     |
| ----------------- | --------------------------------------- |
| FastAPI dashboard | `http://<EC2_PUBLIC_IP>:8000/dashboard` |
| FastAPI metrics   | `http://<EC2_PUBLIC_IP>:8000/metrics`   |
| Prometheus        | `http://<EC2_PUBLIC_IP>:9090`           |
| Grafana           | `http://<EC2_PUBLIC_IP>:3000`           |

Grafana default credentials:

```text
Username: admin
Password: admin123
```

## Start and Stop FFmpeg

Start FFmpeg:

```bash
cd ~/aws-media-pipeline-observability/source-ec2
./scripts/start_ffmpeg.sh
```

Stop FFmpeg:

```bash
./scripts/stop_ffmpeg.sh
```

Check status:

```bash
./scripts/status.sh
```

FFmpeg can also be controlled from the FastAPI dashboard using a valid admin JWT.

## Metrics

Prometheus runtime metrics include:

```text
cpu_usage_percent
memory_usage_percent
ffmpeg_running
ffmpeg_bitrate_kbps
ffmpeg_speed
srt_caller_process_active
```

CloudWatch/Grafana metrics include:

```text
MediaConnect SourceBitRate
MediaConnect SourcePacketLossPercent
MediaLive ActiveAlerts
MediaLive InputVideoFrameRate
MediaLive NetworkIn
MediaPackage RequestCount
MediaPackage egress-related metrics, when available
```

## Grafana Dashboard Design

Recommended dashboard layout:

```text
Host Runtime Observability
- EC2 CPU
- EC2 memory
- FFmpeg running
- FFmpeg bitrate
- FFmpeg speed
- SRT caller process active
```

```text
AWS Media Services Observability
- MediaConnect metrics
- MediaLive metrics
- MediaPackage metrics
```

```text
End-to-End Live Pipeline Demo
- FFmpeg running
- FFmpeg bitrate
- MediaConnect source bitrate
- MediaLive active alerts
- MediaLive input frame rate
- MediaPackage request count
```

## CloudWatch Access

The EC2 instance should have an IAM role attached with CloudWatch read permissions.

Recommended policy:

```text
CloudWatchReadOnlyAccess
```

Verify from EC2:

```bash
aws sts get-caller-identity
aws cloudwatch list-metrics --region us-east-1 --max-items 5
```

Do not use long-lived AWS access keys on the EC2 instance. Use an IAM instance profile instead.

## JWT Authentication and RBAC

The FastAPI dashboard uses JWT authentication to protect administrative operations.

Roles:

| Role   | Access                                             |
| ------ | -------------------------------------------------- |
| admin  | Full operational access                            |
| viewer | Read-only access; administrative operations denied |

Protected admin endpoints:

```text
POST /ffmpeg/start
POST /ffmpeg/stop
GET  /runtime-config
```

Public endpoints:

```text
GET /
GET /dashboard
GET /health
GET /status
GET /ffmpeg/status
GET /metrics
```

## Generate Admin Token

Run from the `source-ec2` directory:

```bash
cd ~/aws-media-pipeline-observability/source-ec2

python3 - <<'PY'
import jwt
import datetime
from pathlib import Path

secret = ""

for line in Path(".env").read_text().splitlines():
    if line.startswith("JWT_SECRET="):
        secret = line.split("=", 1)[1].strip()
        break

payload = {
    "sub": "ihsan",
    "role": "admin",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
}

print(jwt.encode(payload, secret, algorithm="HS256"))
PY
```

Paste the generated token into the dashboard JWT field.

## Generate Viewer Token

```bash
cd ~/aws-media-pipeline-observability/source-ec2

python3 - <<'PY'
import jwt
import datetime
from pathlib import Path

secret = ""

for line in Path(".env").read_text().splitlines():
    if line.startswith("JWT_SECRET="):
        secret = line.split("=", 1)[1].strip()
        break

payload = {
    "sub": "viewer",
    "role": "viewer",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
}

print(jwt.encode(payload, secret, algorithm="HS256"))
PY
```

## Expected RBAC Behavior

| Token         | Expected Result                       |
| ------------- | ------------------------------------- |
| No token      | 401 Unauthorized                      |
| Invalid token | 401 Unauthorized                      |
| Expired token | 401 Token expired                     |
| Viewer token  | 403 Administrator privileges required |
| Admin token   | Allowed for protected operations      |

## Demo Workflow

1. Open the FastAPI dashboard.

```text
http://<EC2_PUBLIC_IP>:8000/dashboard
```

2. Generate an admin JWT.

3. Paste the token into the dashboard JWT field.

4. Start FFmpeg.

5. Verify:

```text
FFmpeg running = 1
FFmpeg bitrate rises
MediaConnect source bitrate rises
MediaLive active alerts drop
MediaLive input frame rate appears
HLS/DASH playback works
MediaPackage request metrics move when playback starts
```

6. Stop FFmpeg.

7. Verify:

```text
FFmpeg running = 0
MediaLive active alerts return
```

8. Generate a viewer JWT.

9. Attempt protected operations.

Expected result:

```text
Viewer token is blocked with 403 Forbidden.
```

## Useful Commands

Check containers:

```bash
docker compose ps
```

Restart services:

```bash
docker compose restart
```

Restart only Grafana:

```bash
docker compose restart grafana
```

View FastAPI logs:

```bash
docker logs metrics-api --tail 100
```

View FFmpeg log:

```bash
tail -f logs/ffmpeg.log
```

Check Git status:

```bash
git status
```

## Cleanup Warning

Do not run this unless you intentionally want to delete Grafana and Prometheus stored data:

```bash
docker compose down -v
```

Use this for normal stop/start:

```bash
docker compose down
docker compose up -d
```

## Current Status

Completed:

* Host-managed FFmpeg
* FastAPI dashboard
* Prometheus runtime metrics
* Grafana dashboards
* CloudWatch datasource
* AWS Media Services metrics
* JWT authentication
* RBAC
* Dashboard provisioning
* GitHub checkpoint

Next documentation improvements should go under:

```text
docs/
├── architecture.md
├── deployment.md
├── demo-guide.md
├── troubleshooting.md
└── screenshots/
```
