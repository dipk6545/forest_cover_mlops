FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serve.txt .

# Use PyPI official wheel host directly with trusted-host and extended timeout
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries=10 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements-serve.txt

COPY backend /app/backend

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
