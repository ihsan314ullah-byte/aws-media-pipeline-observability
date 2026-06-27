# Troubleshooting Guide

## Overview

This document captures common issues encountered while developing and operating the AWS Media Pipeline Observability project, along with their resolutions.

---

# Git & Repository Issues

## Problem: `fatal: not a git repository`

### Symptoms

```text
fatal: not a git repository (or any of the parent directories): .git
```

### Cause

Git commands were executed outside the repository root.

### Resolution

Navigate to the repository first:

```bash
cd ~/aws-media-pipeline-observability
git status
```

---

## Problem: Obsolete or duplicate documentation

### Symptoms

* Multiple README files
* Conflicting setup instructions
* Outdated Grafana documentation

### Resolution

Maintain:

* One authoritative `README.md`
* Detailed documentation under `docs/`

Remove obsolete documentation after its content has been merged.

---

# Docker

## Problem: Docker permission denied

### Symptoms

```text
permission denied while trying to connect to the Docker daemon
```

### Resolution

Add the user to the Docker group:

```bash
sudo usermod -aG docker ubuntu
```

Log out and log back in.

---

## Problem: Grafana dashboards disappear

### Cause

Grafana storage is not persistent.

### Resolution

Ensure Docker Compose uses a persistent volume:

```yaml
volumes:
  - grafana-data:/var/lib/grafana
```

Avoid:

```bash
docker compose down -v
```

unless you intentionally want to remove persistent volumes.

---

# AWS CLI & IAM

## Problem: `aws: command not found`

### Resolution

Install AWS CLI v2 using the official installer.

Verify:

```bash
aws --version
```

---

## Problem: Unable to locate credentials

### Symptoms

```text
Unable to locate credentials
```

### Cause

The EC2 instance has no IAM role attached.

### Resolution

Attach an IAM role with:

* CloudWatchReadOnlyAccess

Verify:

```bash
aws sts get-caller-identity
```

---

# CloudWatch

## Problem: Grafana CloudWatch datasource fails

### Possible causes

* Incorrect AWS region
* Missing IAM permissions
* CloudWatch datasource not provisioned

### Resolution

Verify:

* IAM role attached
* `cloudwatch.yml`
* CloudWatch datasource status in Grafana
* Region matches deployed AWS resources

---

# FFmpeg

## Problem: FFmpeg does not start

### Check

```bash
./scripts/status.sh
```

Inspect:

```bash
tail -f logs/ffmpeg.log
```

Verify:

* `.env`
* Input video
* SRT destination
* Target IP and port

---

## Problem: FFmpeg appears stopped but stale metrics remain

### Cause

Old metric values persisted after FFmpeg exited.

### Resolution

Reset runtime metrics when FFmpeg stops so the dashboard reflects the current state.

---

# AWS Media Services

## Problem: MediaLive Active Alerts remain high

### Possible causes

* FFmpeg not running
* SRT stream not reaching MediaConnect
* Incorrect target IP or port

### Resolution

Verify:

* FFmpeg process
* MediaConnect flow
* MediaLive input
* Grafana MediaConnect bitrate panel

---

## Problem: No MediaPackage activity

### Cause

No client is requesting playback.

### Resolution

Open the HLS or DASH endpoint in a compatible player.

Verify request metrics in Grafana.

---

# JWT & RBAC

## Problem: HTTP 401 Unauthorized

### Causes

* Missing token
* Invalid token
* Expired token

### Resolution

Generate a new JWT and ensure the correct secret is used.

---

## Problem: HTTP 403 Forbidden

### Cause

Viewer role attempting an administrative operation.

### Expected behavior

Viewer accounts may monitor the system but cannot:

* Start FFmpeg
* Stop FFmpeg
* Read protected runtime configuration

---

# Grafana

## Problem: Dashboard not imported automatically

### Cause

Missing dashboard provisioning configuration.

### Resolution

Ensure:

```text
grafana/provisioning/dashboards/dashboard.yml
```

exists and dashboard JSON files are located under:

```text
source-ec2/grafana/dashboards/
```

Restart Grafana:

```bash
docker compose restart grafana
```

---

# Runtime Configuration

## Problem: Incorrect runtime values

### Cause

`.env` does not match the deployed infrastructure.

### Resolution

Regenerate the runtime configuration from the Terraform repository and replace:

```text
source-ec2/.env
```

---

# Repository Maintenance

## Recommended Practices

* Keep one authoritative `README.md`.
* Store detailed documentation under `docs/`.
* Keep runtime-generated files out of Git.
* Preserve empty runtime directories using `.gitkeep`.
* Commit meaningful milestones rather than many tiny commits.
* Use an IAM instance profile instead of long-lived AWS access keys.

---

# Operational Checklist

Before demonstrating the project, verify:

* Docker containers are running.
* FFmpeg is operational.
* MediaLive channel is running.
* Grafana dashboards load correctly.
* CloudWatch datasource is healthy.
* Prometheus is scraping metrics.
* JWT authentication works.
* Viewer RBAC restrictions are enforced.
* HLS/DASH playback is functional.

This checklist provides a quick health assessment before a demo or operational handover.
