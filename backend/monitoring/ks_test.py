"""
Dedicated Kolmogorov-Smirnov (KS) Two-Sample Test Service for Continuous Feature Drift.

The two-sample Kolmogorov-Smirnov test tests whether two underlying one-dimensional
continuous distributions differ significantly.
Hypotheses:
  H0 (Null): The production stream and reference baseline come from the same distribution.
  H1 (Alternative): The distributions are different (data drift has occurred).

Decision rule: If p_value < alpha (default 0.05) and KS statistic > threshold, flag feature as DRIFTED.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scipy import stats

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
REF_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "train_reference.csv")
STREAM_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "production_stream.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "monitoring", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

CONTINUOUS_FEATURES = [
    "Elevation",
    "Aspect",
    "Slope",
    "Horizontal_Distance_To_Hydrology",
    "Vertical_Distance_To_Hydrology",
    "Horizontal_Distance_To_Roadways",
    "Horizontal_Distance_To_Fire_Points",
    "Hillshade_9am",
    "Hillshade_Noon",
    "Hillshade_3pm",
]

def run_ks_drift_test(
    n_samples: int = 5000,
    alpha: float = 0.05,
    inject_drift: bool = False,
    drift_feature: str = "Elevation",
    drift_delta: float = 400.0,
):
    print("=" * 85)
    print("KOLMOGOROV-SMIRNOV (KS) TWO-SAMPLE DRIFT ANALYSIS")
    print(f"Alpha (Significance Level): {alpha} | Batch Size: {n_samples}")
    print("=" * 85)

    # 1. Load baseline & production sample
    df_ref = pd.read_csv(REF_DATA_PATH, usecols=CONTINUOUS_FEATURES)
    df_prod = pd.read_csv(STREAM_DATA_PATH, usecols=CONTINUOUS_FEATURES)

    ref_sample = df_ref.sample(n=min(n_samples, len(df_ref)), random_state=42)
    prod_sample = df_prod.sample(n=min(n_samples, len(df_prod)), random_state=101).copy()

    if inject_drift:
        print(f"⚠️  Injecting synthetic domain shift into '{drift_feature}': +{drift_delta}")
        prod_sample[drift_feature] = prod_sample[drift_feature] + drift_delta

    results = []
    drift_count = 0

    print(f"\n{'Feature':<35} | {'KS Stat (D)':<12} | {'p-value':<12} | {'Drift Status':<12}")
    print("-" * 85)

    for col in CONTINUOUS_FEATURES:
        data_ref = ref_sample[col].values
        data_prod = prod_sample[col].values

        # Run 2-sample Kolmogorov-Smirnov test
        ks_res = stats.ks_2samp(data_ref, data_prod)
        stat = float(ks_res.statistic)
        p_val = float(ks_res.pvalue)

        # Flag drift if p-value is below significance threshold
        is_drift = bool(p_val < alpha)
        if is_drift:
            drift_count += 1
            status_str = "🚨 DRIFT"
        else:
            status_str = "✅ STABLE"

        print(f"{col:<35} | {stat:<12.5f} | {p_val:<12.4e} | {status_str:<12}")

        results.append({
            "feature": col,
            "ks_statistic": round(stat, 6),
            "p_value": p_val,
            "alpha": alpha,
            "drift_detected": is_drift,
            "reference_mean": float(np.mean(data_ref)),
            "production_mean": float(np.mean(data_prod)),
            "reference_std": float(np.std(data_ref)),
            "production_std": float(np.std(data_prod))
        })

    print("-" * 85)
    drift_share = drift_count / len(CONTINUOUS_FEATURES)
    dataset_drift = drift_share >= 0.3
    summary_banner = "🚨 DATASET-LEVEL DRIFT DETECTED" if dataset_drift else "✅ DATASET STABLE"
    print(f"Summary: {drift_count}/{len(CONTINUOUS_FEATURES)} features drifted ({drift_share * 100:.1f}%). Result: {summary_banner}")

    report_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_features_tested": len(CONTINUOUS_FEATURES),
        "drifted_features_count": drift_count,
        "dataset_drift_detected": dataset_drift,
        "alpha": alpha,
        "features": results
    }

    # Save to reports
    out_file = os.path.join(REPORTS_DIR, "ks_drift_report.json")
    with open(out_file, "w") as f:
        json.dump(report_payload, f, indent=2)

    print(f"\n[Artifact Saved] Detailed KS metrics written to: {out_file}\n")
    return report_payload

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Kolmogorov-Smirnov 2-sample test for feature drift")
    parser.add_argument("--drift", action="store_true", help="Inject artificial drift into Elevation")
    parser.add_argument("--samples", type=int, default=5000, help="Sample size per distribution")
    parser.add_argument("--alpha", type=float, default=0.05, help="p-value significance threshold")
    args = parser.parse_args()

    run_ks_drift_test(n_samples=args.samples, alpha=args.alpha, inject_drift=args.drift)
