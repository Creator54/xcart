import os
import time
from app.core.logging import setup_logging
from app.core.telemetry import (
    setup_telemetry,
    track_request,
    track_cart_items,
    track_order_total,
    track_user_activity
)

def main():
    # Setup logging
    setup_logging()
    
    # Setup OpenTelemetry
    setup_telemetry()
    
    print("\nStarting metrics test...")
    print("Will send metrics every 5 seconds for 30 seconds...")
    
    start_time = time.time()
    iteration = 1
    
    while time.time() - start_time < 30:
        print(f"\nIteration {iteration}:")
        
        # Test HTTP metrics
        print("- Sending HTTP metrics...")
        track_request("GET", "/test")
        track_request("POST", "/test")
        
        # Test business metrics
        print("- Sending business metrics...")
        track_cart_items(1, 5)  # Add 5 items to cart
        track_order_total(1, 99.99)  # Track order amount
        track_user_activity(1, True)  # Track user login
        
        print("- Waiting 5 seconds for next batch...")
        time.sleep(5)
        iteration += 1
    
    print("\nTest completed!")
    print("If metrics were exported successfully, you should see 'Metrics exported successfully!' messages above.")
    print("Check your SigNoz dashboard for the following metrics:")
    print("- http_requests_total")
    print("- cart_items_total")
    print("- order_total_amount")
    print("- active_users")

if __name__ == "__main__":
    # Set test environment variables if not set
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        print("Error: OTEL_EXPORTER_OTLP_ENDPOINT not set!")
        print("Example: export OTEL_EXPORTER_OTLP_ENDPOINT='https://ingest.{region}.signoz.cloud:443'")
        exit(1)
    
    if not os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
        print("Error: OTEL_EXPORTER_OTLP_HEADERS not set!")
        print("Example: export OTEL_EXPORTER_OTLP_HEADERS='signoz-access-token={your-token}'")
        exit(1)
    
    print("\nCurrent OpenTelemetry Configuration:")
    print(f"Endpoint: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}")
    print(f"Headers: {os.getenv('OTEL_EXPORTER_OTLP_HEADERS')}")
    input("\nPress Enter to start the test...")
    
    main() 