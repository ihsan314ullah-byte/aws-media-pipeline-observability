# First-Time Setup & Troubleshooting

This section covers the most common issues encountered when deploying the project on a fresh environment.

---

## 1. Generate the Runtime `.env` File

The observability repository requires a runtime `.env` file generated from the Terraform outputs.

From the Terraform Repository/PC : for ex in my-case

```powershell
cd C:\Users\<username>\Desktop\terraform-aws-mediaconnect-lab

Set-ExecutionPolicy -Scope Process Bypass

.\scripts\generate-runtime-env.ps1
```

The script reads the current Terraform outputs and generates a `.env` file containing values such as:

* `SRT_TARGET_IP`
* `SRT_TARGET_PORT`
* `SRT_LATENCY_MS`
* `HLS_URL`
* `DASH_URL`

If PowerShell reports:

```
Running scripts is disabled on this system
```
then for the current PowerShell session, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```
---

## 2. Copy the Runtime `.env` to the EC2 Repository

After generating the `.env` file, copy it to the EC2 instance:

```powershell
scp -i "<path-to-key>.pem" .env ubuntu@<EC2_PUBLIC_IP>:~/aws-media-pipeline-observability/source-ec2/.env
```

If `scp` reports:

```
stat local ".env": No such file or directory
```

verify that the `.env` file was successfully generated before attempting the copy.

---

## 3. Verify the `.env` File

On the EC2 instance:

```bash
cat .env
```

Ensure values such as the following appear on a **single line**:

```env
SRT_TARGET_IP=54.xxx.xxx.xxx
SRT_TARGET_PORT=5000
SRT_LATENCY_MS=2000
```

Incorrect formatting (extra spaces, blank lines, or Windows line endings) can prevent FFmpeg from resolving the SRT destination.

If necessary, convert Windows line endings:

```bash
sed -i 's/\r$//' .env
```

---

## 4. Install Docker Compose

Some Ubuntu images include Docker Engine but not the Docker Compose plugin.

Verify:

```bash
docker compose version
```

If unavailable:

```bash
sudo apt update
sudo apt install -y docker-compose-v2
```

or

```bash
sudo apt install -y docker-compose-plugin
```

Verify again:

```bash
docker compose version
```

---

## 5. Start the Observability Stack

```bash
cd ~/aws-media-pipeline-observability/source-ec2

docker compose up -d

docker compose ps
```

---

## 6. FFmpeg Fails with "Failed to resolve hostname"

If the UI returns:

```
Failed to resolve hostname
```

verify that the `.env` file does not contain blank lines or hidden carriage return characters.

The SRT target should be constructed as:

```
srt://<SRT_TARGET_IP>:<SRT_TARGET_PORT>?mode=caller&latency=<SRT_LATENCY_MS>
```

---

## 7. CloudWatch Integration (Cross-Account)

This project supports Grafana running in a different AWS account from the Terraform-managed media infrastructure.

### Account A (Terraform / Media Services)

Create an IAM role (for example, `GrafanaCloudWatchReadRole`) with permissions to read:

* CloudWatch Metrics
* CloudWatch Logs

Configure the trust policy to allow the EC2 IAM role from Account B to assume it.

### Account B (Grafana EC2)

Attach an IAM role (for example, `GrafanaEC2Role`) to the EC2 instance with permission to call:

```
sts:AssumeRole
```

against the Account A role.

Configure the Grafana CloudWatch data source:

* Authentication: AWS SDK Default
* Assume Role ARN: `arn:aws:iam::<ACCOUNT_A_ID>:role/GrafanaCloudWatchReadRole`
* Region: `us-east-1`

If Grafana reports:

```
no EC2 IMDS role found
```

verify that an IAM role is attached to the EC2 instance.

---

## 8. Useful Verification Commands

Docker:

```bash
docker --version
docker compose version
docker compose ps
```

Terraform:

```powershell
terraform output
```

Runtime Environment:

```bash
cat .env
```

FFmpeg:

```bash
./scripts/status.sh
tail -f logs/ffmpeg.log
```

Grafana:

```
http://<EC2_PUBLIC_IP>:3000
```

FastAPI Dashboard:

```
http://<EC2_PUBLIC_IP>:8000/dashboard
```

Prometheus:

```
http://<EC2_PUBLIC_IP>:9090
```
