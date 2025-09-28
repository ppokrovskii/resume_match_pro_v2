"""
Document Service - FastAPI Application
Pure document storage and management microservice
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from routers.documents import router as documents_router
from routers.health import router as health_router
from routers.auth import router as auth_router
from utils.fastapi_error_handler import register_exception_handlers
from middleware.rate_limiter import RateLimitMiddleware
from utils.database import init_db
from utils.swagger_auth import configure_swagger_auth, get_swagger_ui_init_oauth
from middleware.auth0_middleware import Auth0Middleware

# Load environment variables from .env file
load_dotenv()


def setup_tracing():
    """Set up OpenTelemetry tracing"""
    jaeger_endpoint = os.getenv('JAEGER_ENDPOINT')
    if not jaeger_endpoint:
        return
    
    try:
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer_provider()
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            endpoint=jaeger_endpoint,
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer.add_span_processor(span_processor)
        
        print(f"Tracing configured with Jaeger endpoint: {jaeger_endpoint}")
        
    except Exception as e:
        print(f"WARNING: Failed to configure tracing: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting Document Service...")
    
    # Set up tracing
    setup_tracing()
    
    # Initialize database
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        init_db(database_url)
        print("Database initialized")
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        raise
    
    # Instrument FastAPI and requests
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    
    print("Document Service started successfully")
    
    yield
    
    # Shutdown
    print("Shutting down Document Service...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Document Service API",
        description="Pure document storage and management microservice",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        swagger_ui_init_oauth=get_swagger_ui_init_oauth()
    )
    
    # Configure Swagger UI with Auth0 integration
    configure_swagger_auth(app)
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Auth0 middleware
    app.add_middleware(Auth0Middleware)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Add rate limiting middleware (100 requests per minute as documented)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    
    # Include routers
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    
    return app


# Create the app instance
app = create_app()




if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
        log_level="info"
    )