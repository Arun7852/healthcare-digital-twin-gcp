from google.cloud import pubsub_v1

PROJECT_ID = "digitaltwin-475617"
TOPIC_ID = "ingestion-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

BAD_MESSAGES = [
    b"NOT_JSON_AT_ALL",
    b"{bad json}",
    b'{"patient_id": "p_bad_1", "device_id": ',
]

def publish_bad_message(data: bytes):
    future = publisher.publish(topic_path, data=data)
    print(f"Published bad message ID: {future.result()}")
    print(f"Raw bytes: {data}")
    print("-" * 50)

if __name__ == "__main__":
    print("Running BAD MESSAGE / DLQ demo...")
    for msg in BAD_MESSAGES:
        publish_bad_message(msg)
