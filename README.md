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


## JWT Authentication & Role-Based Access Control (RBAC)

The FastAPI dashboard uses JSON Web Tokens (JWT) to protect administrative operations.

Two roles are currently supported:

| Role       | Description                                             |
| ---------- | ------------------------------------------------------- |
| **admin**  | Full control of the media pipeline                      |
| **viewer** | Read-only access (administrative operations are denied) |

---

### Protected API Endpoints

The following endpoints require a valid **Admin JWT**:

```
POST /ffmpeg/start
POST /ffmpeg/stop
GET  /runtime-config
```

The following endpoints remain public:

```
GET /
GET /dashboard
GET /health
GET /status
GET /ffmpeg/status
GET /metrics
```

---

## Generate an Admin Token

Run the following on the EC2 instance from the `source-ec2` directory.

```bash
cd ~/aws-media-pipeline-observability/source-ec2

python3 - <<'PY'
import jwt
import datetime
from pathlib import Path

secret = ""

for line in Path(".env").read_text().splitlines():
    if line.startswith("JWT_SECRET="):
        secret = line.split("=",1)[1].strip()
        break

payload = {
    "sub": "ihsan",
    "role": "admin",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
}

print(jwt.encode(payload, secret, algorithm="HS256"))
PY
```

Copy the generated token and paste it into the **JWT Token** field on the dashboard.

Administrator permissions include:

* Start FFmpeg
* Stop FFmpeg
* Read runtime configuration
* Open HLS player
* Open DASH player

---

## Generate a Viewer Token

```bash
cd ~/aws-media-pipeline-observability/source-ec2

python3 - <<'PY'
import jwt
import datetime
from pathlib import Path

secret = ""

for line in Path(".env").read_text().splitlines():
    if line.startswith("JWT_SECRET="):
        secret = line.split("=",1)[1].strip()
        break

payload = {
    "sub": "viewer",
    "role": "viewer",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
}

print(jwt.encode(payload, secret, algorithm="HS256"))
PY
```

---

## Expected RBAC Behaviour

| Token         | Result                                |
| ------------- | ------------------------------------- |
| No Token      | 401 Unauthorized                      |
| Invalid Token | 401 Unauthorized                      |
| Expired Token | 401 Token Expired                     |
| Viewer Token  | 403 Administrator privileges required |
| Admin Token   | Full access to protected operations   |

---

## Dashboard Demonstration Workflow

1. Open the dashboard.

```
http://<EC2_PUBLIC_IP>:8000
```

2. Generate an **Admin JWT**.

3. Paste the token into the **JWT Token** field.

4. Demonstrate:

* Refresh Host Status
* Start FFmpeg
* Verify FFmpeg Status
* Open HLS Player
* Open DASH Player
* View Prometheus Metrics
* Open Prometheus
* Open Grafana
* Stop FFmpeg

5. Generate a **Viewer JWT**.

6. Repeat the same actions.

Expected result:

* Viewer can access public monitoring endpoints.
* Viewer is denied administrative operations with HTTP **403 Forbidden**.
* Admin has full operational access.

This demonstrates Role-Based Access Control (RBAC) implemented with JWT authentication.
