"""
Utility script to download processed training and stream datasets from Cloudflare R2
or fetch directly from the official UCI / Kaggle repository if not present locally.
"""

import os
import boto3
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def download_data_from_r2():
    r2_endpoint = os.getenv("R2_ENDPOINT_URL") or os.getenv("MLFLOW_S3_ENDPOINT_URL")
    r2_bucket = os.getenv("R2_BUCKET_NAME", "netsentry")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not (r2_endpoint and aws_key and aws_secret):
        print("Missing Cloudflare R2 credentials in .env")
        return False

    s3 = boto3.client(
        "s3",
        endpoint_url=r2_endpoint,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name="auto"
    )

    files = [
        ("forest-cover-mlops/data/train_reference.csv", os.path.join(DATA_DIR, "train_reference.csv")),
        ("forest-cover-mlops/data/production_stream.csv", os.path.join(DATA_DIR, "production_stream.csv"))
    ]

    for key, local_dest in files:
        if not os.path.exists(local_dest):
            print(f"Downloading {key} from Cloudflare R2 ({r2_bucket}) -> {local_dest}...")
            s3.download_file(r2_bucket, key, local_dest)
            print(f"✅ Downloaded {os.path.basename(local_dest)}")
        else:
            print(f"✓ {os.path.basename(local_dest)} already exists locally.")

    return True

if __name__ == "__main__":
    download_data_from_r2()
