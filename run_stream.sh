#!/usr/bin/env bash
set -e

# ==============================================================================
# All-in-One Kafka Streaming & Real-Time Inference Runner
# ==============================================================================

echo "======================================================================"
echo "🌲 LAUNCHING REAL-TIME EVENT STREAMING & INFERENCE PIPELINE"
echo "======================================================================"

# 1. Install confluent-kafka if missing
python3 -c "import confluent_kafka" 2>/dev/null || {
    echo "Installing confluent-kafka..."
    pip install confluent-kafka
}

# 2. Start Kafka Consumer in the background
echo "1. Starting Kafka Scoring Consumer in background..."
python3 backend/streaming/consumer.py &
CONSUMER_PID=$!

# Ensure consumer process cleans up on exit
cleanup() {
    echo ""
    echo "Stopping background consumer (PID $CONSUMER_PID)..."
    kill $CONSUMER_PID 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# 3. Wait 2 seconds for consumer connection to register
sleep 2

# 4. Run Producer to stream 50 real-time events
BATCH_SIZE=${1:-50}
DELAY=${2:-0.1}

echo "2. Streaming $BATCH_SIZE live terrain survey events (delay: ${DELAY}s)..."
python3 backend/streaming/producer.py --batch-size "$BATCH_SIZE" --delay "$DELAY"

# 5. Allow consumer a moment to finish processing remaining queue
sleep 2

echo "======================================================================"
echo "✅ STREAMING & INFERENCE COMPLETE!"
echo "Check Prometheus (Port 9090) to view request spikes!"
echo "======================================================================"
