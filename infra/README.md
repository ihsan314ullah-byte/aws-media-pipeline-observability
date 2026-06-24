# AWS Live Streaming Pipeline via Terraform

## Overview

This project deploys a complete AWS live streaming workflow using Terraform.

Architecture:

OBS / FFmpeg
    ↓
MediaConnect
    ↓
MediaLive
    ↓
MediaPackage V1
    ├── HLS Endpoint (.m3u8)
    └── DASH Endpoint (.mpd)

## Features

- Infrastructure as Code (Terraform)
- AWS MediaConnect
- AWS MediaLive
- AWS MediaPackage V1
- HLS Delivery
- DASH Delivery
- CloudFormation integration for MediaPackage Origin Endpoints

## Current Status

✅ MediaConnect Flow

✅ MediaLive Input

✅ MediaLive Channel

✅ MediaPackage Channel

✅ HLS Playback

✅ DASH Playback

## Future Enhancements

- Adaptive Bitrate Streaming (ABR)
- CloudFront Distribution
- Monitoring & Alerting
- Cost Optimization