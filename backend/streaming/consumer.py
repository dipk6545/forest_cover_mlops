import os
import json
import time
import requests
from kafka import KafkaConsumer, KafkaProducer

# Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "terrain_survey.raw")
TOPIC_PRED = os.getenv("KAFKA_TOPIC_PRED", "terrain_survey.predictions")
API_URL = os.getenv("API_PREDICT_URL", "http://localhost:8000/predict")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "forest-scoring-group")

def connect_consumer():
    """Initializes and returns a KafkaConsumer with retry logic."""
    print(f"Connecting Consumer to {KAFKA_BROKER} on topic '{TOPIC_RAW}'...")
    for attempt in range(1, 11):
        try:
            consumer = KafkaConsumer(
                TOPIC_RAW,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id=GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )
            print("Connected to Kafka Consumer successfully!")
            return consumer
        except Exception as e:
            print(f"Attempt {attempt}/10: Kafka broker not ready yet ({e}). Waiting 3 seconds...")
            time.sleep(3)
    raise RuntimeError("Failed to connect to Kafka consumer.")

def connect_pred_producer():
    """Producer to publish scored predictions to topic: terrain_survey.predictions."""
    try:
        return KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
    except Exception as e:
        print(f"Note: Prediction publisher initialization: {e}")
        return None

def run_consumer():
    """Listens to Kafka raw topic, scores each event via FastAPI, and logs output."""
    consumer = connect_consumer()
    pred_producer = connect_pred_producer()

    print(f"Real-Time ML Consumer Active! Scoring incoming events via {API_URL}...\n")
    processed_count = 0

    try:
        for message in consumer:
            raw_event = message.value
            processed_count += 1

            # Prepare payload for FastAPI /predict
            payload = {
                "Elevation": float(raw_event.get("Elevation", 2500)),
                "Aspect": float(raw_event.get("Aspect", 0)),
                "Slope": float(raw_event.get("Slope", 0)),
                "Horizontal_Distance_To_Hydrology": float(raw_event.get("Horizontal_Distance_To_Hydrology", 0)),
                "Vertical_Distance_To_Hydrology": float(raw_event.get("Vertical_Distance_To_Hydrology", 0)),
                "Horizontal_Distance_To_Roadways": float(raw_event.get("Horizontal_Distance_To_Roadways", 0)),
                "Horizontal_Distance_To_Fire_Points": float(raw_event.get("Horizontal_Distance_To_Fire_Points", 0)),
                "Hillshade_9am": float(raw_event.get("Hillshade_9am", 200)),
                "Hillshade_Noon": float(raw_event.get("Hillshade_Noon", 200)),
                "Hillshade_3pm": float(raw_event.get("Hillshade_3pm", 150)),
                "Wilderness_Area": int(raw_event.get("Wilderness_Area", 1)),
                "Soil_Type": int(raw_event.get("Soil_Type", 29))
            }

            try:
                # Call FastAPI scoring endpoint
                resp = requests.post(API_URL, json=payload, timeout=5)
                if resp.status_code == 200:
                    pred_data = resp.json()
                    tree_species = pred_data.get("tree_species")
                    conf = pred_data.get("confidence")
                    latency = pred_data.get("latency_ms")

                    # Log to console
                    print(f"[CONSUMER <- SCORED #{processed_count}] Species: {tree_species:<16} | Conf: {conf*100:.1f}% | Latency: {latency:.1f}ms")

                    # Publish to predictions topic
                    if pred_producer:
                        output_event = {**raw_event, "prediction": pred_data}
                        pred_producer.send(TOPIC_PRED, value=output_event)
                else:
                    print(f"[ERROR] API returned status {resp.status_code}: {resp.text}")
            except Exception as api_err:
                print(f"[ERROR] Inference call failed: {api_err}")

    except KeyboardInterrupt:
        print("\nConsumer stopped by user.")
    finally:
        consumer.close()
        if pred_producer:
            pred_producer.close()

if __name__ == "__main__":
    run_consumer()
