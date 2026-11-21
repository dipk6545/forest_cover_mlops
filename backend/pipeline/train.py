import os
import json
import joblib
import pandas as pd
import numpy as np
import mlflow
import mlflow.lightgbm
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from dotenv import load_dotenv

from backend.pipeline.feature_engineering import build_features

# 1. Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# 2. Configure MLflow Tracking & Cloudflare R2 Artifact Storage
mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
mlflow.set_tracking_uri(mlflow_tracking_uri)

experiment_name = "forest-cover-classification"
mlflow.set_experiment(experiment_name)

def run_training_pipeline():
    """
    Executes the end-to-end ML training pipeline:
    Data Loading -> Feature Engineering -> Train/Val/Test Split -> LightGBM Training -> MLflow Logging
    """
    print("=" * 70)
    print("STARTING ML TRAINING & MLFLOW PIPELINE")
    print("=" * 70)

    # Paths
    train_path = os.path.join(PROJECT_ROOT, "data", "processed", "train_reference.csv")
    models_dir = os.path.join(BASE_DIR, "models")
    artifacts_dir = os.path.join(BASE_DIR, "artifacts")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    # 1. Load Data
    print(f"1. Loading reference training dataset: {train_path}...")
    if not os.path.exists(train_path):
        print(f"Dataset not found locally. Auto-pulling from Cloudflare R2...")
        from backend.pipeline.pull_data import download_data_from_r2
        download_data_from_r2()

    df_raw = pd.read_csv(train_path)

    # 2. Feature Engineering
    print("2. Generating engineered cartographic features...")
    df_feat = build_features(df_raw)

    X = df_feat.drop(columns=["Cover_Type"])
    y = df_feat["Cover_Type"]
    feature_names = list(X.columns)

    # 3. Stratified Split (70% Train, 15% Validation, 15% Test)
    print("3. Performing stratified 70/15/15 split...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    # 4. Hyperparameters
    params = {
        "objective": "multiclass",
        "num_class": 7,
        "n_estimators": 200,
        "learning_rate": 0.095,
        "num_leaves": 127,
        "colsample_bytree": 0.80,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    }

    # 5. MLflow Run
    with mlflow.start_run(run_name="LightGBM_Production_Model") as run:
        print(f"4. MLflow Run started. Run ID: {run.info.run_id}")

        # Log parameters
        mlflow.log_params(params)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("val_samples", len(X_val))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("n_features", len(feature_names))

        # Train model
        print("5. Training LightGBM model...")
        model = lgb.LGBMClassifier(**params)
        model.fit(X_train, y_train - 1)  # 0-indexed for LightGBM

        # Validation Metrics
        val_preds = model.predict(X_val) + 1
        val_acc = accuracy_score(y_val, val_preds)
        val_f1 = f1_score(y_val, val_preds, average="weighted")

        # Test Metrics
        test_preds = model.predict(X_test) + 1
        test_acc = accuracy_score(y_test, test_preds)
        test_f1 = f1_score(y_test, test_preds, average="weighted")

        print(f"   Validation Accuracy: {val_acc:.4f} | F1: {val_f1:.4f}")
        print(f"   Test Accuracy:       {test_acc:.4f} | F1: {test_f1:.4f}")

        # Log metrics to MLflow
        mlflow.log_metric("val_accuracy", val_acc)
        mlflow.log_metric("val_f1_weighted", val_f1)
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.log_metric("test_f1_weighted", test_f1)

        # 6. Save Model Artifacts
        model_local_path = os.path.join(models_dir, "model.joblib")
        joblib.dump(model, model_local_path)
        print(f"6. Saved model locally to: {model_local_path}")

        # Log artifact to MLflow / R2
        try:
            mlflow.log_artifact(model_local_path, artifact_path="model")
            print("   Model logged to MLflow artifact store.")
        except Exception as e:
            print(f"   Note on remote artifact upload: {e}")

        # Save metadata and schema
        metadata = {
            "model_name": "Forest_Cover_Type_LightGBM",
            "version": "1.0.0",
            "run_id": run.info.run_id,
            "n_features": len(feature_names),
            "features": feature_names,
            "target": "Cover_Type",
            "metrics": {
                "val_accuracy": float(val_acc),
                "val_f1": float(val_f1),
                "test_accuracy": float(test_acc),
                "test_f1": float(test_f1)
            }
        }
        meta_local_path = os.path.join(artifacts_dir, "metadata.json")
        with open(meta_local_path, "w") as f:
            json.dump(metadata, f, indent=2)

    print("=" * 70)
    print("PIPELINE EXECUTION COMPLETE & LOGGED!")
    print("=" * 70)

if __name__ == "__main__":
    run_training_pipeline()
