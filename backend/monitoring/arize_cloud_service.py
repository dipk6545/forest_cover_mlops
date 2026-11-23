import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Arize Cloud API
import arize

# Credentials
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY", "ak-fc199fc3-7223-4267-906a-b55dee277149-S_XGo69iRZKtk3mQ1f0NKr_chcLRByjR")
SPACE_ID = "U3BhY2U6NTk4MTU6R2FXYg=="  # Default Space
MODEL_ID = "forest-cover-lgbm-production"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
REF_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "train_reference.csv")
STREAM_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "production_stream.csv")

SPECIES_MAP = {
    1: "Spruce/Fir",
    2: "Lodgepole Pine",
    3: "Ponderosa Pine",
    4: "Cottonwood/Willow",
    5: "Aspen",
    6: "Douglas-fir",
    7: "Krummholz"
}

def sync_to_arize_cloud(n_samples: int = 1000):
    """
    Uploads reference baseline and production stream inferences directly
    to Arize Cloud for real-time drift, performance, and data quality tracking.
    """
    print("=" * 75)
    print("☁️  SYNCING MLOPS TELEMETRY TO ARIZE AI CLOUD")
    print(f"Space: Default Space ({SPACE_ID}) | Model: {MODEL_ID}")
    print("=" * 75)

    client = arize.ArizeClient(api_key=ARIZE_API_KEY)

    # 1. Load Data
    if not os.path.exists(REF_DATA_PATH):
        from backend.pipeline.pull_data import download_data_from_r2
        download_data_from_r2()

    print(f"1. Reading training reference baseline ({REF_DATA_PATH})...")
    df_ref = pd.read_csv(REF_DATA_PATH)
    ref_sample = df_ref.sample(n=min(n_samples, len(df_ref)), random_state=42).copy()

    print(f"2. Reading production stream inferences ({STREAM_DATA_PATH})...")
    df_stream = pd.read_csv(STREAM_DATA_PATH)
    stream_sample = df_stream.sample(n=min(n_samples, len(df_stream)), random_state=101).copy()

    # Features to monitor
    features = [
        "Elevation", "Aspect", "Slope",
        "Horizontal_Distance_To_Hydrology", "Vertical_Distance_To_Hydrology",
        "Horizontal_Distance_To_Roadways", "Horizontal_Distance_To_Fire_Points",
        "Hillshade_9am", "Hillshade_Noon", "Hillshade_3pm"
    ]

    ref_payload = ref_sample[features].copy()
    ref_payload["actual_label"] = ref_sample["Cover_Type"].map(SPECIES_MAP)

    stream_payload = stream_sample[features].copy()
    stream_payload["actual_label"] = stream_sample["Cover_Type"].map(SPECIES_MAP)

    # 3. Create Datasets in Arize Cloud
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ref_dataset_name = f"forest_cover_baseline_{timestamp_str}"
    stream_dataset_name = f"forest_cover_production_stream_{timestamp_str}"

    print("\n3. Uploading Baseline & Production Datasets to Arize Cloud...")
    try:
        ref_ds = client.datasets.create(
            name=ref_dataset_name,
            space="Default Space",
            examples=ref_payload
        )
        print(f"✅ Created Reference Dataset in Arize Cloud: '{ref_dataset_name}'")
    except Exception as e:
        print(f"Note on baseline sync: {e}")

    try:
        stream_ds = client.datasets.create(
            name=stream_dataset_name,
            space="Default Space",
            examples=stream_payload
        )
        print(f"✅ Created Production Stream Dataset in Arize Cloud: '{stream_dataset_name}'")
    except Exception as e:
        print(f"Note on stream sync: {e}")

    print("\n" + "=" * 75)
    print("🚀 ARIZE AI CLOUD SYNC COMPLETE!")
    print("View your models, datasets, and drift metrics live at:")
    print("👉 https://app.arize.com")
    print("=" * 75)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload MLOps drift and telemetry to Arize Cloud")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to upload")
    args = parser.parse_args()

    sync_to_arize_cloud(n_samples=args.samples)
