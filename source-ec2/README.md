#  README.md
# AWS Media Streaming + Observability Pipeline

This project implements a **real-time video streaming pipeline** on AWS with full **observability using FastAPI, Prometheus, and Grafana-ready metrics**.

It demonstrates how a live video stream can be ingested, transported, monitored, and analyzed end-to-end using modern cloud and DevOps tools.

---

# What This Project Does

The system:

- Streams a video file using **FFmpeg (SRT caller mode)**
- Sends stream to **AWS MediaConnect**
- Processes via **AWS MediaLive**
- Packages via **AWS MediaPackage**
- Delivers via **DASH ABR Player**
- Exposes **real-time system + streaming metrics**
- Provides **Prometheus-compatible metrics endpoint**
- Enables **Grafana dashboards for visualization**

---

# Architecture Overview

## General Streaming Flow:

EC2-FFmpeg(SRT Caller) -> MP4 File -> AWS MediaConnect(SRT Listener) -> AWS MediaLive -> AWS MediaPackage -> DASH Player endpoints(ABR Ladder)


## Prallel Observability Pipeline:

FFmpeg Logs + System Metrics -> FastAPI (/metrics endpoint) -> Prometheus Scraping -> Grafana Visualization 

---

# Project Structure

```
streaming-demo/
├── api/
│   ├── api.py              # FastAPI metrics exporter
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Container for API
│
├── scripts/
│   ├── start\_ffmpeg.sh     # Start SRT streaming
│   ├── stop\_ffmpeg.sh      # Stop streaming
│   ├── status.sh           # System + stream diagnostics
│
├── prometheus/
│   └── prometheus.yml      # Prometheus scrape config
│
├── logs/
│   ├── ffmpeg.log          # FFmpeg runtime logs
│   ├── ffmpeg.pid          # Process tracking
│
└── input/
    └── tempest\_input.mp4   # Input video file
````

---

# Core Components Explained

## 1. FFmpeg Streaming Engine

* Reads local MP4 file
* Streams via **SRT protocol (caller mode)**
* Sends encoded MPEG-TS stream to AWS MediaConnect
* Logs performance metrics to `ffmpeg.log`

### Key Metrics:

* bitrate
* speed (real-time processing rate)
* stream stability

---

## 2. FastAPI Metrics Service

Exposes system + streaming metrics at:

```
http://<EC2-IP>:8000/metrics
```

### Metrics exposed:

* CPU usage
* Memory usage
* FFmpeg running state
* FFmpeg bitrate
* FFmpeg speed
* SRT port activity

This acts as a **custom Prometheus exporter**.

---

## 3. Prometheus

* Scrapes FastAPI `/metrics`
* Stores time-series data
* Enables querying and alerting

Default UI:

```
http://<EC2-IP>:9090
```

---

## 4. AWS Media Pipeline

Handles cloud-side streaming:

* MediaConnect → transport layer
* MediaLive → processing / transcoding
* MediaPackage → packaging for playback
* DASH Player → final viewer

---

# Metrics Available

Example output:

```
cpu_usage_percent 3.2
memory_usage_percent 16.1
ffmpeg_running 1
ffmpeg_bitrate_kbps 4290.7
ffmpeg_speed 1.0
srt_active 1
```

---

# Key Design Idea

This project separates:

| Layer              | Purpose              |
| ------------------ | -------------------- |
| FFmpeg             | Streaming engine     |
| AWS Media Services | Cloud video pipeline |
| FastAPI            | Metrics exporter     |
| Prometheus         | Time-series storage  |
| Grafana (future)   | Visualization        |

---

# How to Run on a Fresh EC2
```bash
sudo apt update

sudo apt install git ffmpeg tree -y
```


## 1. Clone repository

```bash
git clone https://github.com/ihsan314ullah-byte/aws-streaming-observability.git
ls-lh
mv aws-streaming-observability ~/streaming-demo
cd ~/streaming-demo
tree -L 3

make sure the ~/streaming-demo/logs exist, if not you will get errors in starting/stoping ffmpeg script and then make
mkdir -p logs

ensure scripts are executiable via: chmod +x scripts/*.sh
check via: ls -lh ~/streaming-demo/scripts/

```

---

## 2. Install docker dependency

```bash
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

IMPORTANT: logout and login again after installing Docker.

---
### Create Docker network (important)

```bash
docker network create streaming-net
```

## 3. Start FastAPI metrics container

```bash
cd ~/streaming-demo/api
docker build -t metrics-api .
```

```bash
docker run -d \
--name metrics-api \
--network streaming-net \
-p 8000:8000 \
-v /home/ubuntu/streaming-demo:/home/ubuntu/streaming-demo \
metrics-api
```

---

## 4. Start/Run Prometheus

```bash
docker run -d \
--name prometheus \
--network streaming-net \
-p 9090:9090 \
-v ~/streaming-demo/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
prom/prometheus
```

---

## 5.  Grafana Setup (Docker)

```bash
docker run -d \
--name grafana \
--network streaming-net \
-p 3000:3000 \
grafana/grafana
````
---

## 5. Start streaming

```bash
bash scripts/start_ffmpeg.sh
```

---

## 6. Verify system

### API:

```
http://<EC2-IP>:8000/metrics
```

### Prometheus:

```
http://<EC2-IP>:9090
```

### Grafana UI Access

Open in browser:

```text
http://<EC2-PUBLIC-IP>:3000
```
---

# Future Enhancements

* Alerting rules (stream failure detection)
* AWS CloudWatch integration
* Multi-stream ingestion
* Real-time QoE scoring

---

# What This Project Demonstrates

* Live video streaming over SRT
* AWS media pipeline architecture
* Observability engineering
* Prometheus custom exporter design
* Log-based metric extraction
* DevOps + streaming integration
* Grafana dashboards (stream health visualization)

---

# Author Notes

This project was built as a **hands-on streaming + observability system** combining:

* Media engineering
* Cloud infrastructure (AWS)
* DevOps monitoring
* Real-time metrics design

```

---

---

## JWT Admin/Viewer Token Generation

The dashboard uses JWT-based role access control.

Protected admin operations require a valid JWT token with:

```json
{
  "role": "admin"
}
Viewer tokens are intentionally blocked from administrative operations such as starting or stopping FFmpeg.
# Generate Admin Token
Run this from the source-ec2 directory on the EC2 instance:
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

Admin permissions:

Start FFmpeg
Stop FFmpeg
Read protected runtime config
Open HLS/DASH playback links from runtime config
# Generate Viewer Token
Run this from the source-ec2 directory on the EC2 instance:
```
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
Expected viewer behavior:

Start FFmpeg: blocked with 403 Forbidden
Stop FFmpeg: blocked with 403 Forbidden
Protected runtime config: blocked with 403 Forbidden
# Expected RBAC Behavior
Token Type	Expected Result
No token	401 Unauthorized
Invalid token	401 Unauthorized
Expired token	401 Token expired
Viewer token	403 Administrator privileges required
Admin token	Allowed for protected operations
# Protected Endpoints
```
POST /ffmpeg/start
POST /ffmpeg/stop
GET /runtime-config
```
# Public Endpoints
```
GET /
GET /dashboard
GET /health
GET /status
GET /ffmpeg/status
GET /metrics
```
