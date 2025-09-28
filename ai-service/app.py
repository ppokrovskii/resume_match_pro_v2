"""
AI Service - Flask application entry point
Handles embeddings generation and semantic matching
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from routes.embeddings import embeddings_bp
from routes.matching import matching_bp
from routes.search import search_bp
from routes.health import health_bp
from utils.error_handler import register_error_handlers
from utils.database import init_db

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/resumematch')
    app.config['AZURE_OPENAI_ENDPOINT'] = os.getenv('AZURE_OPENAI_ENDPOINT')
    app.config['AZURE_OPENAI_API_KEY'] = os.getenv('AZURE_OPENAI_API_KEY')
    app.config['AZURE_OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
    app.config['EMBEDDING_MODEL'] = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # CORS configuration
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    
    # Initialize OpenTelemetry tracing
    if os.getenv('JAEGER_ENDPOINT'):
        setup_tracing(app)
    
    # Initialize database
    init_db(app.config['DATABASE_URL'])
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(embeddings_bp, url_prefix='/api/v1/embeddings')
    app.register_blueprint(matching_bp, url_prefix='/api/v1/matching')
    app.register_blueprint(search_bp, url_prefix='/api/v1/search')
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def setup_tracing(app):
    """Setup OpenTelemetry distributed tracing"""
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv('JAEGER_HOST', 'localhost'),
        agent_port=int(os.getenv('JAEGER_PORT', 14268))
    )
    
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Auto-instrument Flask and requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)






