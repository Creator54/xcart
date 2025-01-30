#! /bin/bash

export OTEL_RESOURCE_ATTRIBUTES=service.name=Xcart
export OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.in.signoz.cloud:443"
export OTEL_EXPORTER_OTLP_HEADERS="signoz-ingestion-key=PzvfUmn6V6ZRh1XbJRYRC7NL-zlpxi-KQpGP"

uvicorn app.main:app --reload --port 8000