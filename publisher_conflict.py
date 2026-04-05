import json
from datetime import datetime, timezone, timedelta
from google.cloud import pubsub_v1

PROJECT_ID = "digitaltwin-475617"
TOPIC_ID = "ingestion-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

PATIENT_ID = "p_conflict_1"
now = datetime.now(timezone.utc)

EVENTS = [
    # Bedside monitor: more trusted for HR/BP, but slightly older
    {
        "patient_id": PATIENT_ID,
        "device_id": "bedside_conflict_1",
        "device_type": "bedside_monitor",
        "heart_rate": 78,
        "spo2": 97,
        "systolic_bp": 118,
        "diastolic_bp": 75,
        "event_time": (now - timedelta(seconds=18)).isoformat(),
    },

    # Wearable: slightly less trusted for HR, but much fresher
    # This should win HR if freshness is prioritized strongly
    {
        "patient_id": PATIENT_ID,
        "device_id": "wearable_conflict_1",
        "device_type": "wearable",
        "heart_rate": 112,
        "spo2": 95,
        "systolic_bp": 132,
        "diastolic_bp": 82,
        "event_time": (now - timedelta(seconds=2)).isoformat(),
    },

    # Pulse oximeter: best source for SpO2, also fresh
    {
        "patient_id": PATIENT_ID,
        "device_id": "spo2_probe_conflict_1",
        "device_type": "pulse_oximeter",
        "heart_rate": 84,
        "spo2": 91,
        "systolic_bp": 125,
        "diastolic_bp": 79,
        "event_time": now.isoformat(),
    },
]


def publish_event(event: dict):
    data = json.dumps(event).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    print(f"Published message ID: {future.result()}")
    print(json.dumps(event, indent=2))
    print("-" * 50)


if __name__ == "__main__":
    print("Running CONFLICT + FRESHNESS demo...")
    for event in EVENTS:
        publish_event(event)
