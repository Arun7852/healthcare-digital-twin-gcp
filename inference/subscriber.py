import os
import base64
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import Flask, request, jsonify
from google.cloud import bigquery

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PROJECT_ID = "digitaltwin-475617"
TABLE_ID = f"{PROJECT_ID}.bronze_raw.events_ingest"

bq_client = bigquery.Client()

# =========================
# Configurable rule section
# =========================

# Metric-specific trust by device type
METRIC_CONFIDENCE = {
    "bedside_monitor": {
        "heart_rate": 0.95,
        "spo2": 0.70,
        "blood_pressure": 0.95,
    },
    "pulse_oximeter": {
        "heart_rate": 0.60,
        "spo2": 0.95,
        "blood_pressure": 0.20,
    },
    "wearable": {
        "heart_rate": 0.70,
        "spo2": 0.50,
        "blood_pressure": 0.35,
    },
}

FRESHNESS_RULES = {
    "fresh_seconds": 15,
    "stale_seconds": 60,
}

STATUS_THRESHOLDS = {
    "spo2_alert": 90,
    "spo2_warning": 94,
    "hr_alert": 125,
    "hr_warning": 110,
    "sys_bp_alert": 155,
    "sys_bp_warning": 140,
}


def make_trace_id() -> str:
    return str(uuid.uuid4())


def make_dedup_key(event: dict) -> str:
    patient_id = event.get("patient_id", "unknown")
    device_id = event.get("device_id", "unknown")
    event_time = event.get("event_time", "unknown")
    return f"{patient_id}:{device_id}:{event_time}"


def classify_status(event: dict) -> Tuple[str, str]:
    hr = event.get("heart_rate", 0)
    spo2 = event.get("spo2", 100)
    sys_bp = event.get("systolic_bp", 0)

    if spo2 < STATUS_THRESHOLDS["spo2_alert"]:
        return "alert", f"SpO2 below alert threshold ({spo2} < {STATUS_THRESHOLDS['spo2_alert']})"
    if hr > STATUS_THRESHOLDS["hr_alert"]:
        return "alert", f"Heart rate above alert threshold ({hr} > {STATUS_THRESHOLDS['hr_alert']})"
    if sys_bp > STATUS_THRESHOLDS["sys_bp_alert"]:
        return "alert", f"Systolic BP above alert threshold ({sys_bp} > {STATUS_THRESHOLDS['sys_bp_alert']})"

    if spo2 < STATUS_THRESHOLDS["spo2_warning"]:
        return "warning", f"SpO2 below warning threshold ({spo2} < {STATUS_THRESHOLDS['spo2_warning']})"
    if hr > STATUS_THRESHOLDS["hr_warning"]:
        return "warning", f"Heart rate above warning threshold ({hr} > {STATUS_THRESHOLDS['hr_warning']})"
    if sys_bp > STATUS_THRESHOLDS["sys_bp_warning"]:
        return "warning", f"Systolic BP above warning threshold ({sys_bp} > {STATUS_THRESHOLDS['sys_bp_warning']})"

    return "stable", "All monitored values within configured thresholds"


def compute_freshness(event_time_str: Optional[str], ingest_dt: datetime) -> Tuple[Optional[int], str, str]:
    if not event_time_str:
        return None, "unknown", "No event_time present"

    try:
        event_dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
        age_seconds = int((ingest_dt - event_dt).total_seconds())

        if age_seconds <= FRESHNESS_RULES["fresh_seconds"]:
            return age_seconds, "fresh", f"Event age {age_seconds}s <= {FRESHNESS_RULES['fresh_seconds']}s"
        if age_seconds <= FRESHNESS_RULES["stale_seconds"]:
            return age_seconds, "aging", f"Event age {age_seconds}s between fresh and stale thresholds"
        return age_seconds, "stale", f"Event age {age_seconds}s > {FRESHNESS_RULES['stale_seconds']}s"
    except Exception:
        return None, "unknown", "Failed to parse event_time"


def compute_metric_confidences(device_type: str) -> dict:
    metric_map = METRIC_CONFIDENCE.get(device_type, {
        "heart_rate": 0.50,
        "spo2": 0.50,
        "blood_pressure": 0.50,
    })

    return {
        "hr_confidence": metric_map["heart_rate"],
        "hr_confidence_reason": f"Configured HR trust for device_type={device_type}",
        "spo2_confidence": metric_map["spo2"],
        "spo2_confidence_reason": f"Configured SpO2 trust for device_type={device_type}",
        "bp_confidence": metric_map["blood_pressure"],
        "bp_confidence_reason": f"Configured BP trust for device_type={device_type}",
    }


def enrich_event(raw_event: dict) -> dict:
    ingest_dt = datetime.now(timezone.utc)

    freshness_seconds, freshness_state, freshness_reason = compute_freshness(
        raw_event.get("event_time"),
        ingest_dt,
    )

    status, status_reason = classify_status(raw_event)
    metric_confidence = compute_metric_confidences(raw_event.get("device_type", "unknown"))

    enriched = {
        **raw_event,
        **metric_confidence,
        "freshness_seconds": freshness_seconds,
        "freshness_state": freshness_state,
        "freshness_reason": freshness_reason,
        "status": status,
        "status_reason": status_reason,
    }

    return enriched


def build_bronze_row(enriched_event: dict, trace_id: str, dedup_key: str, ingest_dt: datetime) -> dict:
    return {
        "ingest_ts": ingest_dt.isoformat(),
        "tenant": "demo_hospital",
        "event_type": "synthetic_vitals",
        "trace_id": trace_id,
        "dedup_key": dedup_key,
        "event_time": enriched_event.get("event_time"),
        "payload": json.dumps(enriched_event),
    }


@app.route("/", methods=["POST"])
def receive_pubsub():
    try:
        envelope = request.get_json(silent=True)
        logging.info("Received envelope: %s", envelope)

        if not envelope or "message" not in envelope:
            return jsonify({"error": "Invalid Pub/Sub push format"}), 400

        message = envelope["message"]
        encoded_data = message.get("data")

        if not encoded_data:
            return jsonify({"error": "No data field in Pub/Sub message"}), 400

        decoded_data = base64.b64decode(encoded_data).decode("utf-8")
        raw_event = json.loads(decoded_data)

        logging.info("Decoded raw event: %s", raw_event)

        trace_id = make_trace_id()
        dedup_key = make_dedup_key(raw_event)
        ingest_dt = datetime.now(timezone.utc)

        enriched_event = enrich_event(raw_event)
        row = build_bronze_row(enriched_event, trace_id, dedup_key, ingest_dt)

        logging.info("Bronze row: %s", row)

        errors = bq_client.insert_rows_json(TABLE_ID, [row])

        if errors:
            logging.error("BigQuery insert errors: %s", errors)
            return jsonify({"error": errors}), 500

        return jsonify({
            "message": "Processed successfully",
            "trace_id": trace_id,
            "dedup_key": dedup_key,
            "enriched_event": enriched_event,
        }), 200

    except Exception as e:
        logging.exception("Unhandled error in subscriber")
        return jsonify({"error": str(e)}), 500


@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
