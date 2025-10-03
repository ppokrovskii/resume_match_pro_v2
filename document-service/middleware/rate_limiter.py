"""
Rate limiting middleware for FastAPI
Implements per-user/service rate limiting as documented
"""

import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed for the given identifier
        
        Args:
            identifier: User ID, service ID, or IP address
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        async with self._lock:
            current_time = time.time()
            
            # Initialize if first request from this identifier
            if identifier not in self.requests:
                self.requests[identifier] = []
            
            # Remove old requests outside the window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.window_seconds
            ]
            
            # Check if limit exceeded
            current_count = len(self.requests[identifier])
            is_allowed = current_count < self.max_requests
            
            if is_allowed:
                self.requests[identifier].append(current_time)
                current_count += 1
            
            # Calculate reset time
            if self.requests[identifier]:
                oldest_request = min(self.requests[identifier])
                reset_time = int(oldest_request + self.window_seconds)
            else:
                reset_time = int(current_time + self.window_seconds)
            
            rate_limit_info = {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_count),
                "reset": reset_time,
                "window": self.window_seconds
            }
            
            return is_allowed, rate_limit_info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(max_requests, window_seconds)
        logger.info(f"Rate limiter initialized: {max_requests} requests per {window_seconds} seconds")
    
    def get_identifier(self, request: Request) -> str:
        """
        Get identifier for rate limiting
        Priority: user_id > service_id > client_ip
        """
        # Try to get user ID from JWT token (if authenticated)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Try to get service identifier from JWT token
        service_id = getattr(request.state, 'service_id', None)
        if service_id:
            return f"service:{service_id}"
        
        # Fallback to client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if request should skip rate limiting"""
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return True
        
        # Skip for OpenAPI docs
        if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
            return True
        
        return False
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting"""
        
        # Skip rate limiting for certain endpoints
        if self.should_skip_rate_limiting(request):
            return await call_next(request)
        
        # Get identifier for rate limiting
        identifier = self.get_identifier(request)
        
        # Check rate limit
        try:
            is_allowed, rate_info = await self.rate_limiter.is_allowed(identifier)
            
            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {identifier}")
                
                # Return 429 Too Many Requests
                return Response(
                    content='{"success": false, "error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "X-RateLimit-Window": str(rate_info["window"]),
                        "Retry-After": str(rate_info["window"])
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            response.headers["X-RateLimit-Window"] = str(rate_info["window"])
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # If rate limiting fails, allow the request to proceed
            return await call_next(request)

