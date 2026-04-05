import json
from datetime import datetime, timezone
from google.cloud import pubsub_v1

PROJECT_ID = "digitaltwin-475617"
TOPIC_ID = "ingestion-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

EVENTS = [
    {
        "patient_id": "p_norm_1",
        "device_id": "wearable_norm_1",
        "device_type": "wearable",
        "heart_rate": 88,
        "spo2": 96,
        "systolic_bp": 121,
        "diastolic_bp": 77,
    },
    {
        "patient_id": "p_norm_2",
        "device_id": "spo2_probe_norm_1",
        "device_type": "pulse_oximeter",
        "heart_rate": 95,
        "spo2": 92,
        "systolic_bp": 136,
        "diastolic_bp": 85,
    },
    {
        "patient_id": "p_norm_3",
        "device_id": "bedside_norm_1",
        "device_type": "bedside_monitor",
        "heart_rate": 76,
        "spo2": 99,
        "systolic_bp": 116,
        "diastolic_bp": 74,
    },
]

def publish_event(event: dict):
    event["event_time"] = datetime.now(timezone.utc).isoformat()
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    print(f"Published message ID: {future.result()}")
    print(json.dumps(event, indent=2))
    print("-" * 50)

if __name__ == "__main__":
    print("Running NORMAL demo...")
    for event in EVENTS:
        publish_event(event)
