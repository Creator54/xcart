#! /bin/bash

export OTEL_RESOURCE_ATTRIBUTES=service.name=xcart-v1
export OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.in.signoz.cloud:443"
export OTEL_EXPORTER_OTLP_HEADERS="<your-signoz-ingestion-key>"

uvicorn app.main:app --reload --port 8000