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
source-ec2/   FFmpeg source, FastAPI, Prometheus, Grafana, Docker
scripts/      Helper scripts
dashboards/   Grafana dashboard exports
docs/         Architecture
```

# Infrastructure provisioning

``` 
maintained in the companion repository:https://github.com/ihsan314ullah-byte/terraform-aws-mediaservices

After provisioning the AWS Media services, generate the runtime configuration and copy the generated .env into:

source-ec2/.env
```

# Architecture

```
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
```

# Observability
EC2 Source Metrics -> FastAPI /metrics -> Prometheus -> Grafana
AWS Media Metrics -> CloudWatch -> Grafana
