# AWS Media Pipeline Terraform Lab - Troubleshooting Notes



## Project Summary



This project automates an AWS live streaming media pipeline using Terraform.



Architecture:



```text

OBS / FFmpeg SRT Caller

       ↓

AWS MediaConnect SRT Listener

       ↓

AWS MediaLive

       ↓

AWS MediaPackage V1

      ├── HLS Endpoint (.m3u8)

      └── DASH Endpoint (.mpd)

```



The final working version includes Adaptive Bitrate Streaming using the following ladder:



```text

720p60

720p30

480p30

240p30

```



## Main Challenges Faced



### 1. AWS MediaPackage V1 Origin Endpoint Terraform Limitation



The Terraform AWS provider did not support the expected MediaPackage V1 origin endpoint resource in this lab.



Error encountered:



```text

Invalid resource type: aws\_media\_package\_origin\_endpoint

```



### Solution



Used Terraform-managed CloudFormation stacks to create MediaPackage V1 HLS and DASH origin endpoints.



This allowed the full pipeline to remain Infrastructure as Code.



---



### 2. HLS Worked Before DASH



The HLS endpoint was created and validated first.



After HLS playback worked successfully in VLC, a DASH endpoint was added through another CloudFormation stack.



This reduced troubleshooting complexity.



---



### 3. Initial ABR Ladder Caused Playback Problems



The first ABR ladder included:



```text

1080p 5000k

720p 3000k

480p 1500k

360p 700k

```



Playback problems included:



```text

Buffer stalled

Timeout while loading level playlist

Error while loading fragment

DASH request timeout

```



### Solution



Replaced the ladder with a proven working design:



```text

720p60

720p30

480p30

240p30

```



This stabilized both HLS and DASH playback.



---


## Final Working Status



```text

MediaConnect        Working

MediaLive           Working

MediaPackage V1     Working

HLS Endpoint        Working

DASH Endpoint       Working

ABR Ladder          Working

Terraform IaC       Working

```



## Future Enhancements



Possible next improvements:



```text

CloudFront CDN distribution

Custom HLS/DASH player page

CloudWatch monitoring

MediaLive alarms

Terraform variables cleanup

Cost optimization

AWS MediaPackage V2 migration

CI/CD validation with GitHub Actions

```



