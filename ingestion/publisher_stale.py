import json
from datetime import datetime, timezone, timedelta
from google.cloud import pubsub_v1

PROJECT_ID = "digitaltwin-475617"
TOPIC_ID = "ingestion-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

PATIENT_ID = "p_fresh_1"

EVENTS = [
    {
        "patient_id": PATIENT_ID,
        "device_id": "wearable_fresh_1",
        "device_type": "wearable",
        "heart_rate": 90,
        "spo2": 96,
        "systolic_bp": 122,
        "diastolic_bp": 78,
        "event_time": (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat(),
    },
    {
        "patient_id": PATIENT_ID,
        "device_id": "bedside_fresh_1",
        "device_type": "bedside_monitor",
        "heart_rate": 84,
        "spo2": 97,
        "systolic_bp": 120,
        "diastolic_bp": 76,
        "event_time": (datetime.now(timezone.utc) - timedelta(seconds=25)).isoformat(),
    },
    {
        "patient_id": PATIENT_ID,
        "device_id": "spo2_probe_fresh_1",
        "device_type": "pulse_oximeter",
        "heart_rate": 86,
        "spo2": 95,
        "systolic_bp": 121,
        "diastolic_bp": 77,
        "event_time": (datetime.now(timezone.utc) - timedelta(seconds=75)).isoformat(),
    },
]

def publish_event(event: dict):
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    print(f"Published message ID: {future.result()}")
    print(json.dumps(event, indent=2))
    print("-" * 50)

if __name__ == "__main__":
    print("Running STALE/FRESHNESS demo...")
    for event in EVENTS:
        publish_event(event)
