from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from .metrics import get_metrics
from .logging import get_logger

logger = get_logger("middleware")

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time()
        
        try:
            response = await call_next(request)
            duration_ms = (time() - start_time) * 1000
            
            # Track request metrics
            metrics = get_metrics()
            metrics.track_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in metrics middleware: {str(e)}")
            raise 