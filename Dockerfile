FROM python:3.11-slim

WORKDIR /app

# Install minimal curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight serving dependencies
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

# Copy backend source code and model artifacts
COPY backend /app/backend

ENV PYTHONPATH=/app
EXPOSE 8000

# Run FastAPI serving engine
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
