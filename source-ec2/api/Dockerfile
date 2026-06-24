# ------------------------------------------------------------
# BASE IMAGE
# ------------------------------------------------------------
# Lightweight Python environment
FROM python:3.11-slim


# ------------------------------------------------------------
# SYSTEM DEPENDENCIES
# ------------------------------------------------------------
# We install Linux tools required by API:
#
# procps:
#   - top    (CPU usage)
#   - free   (memory usage)
#   - ps     (process listing)
#
# iputils-ping:
#   - ping (network checks)
#
# curl:
#   - HTTP request tool (used for internet check)
#
RUN apt-get update && apt-get install -y \
    procps \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# WORKING DIRECTORY INSIDE CONTAINER
# ------------------------------------------------------------
WORKDIR /app


# ------------------------------------------------------------
# INSTALL PYTHON DEPENDENCIES
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ------------------------------------------------------------
# COPY APPLICATION CODE
# ------------------------------------------------------------
COPY api.py .


# ------------------------------------------------------------
# EXPOSE PORT
# ------------------------------------------------------------
# This tells Docker container listens on port 8000
EXPOSE 8000


# ------------------------------------------------------------
# START APPLICATION
# ------------------------------------------------------------
# uvicorn runs FastAPI server
# 0.0.0.0 = allow external access (important!)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
