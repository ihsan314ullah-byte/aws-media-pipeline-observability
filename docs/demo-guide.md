# Demo Guide

## Objective

This guide demonstrates the complete AWS Media Pipeline Observability project from source ingest to playback and monitoring.

The demo showcases:

* AWS Media Services
* Infrastructure as Code
* Runtime orchestration
* Observability
* Security (JWT + RBAC)
* Operations workflow

Estimated demo time: **10–15 minutes**

---

# Demo Architecture

```text
MP4 Video File
        │
        ▼
FFmpeg (Source EC2)
        │
        ▼
SRT Caller
        │
        ▼
AWS MediaConnect
        │
        ▼
AWS MediaLive
        │
        ▼
AWS MediaPackage
        │
        ▼
HLS / DASH Playback

───────────────

Runtime Metrics
        │
        ▼
FastAPI
        │
        ▼
Prometheus
        │
        ▼
Grafana

───────────────

AWS Metrics
        │
        ▼
CloudWatch
        │
        ▼
Grafana
```

---

# Demo Preparation

Before starting, verify:

* Docker containers are running.
* Grafana is accessible.
* AWS MediaLive channel is running.
* Runtime `.env` is configured.
* FFmpeg is **stopped**.

---

# Step 1 — Introduce the Project

Explain the purpose of the project.

Example:

> This project demonstrates a complete AWS live streaming pipeline with end-to-end observability. A host-managed FFmpeg process sends an SRT stream into AWS MediaConnect. MediaLive processes the stream, MediaPackage publishes HLS/DASH endpoints, and Grafana combines runtime metrics from Prometheus with AWS metrics from CloudWatch.

---

# Step 2 — Show the Architecture

Open:

* `README.md`
* `docs/architecture.md`

Briefly explain:

* Infrastructure repository
* Runtime repository
* Separation of responsibilities
* Streaming flow
* Monitoring flow

---

# Step 3 — Show the FastAPI Dashboard

Open:

```text
http://<EC2_PUBLIC_IP>:8000/dashboard
```

Explain:

* Runtime controls
* Status panel
* Monitoring links
* HLS/DASH playback links
* JWT token field

---

# Step 4 — Generate an Admin JWT

Generate an Admin token.

Paste it into the dashboard.

Explain:

* JWT authentication
* Admin role
* Protected operations

---

# Step 5 — Start FFmpeg

Start FFmpeg from the dashboard.

Explain:

* FFmpeg runs directly on the host.
* FastAPI orchestrates the host process.
* The stream is sent as an SRT caller to AWS MediaConnect.

---

# Step 6 — Observe Runtime Metrics

Open Grafana.

Show the **Host Runtime Observability** dashboard.

Point out:

* FFmpeg running = 1
* CPU usage
* Memory usage
* FFmpeg bitrate
* FFmpeg processing speed

Explain how Prometheus collects metrics from FastAPI.

---

# Step 7 — Observe AWS Metrics

Switch to the **AWS Media Services Observability** dashboard.

Highlight:

### MediaConnect

* Source bitrate
* Packet loss

### MediaLive

* Active alerts
* Input frame rate
* Network input

### MediaPackage

* Request count
* Viewer activity (if playback is active)

Explain that these metrics are retrieved directly from Amazon CloudWatch.

---

# Step 8 — Verify Playback

Open the HLS or DASH player.

Confirm that:

* Video plays successfully.
* MediaPackage request metrics increase.
* Runtime metrics remain stable.

---

# Step 9 — Demonstrate RBAC

Generate a Viewer JWT.

Replace the Admin token.

Attempt to:

* Start FFmpeg
* Stop FFmpeg

Expected result:

* Viewer receives **403 Forbidden**.
* Public monitoring remains accessible.

Explain the difference between authentication and authorization.

---

# Step 10 — Stop FFmpeg

Stop FFmpeg.

Observe:

* FFmpeg running changes to 0.
* MediaConnect bitrate drops.
* MediaLive active alerts increase.
* Playback eventually stops.

This demonstrates end-to-end operational visibility.

---

# Key Takeaways

This project demonstrates:

* AWS MediaConnect
* AWS MediaLive
* AWS MediaPackage
* Terraform-based infrastructure
* Host-managed FFmpeg
* FastAPI operations dashboard
* Prometheus monitoring
* Grafana visualization
* CloudWatch integration
* JWT authentication
* Role-Based Access Control
* Operational troubleshooting

---

# Suggested Questions During a Demo

Be prepared to answer:

* Why does FFmpeg run on the host instead of in Docker?
* Why use both Prometheus and CloudWatch?
* Why split infrastructure and runtime into separate repositories?
* How would this scale to multiple streams?
* How would you automate deployment further?
* What happens if MediaLive loses input?
* How would you add alerting?

These questions naturally extend from the architecture and demonstrate an understanding of the design decisions behind the project.
