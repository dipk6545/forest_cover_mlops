FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including OpenMP runtime required by LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy full requirements and install all packages into the container image
COPY requirements.txt .

RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries=10 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy source code and artifacts
COPY backend /app/backend

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
