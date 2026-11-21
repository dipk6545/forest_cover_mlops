import os
import time
import json
import pandas as pd
from confluent_kafka import Producer

# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC_RAW", "terrain_survey.raw")
STREAM_DATA_PATH = os.getenv(
    "STREAM_DATA_PATH", 
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "processed", "production_stream.csv")
)
DELAY_SECONDS = float(os.getenv("STREAM_DELAY_SECONDS", "0.2"))

def delivery_report(err, msg):
    """Callback triggered by producer on message delivery status."""
    if err is not None:
        print(f"⚠️ Message delivery failed: {err}")

def create_producer():
    """Initializes and returns a Confluent Kafka Producer."""
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'client.id': 'forest-stream-producer'
    }
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    producer = Producer(conf)
    print("Connected to Kafka Producer successfully!")
    return producer

def stream_production_events(batch_size: int = 100, delay: float = 0.2):
    """
    Streams rows from production_stream.csv to Kafka topic.
    """
    print("=" * 70)
    print("STARTING KAFKA PRODUCTION STREAM PRODUCER")
    print(f"Target Broker: {KAFKA_BROKER} | Topic: {TOPIC}")
    print("=" * 70)

    if not os.path.exists(STREAM_DATA_PATH):
        print(f"Stream dataset not found at {STREAM_DATA_PATH}. Auto-pulling from Cloudflare R2...")
        from backend.pipeline.pull_data import download_data_from_r2
        download_data_from_r2()

    df_stream = pd.read_csv(STREAM_DATA_PATH)
    print(f"Loaded {len(df_stream)} real-time terrain survey records.")

    producer = create_producer()
    records_sent = 0

    try:
        for idx, row in df_stream.iterrows():
            payload = row.to_dict()
            producer.produce(
                topic=TOPIC,
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            records_sent += 1

            if records_sent % 10 == 0:
                producer.flush(timeout=1.0)
                print(f"📡 Sent {records_sent} terrain surveys to topic '{TOPIC}' (Latest Elevation: {payload.get('Elevation')}m)")

            if records_sent >= batch_size:
                print(f"\n✅ Reached requested batch limit of {batch_size} events.")
                break

            time.sleep(delay)

        producer.flush()
        print(f"Producer finished. Total messages produced: {records_sent}")
    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
        producer.flush()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stream Forest Survey Events to Kafka")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of records to stream")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between events in seconds")
    args = parser.parse_args()

    stream_production_events(batch_size=args.batch_size, delay=args.delay)
