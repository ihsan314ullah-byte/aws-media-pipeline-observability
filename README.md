# AWS Media Pipeline Observability Lab

End-to-end AWS live streaming lab using:

- EC2 FFmpeg SRT Caller
- AWS MediaConnect SRT Listener
- AWS MediaLive
- AWS MediaPackage
- HLS/DASH ABR endpoints
- FastAPI metrics exporter
- Prometheus
- Grafana
- Terraform Infrastructure as Code

## Project Structure

```text
infra/        Terraform AWS Media Services IaC
source-ec2/   FFmpeg source, FastAPI, Prometheus, Grafana, Docker
scripts/      Helper scripts
dashboards/   Grafana dashboard exports
docs/         Architecture, troubleshooting, cost control

# Architecture
EC2 FFmpeg SRT Caller
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
# Observability
EC2 Source Metrics -> FastAPI /metrics -> Prometheus -> Grafana
AWS Media Metrics -> CloudWatch -> Grafana
