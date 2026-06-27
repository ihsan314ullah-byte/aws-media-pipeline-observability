# Troubleshooting Guide

## Overview

This document captures common issues encountered while developing and
operating the AWS Media Pipeline Observability project, along with their
resolutions.

------------------------------------------------------------------------

# Git & Repository Issues

## Problem: `fatal: not a git repository`

### Symptoms

``` text
fatal: not a git repository (or any of the parent directories): .git
```

### Cause

Git commands were executed outside the repository root.

### Resolution

``` bash
cd ~/aws-media-pipeline-observability
git status
```

------------------------------------------------------------------------

## Problem: Push rejected (non-fast-forward)

### Symptoms

``` text
failed to push some refs
```

### Cause

The remote repository contains commits not present locally.

### Resolution

``` bash
git pull --rebase origin main
git push origin main
```

------------------------------------------------------------------------

## Problem: Obsolete or duplicate documentation

### Resolution

-   Keep one authoritative `README.md`.
-   Store detailed documentation under `docs/`.
-   Remove obsolete documentation after content has been merged.

------------------------------------------------------------------------

# Docker

## Problem: Docker permission denied

### Resolution

``` bash
sudo usermod -aG docker ubuntu
```

Log out and back in.

## Problem: Containers fail to start

### Check

``` bash
docker compose ps
docker compose logs
```

Verify:

-   Docker daemon is running.
-   Required ports are available.
-   `.env` exists.
-   Images were built successfully.

## Problem: Grafana dashboards disappear

### Resolution

Ensure Docker Compose uses a persistent volume:

``` yaml
volumes:
  - grafana-data:/var/lib/grafana
```

Avoid:

``` bash
docker compose down -v
```

unless intentionally removing persistent data.

------------------------------------------------------------------------

# AWS CLI & IAM

## Problem: `aws: command not found`

Install AWS CLI v2 and verify:

``` bash
aws --version
```

## Problem: Unable to locate credentials

Attach an EC2 IAM role with:

-   CloudWatchReadOnlyAccess

Verify:

``` bash
aws sts get-caller-identity
```

------------------------------------------------------------------------

# CloudWatch

## Problem: Grafana CloudWatch datasource fails

Verify:

-   IAM role attached
-   Correct AWS Region
-   CloudWatch datasource configured
-   Region matches deployed infrastructure

------------------------------------------------------------------------

# FFmpeg

## Problem: FFmpeg does not start

Check:

``` bash
./scripts/status.sh
tail -f logs/ffmpeg.log
```

Verify:

-   `.env`
-   Input video
-   Target IP and port
-   SRT destination

## Problem: FFmpeg appears stopped but stale metrics remain

Reset runtime metrics when FFmpeg stops.

------------------------------------------------------------------------

# AWS Media Services

## Problem: MediaLive Active Alerts remain high

Verify:

-   FFmpeg process
-   MediaConnect flow
-   MediaLive input
-   MediaConnect bitrate

## Problem: No MediaPackage activity

Open the HLS or DASH endpoint in a compatible player.

------------------------------------------------------------------------

# JWT & RBAC

## Problem: HTTP 401 Unauthorized

Generate a new JWT and ensure the correct secret is used.

## Problem: HTTP 403 Forbidden

Viewer role attempted an administrative operation.

------------------------------------------------------------------------

# Grafana

## Problem: Dashboard not imported automatically

Verify:

``` text
grafana/provisioning/dashboards/dashboard.yml
source-ec2/grafana/dashboards/
```

Restart:

``` bash
docker compose restart grafana
```

------------------------------------------------------------------------

# Runtime Configuration

## Problem: Incorrect runtime values

### Symptoms

-   FFmpeg cannot connect
-   MediaConnect receives no traffic
-   Playback fails

### Resolution

1.  Regenerate the runtime `.env` from the Terraform repository.
2.  Copy it to:

``` text
source-ec2/.env
```

3.  Restart:

``` bash
docker compose restart
```

4.  Start FFmpeg again.

------------------------------------------------------------------------

# Repository Maintenance

## Recommended Practices

-   Keep one authoritative `README.md`.
-   Store detailed documentation under `docs/`.
-   Never commit production `.env` files.
-   Use IAM roles instead of long-lived access keys.
-   Keep Terraform infrastructure and runtime operations in separate
    repositories.
-   Remove obsolete notes before publishing.

------------------------------------------------------------------------

# Final Validation Checklist

Before demonstrating:

-   Docker containers healthy
-   FFmpeg starts successfully
-   FastAPI dashboard loads
-   Prometheus scraping metrics
-   Grafana dashboards load
-   CloudWatch datasource works
-   MediaConnect receives traffic
-   MediaLive processes stream
-   HLS/DASH playback succeeds
