flowchart LR
    A[Synthetic Vitals Generator] -->|JSON| B(Pub/Sub Topic)
    B --> C[Subscriber (Cloud Run/Function)]
    C -->|features| D[Vertex AI Endpoint]
    C -->|results| E[BigQuery]
    E --> F[Dashboard (Looker/Streamlit)]