# Deployment Guide

## Overview

This guide describes how to deploy the **AWS Media Pipeline Observability** runtime on a fresh Ubuntu EC2 instance.

The AWS Media Services infrastructure (MediaConnect, MediaLive, MediaPackage, IAM resources, and endpoints) is provisioned separately by the companion Terraform repository.

The runtime repository is responsible for:

- Host-managed FFmpeg
- FastAPI dashboard
- Prometheus
- Grafana
- CloudWatch integration
- JWT authentication
- Role-Based Access Control (RBAC)

---

# Prerequisites

Before deploying the runtime, ensure the following have already been completed:

- Ubuntu 24.04 LTS EC2 instance
- Security Group configured for:
  - SSH (22)
  - FastAPI (8000)
  - Prometheus (9090)
  - Grafana (3000)
  - SRT traffic (if applicable)
- AWS Media Services provisioned using the Terraform repository
- Runtime `.env` generated from the Terraform outputs

---

# Install Required Packages

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
aws --version
```

---

# Attach IAM Role

Attach an EC2 IAM role with:

- CloudWatchReadOnlyAccess

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

Generate the runtime configuration from the Terraform repository:

```powershell
cd terraform-aws-mediaservices
terraform apply
.\generate-runtime-env.ps1
```

Copy the generated `.env` file to the EC2 instance:

```bash
scp -i /path/to/key.pem .env ubuntu@<EC2_PUBLIC_IP>:~/aws-media-pipeline-observability/source-ec2/.env
```

Verify:

```bash
cd ~/aws-media-pipeline-observability/source-ec2
cat .env
```

---

# Start the Runtime Stack

```bash
docker compose up -d
docker compose ps
```

Expected:

- metrics-api
- prometheus
- grafana

---

# Runtime Validation

```bash
curl http://localhost:8000/status
curl http://localhost:8000/metrics
```

---

# Verify Services

- FastAPI: `http://<EC2_PUBLIC_IP>:8000/dashboard`
- Prometheus: `http://<EC2_PUBLIC_IP>:9090`
- Grafana: `http://<EC2_PUBLIC_IP>:3000`

Default Grafana credentials:

```text
Username: admin
Password: admin123
```

---

# Start Streaming

```bash
./scripts/start_ffmpeg.sh
./scripts/status.sh
./scripts/stop_ffmpeg.sh
```

---

# Verify the Pipeline

- MediaConnect receives the SRT stream.
- MediaLive processes the input.
- MediaPackage publishes HLS/DASH endpoints.
- Grafana displays runtime and AWS metrics.

---

# Operational Validation

- FastAPI dashboard loads.
- Prometheus scrapes metrics.
- Grafana displays Prometheus metrics.
- Grafana displays CloudWatch metrics.
- HLS/DASH playback succeeds.

---

# Shutdown

```bash
./scripts/stop_ffmpeg.sh
docker compose down
```

Do **not** use:

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

The complete deployment workflow is:

```text
terraform-aws-mediaservices
        │
        ▼
Provision AWS Media Services
        │
        ▼
Generate runtime .env
        │
        ▼
Copy .env to EC2
        │
        ▼
Start Docker services
        │
        ▼
Start FFmpeg
        │
        ▼
Verify HLS/DASH playback
        │
        ▼
Observe the pipeline with Prometheus, Grafana, and CloudWatch
```
