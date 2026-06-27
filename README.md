# AWS Media Pipeline Observability

End-to-end live streaming and observability using AWS Media Services, FFmpeg, FastAPI, Prometheus, Grafana, CloudWatch, JWT authentication, and role-based access control.

This repository contains the **runtime and observability layer** of the project. AWS infrastructure is provisioned separately in the companion Terraform repository:

```text
https://github.com/ihsan314ullah-byte/terraform-aws-mediaservices
```

## Project Overview

This project demonstrates how to run, control, and monitor a live media pipeline using a combination of host-level runtime metrics and AWS Media Services metrics.

The system sends a local MP4 video file through FFmpeg as an SRT caller into AWS MediaConnect. AWS MediaLive processes the input and sends the output to AWS MediaPackage for HLS/DASH playback.

Prometheus collects runtime metrics from the FastAPI application, while Grafana visualizes both Prometheus metrics and AWS CloudWatch metrics.

## Architecture

```text
MP4 Video File
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
HLS / DASH Playback
```

## Observability Flow

```text
FFmpeg + EC2 Runtime Metrics
        |
        v
FastAPI /metrics endpoint
        |
        v
Prometheus
        |
        v
Grafana
```

```text
AWS Media Services Metrics
        |
        v
CloudWatch
        |
        v
Grafana
```

## Companion Terraform Repository

The companion repository provisions the AWS infrastructure and generates the runtime `.env` file used by this repository.

That repository is responsible for:

* AWS MediaConnect
* AWS MediaLive
* AWS MediaPackage
* IAM resources
* HLS endpoint
* DASH endpoint
* Terraform outputs
* Runtime `.env` generation

This repository is responsible for:

* Host-managed FFmpeg
* FastAPI operations API
* HTML operations dashboard
* Prometheus runtime metrics
* Grafana visualization
* CloudWatch datasource integration
* JWT authentication
* Admin/viewer RBAC
* Runtime documentation

## Features

* Host-managed FFmpeg SRT caller workflow
* FastAPI dashboard for runtime visibility
* FFmpeg start/stop/status operations
* Prometheus-compatible `/metrics` endpoint
* Grafana dashboard support
* CloudWatch datasource support
* JWT-based authentication
* Admin and viewer RBAC roles
* Docker Compose runtime stack
* Persistent Grafana/Prometheus data volumes
* Documentation for deployment, architecture, and troubleshooting

## Repository Structure

