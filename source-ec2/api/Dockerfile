# Use a small official Python 3.11 base image for the FastAPI application.
FROM python:3.11-slim

# Install host/process diagnostic utilities.
# util-linux provides nsenter, which is required to execute host-side scripts
# from the privileged container. Removing apt lists keeps the image smaller.
RUN apt-get update && apt-get install -y \
    procps \
    iproute2 \
    iputils-ping \
    curl \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# All following copies and the Uvicorn command operate from /app.
WORKDIR /app

# Copy dependency metadata first to preserve Docker layer caching when only
# application source files change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API module and static dashboard into the runtime image.
COPY api.py .
COPY dashboard.html .

# Document the FastAPI/Uvicorn listening port.
EXPOSE 8000

# Bind on every container interface so Docker's published port can reach it.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
