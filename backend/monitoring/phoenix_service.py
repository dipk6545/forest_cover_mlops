import os
import pandas as pd
import phoenix as px
from phoenix.trace import using_project

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
REF_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "train_reference.csv")
STREAM_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "production_stream.csv")

def start_phoenix_service(port: int = 6006):
    """
    Launches the standalone Arize Phoenix observability server
    and logs baseline vs production datasets for drift evaluation.
    """
    print("=" * 70)
    print("🔥 STARTING ARIZE PHOENIX OBSERVABILITY ENGINE")
    print(f"Target Port: {port}")
    print("=" * 70)

    # 1. Launch Phoenix Session
    session = px.launch_app(port=port)
    print(f"✅ Arize Phoenix UI is live at: {session.url}")

    # 2. Load Datasets for Drift & Evaluation
    print(f"1. Loading reference training dataset ({REF_DATA_PATH})...")
    if not os.path.exists(REF_DATA_PATH):
        from backend.pipeline.pull_data import download_data_from_r2
        download_data_from_r2()

    df_ref = pd.read_csv(REF_DATA_PATH)
    ref_sample = df_ref.sample(n=min(5000, len(df_ref)), random_state=42)

    print(f"2. Loading production stream dataset ({STREAM_DATA_PATH})...")
    if not os.path.exists(STREAM_DATA_PATH):
        from backend.pipeline.pull_data import download_data_from_r2
        download_data_from_r2()

    df_stream = pd.read_csv(STREAM_DATA_PATH)
    stream_sample = df_stream.sample(n=min(2000, len(df_stream)), random_state=123)

    # 3. Register Reference Baseline & Stream Inferences into Phoenix
    client = px.Client(endpoint=f"http://localhost:{port}")
    
    print("3. Registering Reference Baseline and Production Inferences into Phoenix...")
    ref_dataset = client.upload_dataset(
        dataset_name="forest_cover_reference_baseline",
        dataframe=ref_sample
    )
    
    stream_dataset = client.upload_dataset(
        dataset_name="forest_cover_production_stream",
        dataframe=stream_sample
    )

    print("\n" + "=" * 70)
    print(f"🚀 Arize Phoenix Observability Stack Ready!")
    print(f"   - Dashboard URL: http://localhost:{port}")
    print(f"   - Reference Baseline: {ref_dataset.name}")
    print(f"   - Production Stream:  {stream_dataset.name}")
    print("=" * 70)
    return session

if __name__ == "__main__":
    import time
    sess = start_phoenix_service(port=6006)
    print("Holding Phoenix server open. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Arize Phoenix...")
