# Architecture

## Overview

This project implements an end-to-end AWS media streaming and observability pipeline.

The goal is to simulate a production-style live video workflow where a source EC2 instance sends an SRT stream into AWS Media Services, while both runtime metrics and AWS service metrics are visualized in Grafana.

## High-Level Streaming Flow

```text
.mp4 Video File 
        |
        v
FFmpeg on Source EC2
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

## Runtime Observability Flow

```text
FFmpeg Logs + EC2 Runtime Metrics
        |
        v
FastAPI /metrics
        |
        v
Prometheus
        |
        v
Grafana
```

## AWS Observability Flow

```text
AWS MediaConnect
AWS MediaLive
AWS MediaPackage
        |
        v
Amazon CloudWatch
        |
        v
Grafana CloudWatch Datasource
```

## Repository Split

This project is split into two repositories.

### Infrastructure Repository

```text
terraform-aws-mediaservices
```

Responsible for:

* AWS MediaConnect
* AWS MediaLive
* AWS MediaPackage
* IAM resources
* HLS and DASH endpoints
* Terraform outputs
* Runtime `.env` generation

### Runtime / Observability Repository

```text
aws-media-pipeline-observability
```

Responsible for:

* FFmpeg orchestration
* FastAPI dashboard
* Prometheus metrics
* Grafana dashboards
* CloudWatch datasource
* JWT authentication
* RBAC authorization

## Source EC2 Runtime Design

The source EC2 instance runs FFmpeg directly on the host.

Docker Compose runs:

* FastAPI
* Prometheus
* Grafana

FastAPI controls host FFmpeg using host-level scripts.

```text
Source EC2
├── Host
│   ├── FFmpeg
│   ├── start_ffmpeg.sh
│   ├── stop_ffmpeg.sh
│   └── status.sh
│
└── Docker
    ├── FastAPI
    ├── Prometheus
    └── Grafana
```

## Why FFmpeg Runs on the Host

FFmpeg runs on the host instead of inside a container because the project needs clear process control, logging, and operational visibility.

This design allows:

* Direct FFmpeg process management
* Simple PID tracking
* Clear log collection
* Easier troubleshooting
* Dashboard-based start/stop control

## FastAPI Role

FastAPI provides:

* Dashboard UI
* Runtime status endpoint
* Prometheus metrics endpoint
* FFmpeg start/stop API
* JWT authentication
* RBAC enforcement

Important endpoints:

```text
GET  /dashboard
GET  /status
GET  /ffmpeg/status
GET  /metrics
POST /ffmpeg/start
POST /ffmpeg/stop
GET  /runtime-config
```

## Prometheus Role

Prometheus scrapes FastAPI at:

```text
http://metrics-api:8000/metrics
```

Prometheus stores runtime time-series metrics such as:

* CPU usage
* Memory usage
* FFmpeg running state
* FFmpeg bitrate
* FFmpeg speed
* SRT caller process status

## Grafana Role

Grafana provides dashboards for two metric sources.

### Prometheus Datasource

Used for host/runtime metrics:

* EC2 CPU
* EC2 memory
* FFmpeg running
* FFmpeg bitrate
* FFmpeg speed
* SRT caller process active

### CloudWatch Datasource

Used for AWS Media Services metrics:

* MediaConnect source bitrate
* MediaConnect packet loss
* MediaLive active alerts
* MediaLive input frame rate
* MediaLive network input
* MediaPackage request activity

## CloudWatch Integration

Grafana reads AWS metrics through the CloudWatch datasource.

The EC2 instance uses an IAM instance profile with CloudWatch read permissions.

No long-lived AWS access keys should be stored on the EC2 instance.

Recommended IAM policy:

```text
CloudWatchReadOnlyAccess
```

## Authentication and Authorization

The FastAPI dashboard uses JWT authentication.

Two roles are supported:

| Role   | Access                                        |
| ------ | --------------------------------------------- |
| admin  | Can start/stop FFmpeg and read runtime config |
| viewer | Read-only access; protected operations denied |

Protected endpoints require an admin JWT:

```text
POST /ffmpeg/start
POST /ffmpeg/stop
GET  /runtime-config
```

Public endpoints remain accessible without a token:

```text
GET /
GET /dashboard
GET /health
GET /status
GET /ffmpeg/status
GET /metrics
```

## Demo Behavior

When FFmpeg is stopped:

```text
FFmpeg running = 0
MediaConnect bitrate drops
MediaLive active alerts increase
HLS/DASH playback may stop
```

When FFmpeg is started:

```text
FFmpeg running = 1
FFmpeg bitrate rises
MediaConnect source bitrate rises
MediaLive input frame rate appears
MediaLive active alerts drop
HLS/DASH playback works
```

This gives a clear end-to-end operational demonstration from source ingest to AWS processing to playback and monitoring.
