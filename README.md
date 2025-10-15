# Secure, Real-Time Healthcare Digital Twin on Google Cloud

Synthetic vitals stream into Pub/Sub, processed by Cloud Run/Functions calling a Vertex AI endpoint, written to BigQuery, and visualized in Looker Studio or Streamlit — all with least-privilege IAM and CMEK.

## Overview
This project simulates a real-time healthcare monitoring system. Synthetic patient vitals (HR, SpO₂, BP) are published to Pub/Sub, processed by a stateless service, scored by a Vertex AI model (e.g., 3-class: **stable / warning / alert**), and stored in BigQuery for analytics/alerting. A dashboard shows current status and trends.

## Goal
Provide a copy-and-pasteable, HIPAA-aware pattern for secure, real-time AI on Google Cloud (least-privilege IAM, CMEK at rest, clear logging/alerting). Talks (GDG → Regionals → Conf24) will use this repo + a short demo video.

## Stack
- **Messaging:** Pub/Sub  
- **Compute:** Cloud Run or Cloud Functions  
- **ML:** Vertex AI Endpoint (simple classifier)  
- **Storage/Analytics:** BigQuery  
- **Viz:** Looker Studio or Streamlit  
- **Security:** Service Accounts, IAM (least-priv), **CMEK (Cloud KMS)**  
- **Ops:** Cloud Logging, basic alerting
## Architecture (rough)

## Architecture (rough)

```mermaid
flowchart LR
  A[Synthetic Vitals Generator] -->|JSON| B[Pub/Sub Topic]
  B --> C[Subscriber - Cloud Run or Function]
  C -->|features| D[Vertex AI Endpoint]
  C -->|results| E[BigQuery]
  E --> F[Dashboard - Looker or Streamlit]
