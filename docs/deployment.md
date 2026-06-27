# Deployment Guide

## Overview

This guide describes how to deploy the **AWS Media Pipeline Observability** runtime on a fresh Ubuntu EC2 instance.

The AWS Media Services infrastructure (MediaConnect, MediaLive, MediaPackage, IAM resources, and endpoints) is provisioned separately by the companion Terraform repository.

The runtime repository is responsible for:

* Host-managed FFmpeg
* FastAPI dashboard
* Prometheus
* Grafana
* CloudWatch integration
* JWT authentication
* Role-Based Access Control (RBAC)

---

# Prerequisites

Before deploying the runtime, ensure the following have already been completed:

* Ubuntu 24.04 LTS EC2 instance
* Security Group configured for:

  * SSH (22)
  * FastAPI (8000)
  * Prometheus (9090)
  * Grafana (3000)
  * SRT traffic, if applicable
* AWS Media Services provisioned using the Terraform repository
* Runtime `.env` generated from the Terraform outputs

---

# Install Required Packages

Update the system:

```bash
sudo apt update
sudo apt install -y git ffmpeg docker.io curl unzip tree
```

Enable Docker:

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

Log out and log back in after adding the user to the Docker group.

---

# Install AWS CLI

```bash
cd /tmp

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip

unzip -q awscliv2.zip

sudo ./aws/install
```

Verify:

```bash
aws --version
```

---

# Attach IAM Role

Attach an EC2 IAM role with at least:

* CloudWatchReadOnlyAccess

Verify:

```bash
aws sts get-caller-identity

aws cloudwatch list-metrics --region us-east-1 --max-items 5
```

---

# Clone the Repository

```bash
cd ~

git clone https://github.com/ihsan314ullah-byte/aws-media-pipeline-observability.git

cd aws-media-pipeline-observability/source-ec2
```

---

# Runtime Configuration

Copy the generated runtime configuration into:

```text
source-ec2/.env
```

Typical values include:

```text
SRT_TARGET_IP=
SRT_TARGET_PORT=5000
SRT_LATENCY_MS=2000

HLS_URL=
DASH_URL=

JWT_SECRET=
```

---

# Start the Runtime Stack

From the `source-ec2` directory:

```bash
docker compose up -d
```

Verify:

```bash
docker compose ps
```

Expected services:

* metrics-api
* prometheus
* grafana

---

# Verify Services

FastAPI Dashboard

```text
http://<EC2_PUBLIC_IP>:8000/dashboard
```

Prometheus

```text
http://<EC2_PUBLIC_IP>:9090
```

Grafana

```text
http://<EC2_PUBLIC_IP>:3000
```

Default Grafana credentials:

```text
Username: admin
Password: admin123
```

---

# Start Streaming

Start FFmpeg:

```bash
./scripts/start_ffmpeg.sh
```

Check status:

```bash
./scripts/status.sh
```

Stop FFmpeg:

```bash
./scripts/stop_ffmpeg.sh
```

---

# Verify the Pipeline

When FFmpeg is running:

* MediaConnect receives the SRT stream.
* MediaLive processes the input.
* MediaPackage publishes HLS/DASH endpoints.
* Grafana displays runtime and AWS metrics.

---

# Operational Validation

Verify the following:

* FastAPI dashboard loads successfully.
* Prometheus is scraping metrics.
* Grafana shows Prometheus runtime metrics.
* Grafana shows CloudWatch MediaConnect metrics.
* Grafana shows CloudWatch MediaLive metrics.
* MediaPackage request metrics update during playback.
* HLS and DASH playback function correctly.

---

# Shutdown

Stop FFmpeg:

```bash
./scripts/stop_ffmpeg.sh
```

Stop containers:

```bash
docker compose down
```

To preserve Grafana dashboards and Prometheus data, **do not** use:

```bash
docker compose down -v
```

unless you intentionally want to remove persistent Docker volumes.

---

# Companion Repository

Infrastructure provisioning is maintained separately:

```text
terraform-aws-mediaservices
```

The deployment flow is:

```text
Terraform Infrastructure
        ↓
Generate runtime .env
        ↓
Deploy Runtime Repository
        ↓
Start Docker Compose
        ↓
Start FFmpeg
        ↓
Observe Metrics
        ↓
Validate HLS / DASH Playback
```
