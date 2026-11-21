import os
import json
import joblib
import optuna
import pandas as pd
import numpy as np
import mlflow
import mlflow.lightgbm
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from dotenv import load_dotenv

from backend.pipeline.feature_engineering import build_features

# 1. Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# 2. Configure MLflow Tracking
mlflow_tracking_uri = os.getenv("MLFLOW_HTTP_URI", "http://localhost:5000")
mlflow.set_tracking_uri(mlflow_tracking_uri)

experiment_name = "forest-cover-classification"
mlflow.set_experiment(experiment_name)

def run_training_pipeline(n_trials: int = 5, use_optuna: bool = True):
    """
    Executes the end-to-end ML training pipeline with Optuna Bayesian Hyperparameter Tuning:
    Data Loading -> Feature Engineering -> Train/Val/Test Split -> Optuna Tuning -> Best Model MLflow Logging
    """
    print("=" * 70)
    print("STARTING ML TRAINING & OPTUNA HYPERPARAMETER TUNING PIPELINE")
    print(f"Tracking Server: {mlflow_tracking_uri} | Optuna Trials: {n_trials if use_optuna else 1}")
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
        print("Dataset not found locally. Auto-pulling from Cloudflare R2...")
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

    y_train_idx = y_train - 1
    y_val_idx = y_val - 1
    y_test_idx = y_test - 1

    best_params = {}
    
    if use_optuna and n_trials > 1:
        print(f"\n4. Starting Optuna Bayesian Search across {n_trials} trials...")
        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial):
            trial_params = {
                "objective": "multiclass",
                "num_class": 7,
                "n_estimators": trial.suggest_int("n_estimators", 100, 250, step=50),
                "learning_rate": trial.suggest_float("learning_rate", 0.05, 0.15, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 63, 150),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.7, 0.95),
                "subsample": trial.suggest_float("subsample", 0.7, 1.0),
                "random_state": 42,
                "n_jobs": -1,
                "verbose": -1
            }

            with mlflow.start_run(run_name=f"Optuna_Trial_{trial.number}", nested=True):
                mlflow.log_params(trial_params)
                model = lgb.LGBMClassifier(**trial_params)
                model.fit(X_train, y_train_idx)
                
                val_preds = model.predict(X_val) + 1
                val_acc = accuracy_score(y_val, val_preds)
                mlflow.log_metric("val_accuracy", val_acc)
                return val_acc

        with mlflow.start_run(run_name="Optuna_Bayesian_Study") as parent_run:
            mlflow.log_param("n_trials", n_trials)
            study = optuna.create_study(direction="maximize")
            study.optimize(objective, n_trials=n_trials)
            
            print(f"   Best Trial: #{study.best_trial.number} with Val Accuracy: {study.best_value:.4f}")
            best_params = study.best_params
            best_params["objective"] = "multiclass"
            best_params["num_class"] = 7
            best_params["random_state"] = 42
            best_params["n_jobs"] = -1
            best_params["verbose"] = -1
            mlflow.log_params(best_params)
            mlflow.log_metric("best_val_accuracy", study.best_value)
    else:
        best_params = {
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

    # 5. Final Production Model MLflow Run
    print("\n5. Training Final Production Model with Best Hyperparameters...")
    with mlflow.start_run(run_name="LightGBM_Production_Champion") as run:
        mlflow.log_params(best_params)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("n_features", len(feature_names))

        final_model = lgb.LGBMClassifier(**best_params)
        final_model.fit(X_train, y_train_idx)

        # Validation & Test Evaluation
        val_preds = final_model.predict(X_val) + 1
        val_acc = accuracy_score(y_val, val_preds)
        val_f1 = f1_score(y_val, val_preds, average="weighted")

        test_preds = final_model.predict(X_test) + 1
        test_acc = accuracy_score(y_test, test_preds)
        test_f1 = f1_score(y_test, test_preds, average="weighted")

        print(f"   Validation Accuracy: {val_acc:.4f} | F1: {val_f1:.4f}")
        print(f"   Test Accuracy:       {test_acc:.4f} | F1: {test_f1:.4f}")

        mlflow.log_metric("val_accuracy", val_acc)
        mlflow.log_metric("val_f1_weighted", val_f1)
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.log_metric("test_f1_weighted", test_f1)

        # 6. Save Model Artifact
        model_local_path = os.path.join(models_dir, "model.joblib")
        joblib.dump(final_model, model_local_path)
        print(f"6. Saved model locally to: {model_local_path}")

        # Metadata
        metadata = {
            "model_name": "Forest_Cover_Type_LightGBM",
            "version": "1.0.0",
            "run_id": run.info.run_id,
            "n_features": len(feature_names),
            "features": feature_names,
            "target": "Cover_Type",
            "best_params": best_params,
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

    print("\n" + "=" * 70)
    print("OPTUNA HYPERPARAMETER TUNING & MLFLOW PIPELINE COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run LightGBM Training Pipeline with Optuna and MLflow")
    parser.add_argument("--trials", type=int, default=5, help="Number of Optuna Bayesian trials")
    parser.add_argument("--no-optuna", action="store_true", help="Skip Optuna and train with fixed baseline params")
    args = parser.parse_args()

    run_training_pipeline(n_trials=args.trials, use_optuna=not args.no_optuna)
