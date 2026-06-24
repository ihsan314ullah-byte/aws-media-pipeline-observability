# Grafana Overview

Grafana is used to visualize real-time streaming and system metrics collected via Prometheus. It provides dashboards for monitoring FFmpeg streaming health, bitrate, system resources, and SRT connectivity.

---

# Grafana Setup (Docker)

```bash
docker run -d \
--name grafana \
--network streaming-net \
-p 3000:3000 \
grafana/grafana
````

---

# Grafana UI Access

Open in browser:

```text
http://<EC2-PUBLIC-IP>:3000
```

---

# Default Login

```
Username: admin
Password: admin
```

You will be prompted to change the password after first login.

---

# Add Prometheus Data Source

Inside Grafana UI:

```
Connections → Data Sources → Add data source → Prometheus
```

### Configuration:

```
URL: http://prometheus:9090
```

⚠️ Important: Use `prometheus:9090` (Docker service name), NOT localhost.

Click:

```
Save & Test
```

Expected:

```
Data source is working
```

---

# Create Dashboard Panels

Go to:

```
Dashboards → New → New Dashboard → Add Visualization
```

Select Prometheus as the data source.

---

# Key Metrics (PromQL Queries)

## Bitrate (Stream Quality)

```promql
ffmpeg_bitrate_kbps
```

## FFmpeg Speed (Real-time Processing)

```promql
ffmpeg_speed
```

## Stream Status (Running / Stopped)

```promql
ffmpeg_running
```

## SRT Connectivity Status

```promql
srt_active
```

## CPU Usage

```promql
cpu_usage_percent
```

## Memory Usage

```promql
memory_usage_percent
```

---

## System Architecture

```
MP4 Input
   ↓
FFmpeg (SRT Caller)
   ↓
AWS MediaConnect
   ↓
MediaLive
   ↓
MediaPackage
   ↓
DASH Player
```

### Observability Pipeline:

```
FastAPI (/metrics)
   ↓
Prometheus
   ↓
Grafana
```

---

## Fresh EC2 Setup Requirements

### 1. Create Docker network (MANDATORY)

```bash
docker network create streaming-net
```

---

### 2. Start FastAPI Metrics Service

```bash
cd api

docker build -t metrics-api .

docker run -d \
--name metrics-api \
--network streaming-net \
-p 8000:8000 \
-v /home/ubuntu/streaming-demo:/home/ubuntu/streaming-demo \
metrics-api
```

---

### 3. Start Prometheus

```bash
docker run -d \
--name prometheus \
--network streaming-net \
-p 9090:9090 \
-v ~/streaming-demo/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
prom/prometheus
```

---

### 4. Start Grafana

```bash
docker run -d \
--name grafana \
--network streaming-net \
-p 3000:3000 \
grafana/grafana
```

---

### 5. Start FFmpeg Streaming

```bash
bash scripts/start_ffmpeg.sh
```

---

## Outcome

This setup provides a full streaming observability stack:

* Real-time FFmpeg streaming
* AWS media pipeline integration
* System monitoring (CPU, memory)
* Stream health metrics (bitrate, speed)
* Visualization via Grafana dashboards

---

</details>
```

---
