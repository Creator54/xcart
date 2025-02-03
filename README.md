# XCart API

A FastAPI-based e-commerce REST API with OpenTelemetry instrumentation for real-time monitoring via SigNoz.

## Features

- RESTful API endpoints for e-commerce operations
- SQLite database with auto-initialization and sample data
- JWT-based authentication
- Real-time monitoring with OpenTelemetry metrics
- Interactive API documentation (Swagger UI)

## Setup

### Prerequisites
- Python 3.12
- SigNoz account (cloud or self-hosted)

### Installation
```bash
# Clone and setup
git clone https://github.com/creator54/xcart.git
cd xcart
pip install -r requirements.txt

# Configure SigNoz monitoring
# For Cloud:
export OTEL_RESOURCE_ATTRIBUTES="service.name=xcart-v1"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.{region}.signoz.cloud:443"
export OTEL_EXPORTER_OTLP_HEADERS="signoz-access-token={your-token}"

# For Self-Hosted:
export OTEL_RESOURCE_ATTRIBUTES="service.name=xcart-v1"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Start server
bash start.sh  # or: uvicorn app.main:app
```

### Run with Docker
```bash
# Build Docker image
docker build -t xcart .

# Run container
docker run -e OTEL_EXPORTER_OTLP_ENDPOINT="https://ingest.{region}.signoz.cloud:443" \
-e OTEL_EXPORTER_OTLP_HEADERS="signoz-access-token={your-token}" \
-e OTEL_RESOURCE_ATTRIBUTES="service.name=xcart_v1" \
-p 8000:8000 \
xcart
```

Access API documentation at: http://localhost:8000/docs

## API Endpoints

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token

### Products
- `GET /products` - List products
- `GET /products/{id}` - Product details

### Cart 🔒
- `GET /cart` - View cart
- `POST /cart/add` - Add item
- `DELETE /cart/{id}` - Remove item

### Orders 🔒
- `POST /orders` - Place order
- `GET /orders` - Order history

_🔒 Requires Authentication: Include JWT token in Authorization header (`Bearer <token>`)_

## Monitoring

XCart exposes three main metrics via OpenTelemetry:

### 1. Request Latency
```promql
# 95th percentile latency
histogram_quantile(0.95, sum(rate(xcart_v1_http_request_duration_seconds_bucket[1m])) by (le))
```

### 2. Error Count
```promql
# Total errors
sum(xcart_v1_http_errors_total)
```

### 3. Cart Items
```promql
# Items in cart per user
max(xcart_v1_cart_items_total{user_id="1"})
```

### Dashboard
Import `signoz_dashboard.json` in SigNoz to get:
- Latency analysis (p95, p75, p50)
- Error tracking
- Cart statistics

![Dashboard Preview](https://hackmd.io/_uploads/H1iApshOyx.png)

## Troubleshooting

### No Metrics?
1. Verify environment variables
2. Check SigNoz connectivity
3. Validate access token (cloud)

## License
MIT