```text
aws-media-pipeline-observability/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   └── troubleshooting.md
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

| Component      | Purpose                                                          |
| -------------- | ---------------------------------------------------------------- |
| FFmpeg         | Sends the source video to AWS MediaConnect using SRT caller mode |
| FastAPI        | Provides dashboard, runtime API, control endpoints, and metrics  |
| Prometheus     | Scrapes FastAPI runtime metrics                                  |
| Grafana        | Visualizes Prometheus and CloudWatch metrics                     |
| CloudWatch     | Provides AWS Media Services metrics                              |
| Docker Compose | Runs FastAPI, Prometheus, and Grafana together                   |

## Prerequisites

A fresh Ubuntu EC2 instance should have:

* Git
* Docker
* Docker Compose
* FFmpeg
* curl
* unzip

The EC2 instance should also have the required security group rules for:

* SSH
* FastAPI dashboard
* Prometheus
* Grafana
* SRT traffic, if applicable to the test setup

The AWS Media Services infrastructure must be provisioned from the companion Terraform repository before FFmpeg can send traffic into MediaConnect.

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

Clone this repository:

```bash
cd ~
git clone https://github.com/ihsan314ullah-byte/aws-media-pipeline-observability.git
cd aws-media-pipeline-observability/source-ec2
```

Ensure scripts are executable:

```bash
chmod +x scripts/*.sh
```

The `logs/` and `data/` directories are included in the repository using `.gitkeep` files. If they are ever missing on a fresh EC2 instance, recreate them with:

```bash
mkdir -p logs data
```

## Runtime Configuration

This repository requires a runtime `.env` file at:

```text
source-ec2/.env
```

The `.env` file is generated from Terraform outputs in the companion infrastructure repository.

On the machine where the Terraform repository is managed:

```bash
cd terraform-aws-mediaservices
./generate-runtime-env.ps1
```

Then copy the generated `.env` file to the EC2 instance running this repository:

```bash
scp -i /path/to/key.pem .env ubuntu@<EC2_PUBLIC_IP>:~/aws-media-pipeline-observability/source-ec2/.env
```

On the EC2 instance, verify the file:

```bash
cd ~/aws-media-pipeline-observability/source-ec2
cat .env
```

Expected values include:

```text
SRT_TARGET_IP=
SRT_TARGET_PORT=5000
SRT_LATENCY_MS=2000
HLS_URL=
DASH_URL=
JWT_SECRET=
```

Do not commit the real `.env` file to GitHub.

A template is provided at:

```text
source-ec2/.env.example
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

## FFmpeg Runtime Control

Start FFmpeg:

```bash
cd ~/aws-media-pipeline-observability/source-ec2
./scripts/start_ffmpeg.sh
```

Stop FFmpeg:

```bash
./scripts/stop_ffmpeg.sh
```

Check FFmpeg and host status:

```bash
./scripts/status.sh
```

FFmpeg can also be controlled from the FastAPI dashboard using a valid admin JWT.

## FastAPI Endpoints

Public endpoints:

```text
GET /
GET /dashboard
GET /status
GET /ffmpeg/status
GET /metrics
```

Protected admin endpoints:

```text
POST /ffmpeg/start
POST /ffmpeg/stop
GET  /runtime-config
```

## JWT Authentication and RBAC

The FastAPI dashboard uses JWT authentication to protect administrative operations.

Roles:

| Role   | Access                                                 |
| ------ | ------------------------------------------------------ |
| admin  | Full operational access                                |
| viewer | Read-only access; administrative operations are denied |

Expected RBAC behavior:

| Token         | Expected Result                       |
| ------------- | ------------------------------------- |
| No token      | 401 Unauthorized                      |
| Invalid token | 401 Unauthorized                      |
| Expired token | 401 Token expired                     |
| Viewer token  | 403 Administrator privileges required |
| Admin token   | Allowed for protected operations      |

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

## CloudWatch Access

The EC2 instance should use an IAM instance profile with CloudWatch read permissions.

Recommended managed policy:

```text
CloudWatchReadOnlyAccess
```

Verify from EC2:

```bash
aws sts get-caller-identity
aws cloudwatch list-metrics --region us-east-1 --max-items 5
```

Do not use long-lived AWS access keys on the EC2 instance.

## Useful Commands

Check containers:

```bash
docker compose ps
```

Restart all services:

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

View FFmpeg logs:

```bash
tail -f logs/ffmpeg.log
```

Check Git status:

```bash
git status
```

## Cleanup Warning

Use this for a normal stop:

```bash
docker compose down
```

Use this to start again:

```bash
docker compose up -d
```

Do not run this unless you intentionally want to delete Grafana and Prometheus stored data:

```bash
docker compose down -v
```

## Documentation

Additional documentation is available in the `docs/` directory.

| Document                  | Purpose                                                         |
| ------------------------- | --------------------------------------------------------------- |
| `docs/architecture.md`    | Explains the end-to-end media pipeline and observability design |
| `docs/deployment.md`      | Provides the full deployment and runtime procedure              |
| `docs/troubleshooting.md` | Lists common issues, checks, and recovery steps                 |

## Current Status

This runtime repository currently provides:

* Host-managed FFmpeg streaming
* FastAPI operations dashboard
* Prometheus runtime metrics
* Grafana visualization
* CloudWatch datasource support
* JWT authentication
* Admin and viewer RBAC
* Deployment, architecture, and troubleshooting documentation
