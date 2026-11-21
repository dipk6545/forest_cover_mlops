import os
import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from backend.api.schemas import (
    TerrainFeatures,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse
)

# Initialize FastAPI application
app = FastAPI(
    title="Forest Cover Type ML Serving API",
    description="Real-Time and Batch Inference Service for Forest Terrain Classification",
    version="1.0.0"
)

# Enable CORS for Cloudflare Pages and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Cloudflare Pages frontend & localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics instrumentation
REQUEST_COUNT = Counter("api_requests_total", "Total requests received", ["endpoint", "status"])
INFERENCE_LATENCY = Histogram("prediction_latency_seconds", "Inference latency in seconds")
PREDICTION_COUNTER = Counter("predictions_by_class_total", "Predictions count by Cover Type", ["cover_type"])

# Paths to model artifacts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.joblib")
META_PATH = os.path.join(BASE_DIR, "artifacts", "metadata.json")

# Global model state
model = None
metadata = {}
expected_features: List[str] = []

SPECIES_MAP = {
    1: "Spruce/Fir",
    2: "Lodgepole Pine",
    3: "Ponderosa Pine",
    4: "Cottonwood/Willow",
    5: "Aspen",
    6: "Douglas-fir",
    7: "Krummholz"
}

@app.on_event("startup")
def load_model_artifacts():
    """
    Loads the trained LightGBM model and feature schema on API boot.
    If the model does not exist locally, it automatically pulls it from Cloudflare R2!
    """
    global model, metadata, expected_features
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"Model artifact not found locally at {MODEL_PATH}. Attempting to pull from Cloudflare R2...")
            r2_endpoint = os.getenv("R2_ENDPOINT_URL") or os.getenv("MLFLOW_S3_ENDPOINT_URL")
            r2_bucket = os.getenv("R2_BUCKET_NAME", "netsentry")
            aws_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
            
            if r2_endpoint and aws_key and aws_secret:
                try:
                    import boto3
                    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
                    s3 = boto3.client(
                        "s3",
                        endpoint_url=r2_endpoint,
                        aws_access_key_id=aws_key,
                        aws_secret_access_key=aws_secret,
                        region_name="auto"
                    )
                    r2_key = "forest-cover-mlops/artifacts/model.joblib"
                    print(f"Downloading model from Cloudflare R2 ({r2_bucket}/{r2_key}) to {MODEL_PATH}...")
                    s3.download_file(r2_bucket, r2_key, MODEL_PATH)
                    print("✅ Successfully downloaded model artifact from Cloudflare R2!")
                except Exception as dl_err:
                    print(f"⚠️ Failed to pull from Cloudflare R2: {dl_err}")

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH} and could not be fetched from R2")
        
        model = joblib.load(MODEL_PATH)
        print(f"Loaded production model from {MODEL_PATH}")

        if os.path.exists(META_PATH):
            with open(META_PATH, "r") as f:
                metadata = json.load(f)
                expected_features = metadata.get("features", [])
                print(f"Loaded metadata with {len(expected_features)} expected features")
    except Exception as e:
        print(f"FATAL: Error loading model artifacts: {e}")
        raise e

