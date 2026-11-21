import os
import time
import json
import pandas as pd
from kafka import KafkaProducer

# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC_RAW", "terrain_survey.raw")
STREAM_DATA_PATH = os.getenv(
    "STREAM_DATA_PATH", 
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "processed", "production_stream.csv")
)
DELAY_SECONDS = float(os.getenv("STREAM_DELAY_SECONDS", "1.0"))

def create_producer():
    """Initializes and returns a KafkaProducer with JSON serialization and retry logic."""
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    for attempt in range(1, 11):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3
            )
            print("Connected to Kafka Producer successfully!")
            return producer
        except Exception as e:
            print(f"Attempt {attempt}/10: Kafka broker not ready yet ({e}). Waiting 3 seconds...")
            time.sleep(3)
    raise RuntimeError("Failed to connect to Kafka broker after 10 attempts.")

def run_stream():
    """Reads production_stream.csv row-by-row and emits events to Kafka."""
    if not os.path.exists(STREAM_DATA_PATH):
        raise FileNotFoundError(f"Stream dataset not found at {STREAM_DATA_PATH}")

    print(f"Loading stream dataset from: {STREAM_DATA_PATH}")
    df = pd.read_csv(STREAM_DATA_PATH)
    print(f"Total stream records available: {len(df):,}")

    producer = create_producer()
    print(f"Beginning continuous event streaming to topic: '{TOPIC}' (Delay: {DELAY_SECONDS}s/event)...\n")

    event_count = 0
    try:
        for idx, row in df.iterrows():
            payload = row.to_dict()
            # Send payload to Kafka topic
            producer.send(TOPIC, value=payload)
            event_count += 1

            if event_count % 10 == 0 or event_count == 1:
                print(f"[PRODUCER -> KAFKA] Emitted Event #{event_count}: Elevation={payload.get('Elevation')}m, Slope={payload.get('Slope')} deg")

            time.sleep(DELAY_SECONDS)

        producer.flush()
        print(f"\nStreaming completed! Total events pushed: {event_count}")
    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
    finally:
        producer.close()

if __name__ == "__main__":
    run_stream()
