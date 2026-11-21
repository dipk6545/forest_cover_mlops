FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serve.txt .

# Use Cloudflare/Fastly CDN mirrors with extended timeout to bypass Codespaces PyPI throttling
RUN pip install --no-cache-dir \
    -i https://pypi.org/simple \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/ \
    --default-timeout=120 \
    --retries=5 \
    -r requirements-serve.txt

COPY backend /app/backend

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
