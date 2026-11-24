# End-to-End Forest Cover Type MLOps Platform

[![CI Pipeline](https://github.com/dipk6545/forest_cover_mlops/actions/workflows/ci.yml/badge.svg)](https://github.com/dipk6545/forest_cover_mlops/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Model Accuracy](https://img.shields.io/badge/LightGBM-94.2%25%20Accuracy-success.svg)](https://lightgbm.readthedocs.io/)
[![Dashboard](https://img.shields.io/badge/Grafana%20Cloud-Live%20Telemetry-orange.svg)](https://charmingjuniper1515.grafana.net/d/forest-cover-mlops-cloud/forest-cover-mlops-production-dashboard)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, real-time Machine Learning Operations (MLOps) platform that predicts forest cover types (7 tree species) across **581,012 survey observations** using **54 cartographic and geological features**.

Featuring an event-driven architecture powered by **Apache Kafka (KRaft)**, high-speed model scoring via **FastAPI**, experiment tracking and model registration via **MLflow**, zero-egress artifact caching on **Cloudflare R2**, real-time telemetry through **Grafana Cloud & Aiven PostgreSQL**, and continuous data drift auditing with **Evidently AI**.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Raw Survey Records   │
                                  │   (581,012 samples)    │
                                  └───────────┬────────────┘
                                              │ 70 / 30 Split
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
      ┌───────────────────────────────┐                 ┌─────────────────────────────┐
      │   train_reference.csv (70%)   │                 │ production_stream.csv (30%) │
      │   Baseline Reference & Drift  │                 │ Live Real-Time Ingestion    │
      └──────────────┬────────────────┘                 └──────────────┬──────────────┘
                     │                                                 │
                     │ Baseline                                        │ Stream Batch
                     ▼                                                 ▼
      ┌───────────────────────────────┐                 ┌─────────────────────────────┐
      │   Optuna + LightGBM Tuning    │                 │    Kafka Stream Producer    │
      │   (94.2% Validation Accuracy) │                 │ (backend/streaming/producer)│
      └──────────────┬────────────────┘                 └──────────────┬──────────────┘
                     │                                                 │
                     ▼ Model Artifacts                                 │ Socket TCP (9092)
      ┌───────────────────────────────┐                                ▼
      │   Cloudflare R2 Object Store  │                 ┌─────────────────────────────┐
      │   & MLflow Registry (Port 5000)                 │  Apache Kafka Broker (KRaft)│
      └──────────────┬────────────────┘                 │ (topic: terrain_survey.raw) │
                     │                                  └──────────────┬──────────────┘
                     │ Load Champion                                   │
                     ▼                                                 │ Subscribe
      ┌───────────────────────────────┐                                ▼
      │      FastAPI Serving API      │ ◄── HTTP POST ── ┌─────────────────────────────┐
      │ (http://localhost:8000/predict)                  │    Kafka Scoring Consumer   │
      └───────────────────────────────┘ ── JSON Resp ──► │ (backend/streaming/consumer)│
                                                         └──────────────┬──────────────┘
                                                                        │
                                   ┌────────────────────────────────────┴────────────────────────────────────┐
                                   ▼                                                                         ▼
                    ┌─────────────────────────────┐                                           ┌─────────────────────────────┐
                    │     Aiven PostgreSQL DB     │                                           │  Evidently AI Drift Service │
                    │   (Table: model_inferences) │                                           │ (backend/monitoring/drift)  │
                    └──────────────┬──────────────┘                                           └──────────────┬──────────────┘
                                   │                                                                         │
                                   ▼ SQL Queries (5s poll)                                                   ▼
                    ┌─────────────────────────────┐                                           ┌─────────────────────────────┐
                    │    Grafana Cloud Dashboard  │                                           │  Interactive HTML Reports   │
                    │   (Live Inference Telemetry)│                                           │  (Wasserstein / KS Drift)   │
                    └─────────────────────────────┘                                           └─────────────────────────────┘
```

---

## 📋 Prerequisites & Configuration

### 1. System Requirements
- **Docker Engine** 20.10+ and **Docker Compose** v2+
- **Python** 3.10 or 3.11
- Git, curl, bash

### 2. Environment Setup
Copy the template configuration and populate credentials (already configured in production):
```bash
cp .env.example .env
```

Key environment parameters:
| Parameter | Description | Default / Example |
| :--- | :--- | :--- |
| `MLFLOW_TRACKING_URI` | Aiven PostgreSQL connection URI | `postgresql+psycopg2://avnadmin:***@...` |
| `R2_ENDPOINT_URL` | Cloudflare R2 S3-compatible API endpoint | `https://<account_id>.r2.cloudflarestorage.com` |
| `AWS_ACCESS_KEY_ID` | Cloudflare R2 Access Key ID | S3 API credential |
| `AWS_SECRET_ACCESS_KEY` | Cloudflare R2 Secret Access Key | S3 API credential |
| `KAFKA_BROKER` | Local Kafka broker listener | `localhost:9092` |
| `API_PREDICT_URL` | Internal FastAPI prediction endpoint | `http://localhost:8000/predict` |

---

## 🚀 How to Run (Step-by-Step)

### Step 1: Start Minimal Local Infrastructure
Spin up the clean 3-container local stack (Kafka KRaft, FastAPI, MLflow):
```bash
docker compose up -d
```
Verify all 3 containers are healthy:
```bash
docker compose ps
```
*Expected: Only ports `9092` (Kafka), `8000` (FastAPI), and `5000` (MLflow) are active.*

---

### Step 2: Stream Live Inferences (Single Command)
Run the automated streaming pipeline. Pass the **number of records** and **sleep delay (seconds)**:
```bash
./stream.sh <SAMPLES> <DELAY_SECONDS>
```
#### Examples:
```bash
# Stream 50 events at 0.1s interval (fast demo)
./stream.sh 50 0.1

# Stream 200 events at 0.05s interval (high throughput test)
./stream.sh 200 0.05
```
*The script automatically creates Kafka topics, starts the background scoring consumer, connects to Aiven PostgreSQL, scores predictions via FastAPI, and pushes live records.*

---

### Step 3: Run Evidently AI Drift Audit (Single Command)
Evaluate incoming streaming batches against the 406,708 baseline reference rows:
```bash
# Standard distribution audit
./check_drift.sh 2000

# Simulated domain shift (+400m elevation bias to trigger alert)
./check_drift.sh 2000 --drift
```
The resulting interactive report is saved at:
👉 `backend/monitoring/reports/latest_drift_report.html`

---

### Step 4: Clean Teardown
To reset all background processes, stop containers, and clear temporary volumes:
```bash
docker compose down -v --remove-orphans && pkill -9 -f "python3.*(consumer|producer|stream|drift)" || true
```

---

## 📊 Observability & Production Dashboards

### 1. Hosted Grafana Cloud (Live Telemetry)
Access the live production dashboard:
👉 **[Forest Cover MLOps Production Dashboard](https://charmingjuniper1515.grafana.net/d/forest-cover-mlops-cloud/forest-cover-mlops-production-dashboard)**

| Panel Name | Type | Metric Queried |
| :--- | :--- | :--- |
| **Total Production Predictions** | Stat Counter | `SELECT COUNT(*) FROM model_inferences;` |
| **Average Inference Latency** | Gauge (ms) | `SELECT AVG(latency_ms) FROM model_inferences;` |
| **Scoring Throughput** | Time Series | Predictions processed per minute rolling bucket. |
| **Species Classification Breakdown**| Donut / Pie | Distribution across all 7 predicted tree species. |
| **Average Elevation by Species** | Bar Chart | Correlation between altitude (metres) and species. |

### 2. MLflow Experiment Tracker
Open **Port 5000** locally or in Codespaces:
- View all Optuna Bayesian tuning trials and hyperparameter search histories.
- Inspect confusion matrices, ROC-AUC curves, and log-loss curves.
- Access model artifacts and the registered production champion (`LightGBM_Production_Champion`).

---

## 🛠️ Project Structure

```
forest_cover_mlops/
├── backend/
│   ├── api/                     # FastAPI application & Pydantic request models
│   │   └── main.py              # /predict & /health endpoints
│   ├── artifacts/               # Scaler and local preprocessor binaries
│   ├── models/                  # Serialized LightGBM champion models
│   ├── monitoring/              # Observability and drift services
│   │   ├── drift_service.py     # Evidently AI drift detection engine
│   │   ├── ks_test.py           # Kolmogorov-Smirnov statistical tests
│   │   └── reports/             # HTML & JSON generated drift summaries
│   ├── pipeline/                # ETL, feature engineering & model training
│   │   ├── train.py             # Optuna Bayesian hyperparameter search
│   │   └── pull_data.py         # Cloudflare R2 automated data sync
│   └── streaming/               # Real-time streaming components
│       ├── producer.py          # Kafka event publisher
│       └── consumer.py          # Kafka scoring consumer & DB sink
├── data/                        # Tracked via DVC / Cloudflare R2
│   └── processed/               # Reference baseline & production stream CSVs
├── check_drift.sh               # Single-command Evidently AI drift runner
├── stream.sh                    # Single-command streaming & scoring runner
├── docker-compose.yml           # Minimal 3-service container architecture
├── Dockerfile                   # Multi-stage production container for FastAPI
├── pyproject.toml               # PEP 621 modern build configuration
├── requirements.txt             # Python runtime dependencies
├── Forest_Cover_MLOps_Final_Presentation.pptx # Clean presentation deck
└── FOREST_COVER_MLOPS_COMPLETE_GUIDE.md        # Exhaustive technical reference
```

---

## 👤 Author & License
- **Author**: Subhadip Khawas (Roll No. `E26008`)
- **License**: [MIT](LICENSE)
