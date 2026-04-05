import json
from datetime import datetime, timezone
from google.cloud import pubsub_v1

PROJECT_ID = "digitaltwin-475617"
TOPIC_ID = "ingestion-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

FIXED_EVENT_TIME = datetime.now(timezone.utc).isoformat()

EVENT = {
    "patient_id": "p_dup_1",
    "device_id": "wearable_dup_1",
    "device_type": "wearable",
    "heart_rate": 88,
    "spo2": 96,
    "systolic_bp": 121,
    "diastolic_bp": 77,
    "event_time": FIXED_EVENT_TIME,
}

def publish_event(event: dict):
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    print(f"Published message ID: {future.result()}")
    print(json.dumps(event, indent=2))
    print("-" * 50)

if __name__ == "__main__":
    print("Running DUPLICATE demo...")
    publish_event(EVENT)
    publish_event(EVENT)