def preprocess_features(raw_items: List[TerrainFeatures]) -> pd.DataFrame:
    """
    Applies the domain feature engineering and one-hot encoding on raw inputs.
    """
    records = [item.dict() for item in raw_items]
    df = pd.DataFrame(records)

    # 1. 3D Euclidean distance to water
    df["Euclidean_Distance_To_Hydrology"] = np.sqrt(
        df["Horizontal_Distance_To_Hydrology"]**2 + df["Vertical_Distance_To_Hydrology"]**2
    )

    # 2. Water elevation
    df["Elevation_Minus_VDist_Hydrology"] = df["Elevation"] - df["Vertical_Distance_To_Hydrology"]

    # 3. Cyclical Aspect encodings
    df["Aspect_Sin"] = np.sin(df["Aspect"] * np.pi / 180.0)
    df["Aspect_Cos"] = np.cos(df["Aspect"] * np.pi / 180.0)

    # 4. Mean distance to amenities
    df["Mean_Distance_To_Amenities"] = (
        df["Horizontal_Distance_To_Hydrology"] + 
        df["Horizontal_Distance_To_Roadways"] + 
        df["Horizontal_Distance_To_Fire_Points"]
    ) / 3.0

    # 5. Hillshade diurnal range
    df["Hillshade_Range"] = df["Hillshade_Noon"] - df["Hillshade_9am"]

    # 6. One-hot encode Wilderness Areas (1 to 4)
    for i in range(1, 5):
        df[f"Wilderness_Area_{i}"] = (df["Wilderness_Area"] == i).astype(int)
    df.drop(columns=["Wilderness_Area"], inplace=True)

    # 7. One-hot encode Soil Types (1 to 40)
    for i in range(1, 41):
        df[f"Soil_Type_{i}"] = (df["Soil_Type"] == i).astype(int)
    df.drop(columns=["Soil_Type"], inplace=True)

    # Align columns with exact training feature order
    if expected_features:
        for feat in expected_features:
            if feat not in df.columns:
                df[feat] = 0
        df = df[expected_features]

    return df

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Returns system and model health status.
    """
    REQUEST_COUNT.labels(endpoint="/health", status="200").inc()
    return {
        "status": "healthy",
        "service": "forest_cover_ml_serving",
        "model_loaded": model is not None,
        "model_version": metadata.get("version", "1.0.0"),
        "expected_features_count": len(expected_features)
    }

@app.post("/predict", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def predict_single(terrain: TerrainFeatures):
    """
    Real-Time Single Sample Inference.
    """
    if model is None:
        REQUEST_COUNT.labels(endpoint="/predict", status="503").inc()
        raise HTTPException(status_code=503, detail="Model is not loaded")

    start_time = time.time()
    try:
        # Preprocess raw input into full feature vector
        X_input = preprocess_features([terrain])

        # Inference
        probs = model.predict_proba(X_input)[0]
        pred_class_idx = int(np.argmax(probs))
        pred_cover_type = pred_class_idx + 1  # Map 0..6 back to 1..7
        confidence = float(probs[pred_class_idx])

        latency = (time.time() - start_time) * 1000.0

        # Prometheus metrics
        INFERENCE_LATENCY.observe(latency / 1000.0)
        REQUEST_COUNT.labels(endpoint="/predict", status="200").inc()
        PREDICTION_COUNTER.labels(cover_type=str(pred_cover_type)).inc()

        return PredictionResponse(
            cover_type_id=pred_cover_type,
            tree_species=SPECIES_MAP.get(pred_cover_type, "Unknown"),
            confidence=round(confidence, 4),
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/predict", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_batch", response_model=BatchPredictionResponse, status_code=status.HTTP_200_OK)
def predict_batch(request: BatchPredictionRequest):
    """
    High-Throughput Batch Inference Endpoint.
    """
    if model is None:
        REQUEST_COUNT.labels(endpoint="/predict_batch", status="503").inc()
        raise HTTPException(status_code=503, detail="Model is not loaded")

    start_time = time.time()
    try:
        X_input = preprocess_features(request.items)
        probs_matrix = model.predict_proba(X_input)
        pred_indices = np.argmax(probs_matrix, axis=1)

        total_latency = (time.time() - start_time) * 1000.0
        avg_latency = total_latency / max(len(request.items), 1)

        results = []
        for i, idx in enumerate(pred_indices):
            cover_type = int(idx) + 1
            conf = float(probs_matrix[i][idx])
            PREDICTION_COUNTER.labels(cover_type=str(cover_type)).inc()
            results.append(PredictionResponse(
                cover_type_id=cover_type,
                tree_species=SPECIES_MAP.get(cover_type, "Unknown"),
                confidence=round(conf, 4),
                latency_ms=round(avg_latency, 2)
            ))

        REQUEST_COUNT.labels(endpoint="/predict_batch", status="200").inc()
        return BatchPredictionResponse(
            total_samples=len(results),
            predictions=results
        )
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/predict_batch", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
def get_metrics():
    """
    Exposes Prometheus operational metrics for scraping.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
