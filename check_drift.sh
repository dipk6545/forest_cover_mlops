#!/usr/bin/env bash
set -e

# ==============================================================================
# All-in-One Evidently AI Data Drift Check
# Usage: ./check_drift.sh [NUM_SAMPLES] [--drift]
# Example: ./check_drift.sh 2000
# Example: ./check_drift.sh 2000 --drift
# ==============================================================================

SAMPLES=${1:-2000}
DRIFT_FLAG=""

if [ "$2" == "--drift" ] || [ "$1" == "--drift" ]; then
    DRIFT_FLAG="--drift"
fi

cd "$(dirname "$0")"

echo "======================================================================"
echo "📊 RUNNING EVIDENTLY AI DRIFT ANALYSIS"
echo "Evaluating: $SAMPLES samples vs Baseline Reference Data"
if [ -n "$DRIFT_FLAG" ]; then
    echo "Mode: Simulated Domain Shift (+400m elevation bias)"
else
    echo "Mode: Standard Production Stream Evaluation"
fi
echo "======================================================================"

python3 backend/monitoring/drift_service.py --samples "$SAMPLES" $DRIFT_FLAG

echo ""
echo "Interactive HTML Report generated:"
echo "👉 backend/monitoring/reports/latest_drift_report.html"
echo "(In VS Code / Codespaces: Right click on latest_drift_report.html -> 'Open with Live Server' or Preview)"
