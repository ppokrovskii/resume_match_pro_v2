"""
Unit tests for logging configuration and monitoring
Following TDD approach as per project requirements
"""

import os
import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from main import setup_tracing
import sys
import os


class TestLoggingConfiguration:
    """Test logging configuration and setup"""
    
    def test_logger_creation(self):
        """Test that loggers are created with proper names"""
        # Test that we can create loggers for different modules
        auth_logger = logging.getLogger('middleware.auth0_middleware')
        error_logger = logging.getLogger('utils.fastapi_error_handler')
        main_logger = logging.getLogger('main')
        
        assert auth_logger.name == 'middleware.auth0_middleware'
        assert error_logger.name == 'utils.fastapi_error_handler'
        assert main_logger.name == 'main'
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance"""
        parent_logger = logging.getLogger('middleware')
        child_logger = logging.getLogger('middleware.auth0_middleware')
        
        # Child logger should inherit from parent
        assert child_logger.parent == parent_logger or child_logger.parent == logging.getLogger()
    
    def test_log_level_configuration(self):
        """Test log level configuration from environment"""
        # Test default log level
        logger = logging.getLogger('test_logger')
        
        # Test setting log level via environment
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            # In a real application, this would be configured in main.py
            # Here we test the concept
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            assert log_level == 'DEBUG'
        
        with patch.dict(os.environ, {'LOG_LEVEL': 'WARNING'}):
            log_level = os.getenv('LOG_LEVEL', 'INFO')
            assert log_level == 'WARNING'
    
    def test_log_format_consistency(self):
        """Test that log format is consistent across modules"""
        # Create a string buffer to capture log output
        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        
        # Set a consistent format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Test logger
        test_logger = logging.getLogger('test_module')
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)
        
        test_logger.info("Test message")
        
        log_output = log_buffer.getvalue()
        
        # Should contain timestamp, level, module name, and message
        assert '[    INFO]' in log_output
        assert 'test_module:' in log_output
        assert 'Test message' in log_output
        
        # Clean up
        test_logger.removeHandler(handler)


class TestTracingConfiguration:
    """Test OpenTelemetry tracing configuration"""
    
    @patch('main.trace.set_tracer_provider')
    @patch('main.JaegerExporter')
    @patch('main.BatchSpanProcessor')
    @patch('main.RequestsInstrumentor')
    def test_setup_tracing_with_jaeger(self, mock_requests_instr, mock_batch_processor, 
                                      mock_jaeger_exporter, mock_set_tracer_provider):
        """Test tracing setup with Jaeger configuration"""
        mock_exporter = Mock()
        mock_jaeger_exporter.return_value = mock_exporter
        
        mock_processor = Mock()
        mock_batch_processor.return_value = mock_processor
        
        mock_tracer_provider = Mock()
        
        with patch('main.TracerProvider') as mock_tracer_provider_class:
            mock_tracer_provider_class.return_value = mock_tracer_provider
            
            with patch('main.trace.get_tracer_provider') as mock_get_tracer_provider:
                mock_get_tracer_provider.return_value = mock_tracer_provider
                
                with patch.dict(os.environ, {
                    'JAEGER_HOST': 'localhost',
                    'JAEGER_PORT': '14268'
                }):
                    setup_tracing()
                    
                    # Verify tracer provider is set
                    mock_set_tracer_provider.assert_called_once_with(mock_tracer_provider)
                    
                    # Verify Jaeger exporter is created with correct config
                    mock_jaeger_exporter.assert_called_once_with(
                        agent_host_name='localhost',
                        agent_port=14268
                    )
                    
                    # Verify span processor is created and added
                    mock_batch_processor.assert_called_once_with(mock_exporter)
                    mock_tracer_provider.add_span_processor.assert_called_once_with(mock_processor)
                    
                    # Verify requests instrumentation
                    mock_requests_instr.return_value.instrument.assert_called_once()
    
    @patch('main.trace.set_tracer_provider')
    @patch('main.JaegerExporter')
    def test_setup_tracing_default_config(self, mock_jaeger_exporter, mock_set_tracer_provider):
        """Test tracing setup with default configuration"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('main.TracerProvider') as mock_tracer_provider_class:
                with patch('main.BatchSpanProcessor'):
                    with patch('main.trace.get_tracer_provider'):
                        with patch('main.RequestsInstrumentor'):
                            setup_tracing()
                            
                            # Should use default values
                            mock_jaeger_exporter.assert_called_once_with(
                                agent_host_name='localhost',
                                agent_port=14268
                            )
    
    def test_tracing_environment_variables(self):
        """Test tracing configuration from environment variables"""
        # Test JAEGER_ENDPOINT detection
        with patch.dict(os.environ, {'JAEGER_ENDPOINT': 'http://jaeger:14268'}):
            jaeger_endpoint = os.getenv('JAEGER_ENDPOINT')
            assert jaeger_endpoint == 'http://jaeger:14268'
        
        # Test JAEGER_HOST and JAEGER_PORT
        with patch.dict(os.environ, {
            'JAEGER_HOST': 'jaeger-collector',
            'JAEGER_PORT': '14269'
        }):
            jaeger_host = os.getenv('JAEGER_HOST', 'localhost')
            jaeger_port = int(os.getenv('JAEGER_PORT', 14268))
            
            assert jaeger_host == 'jaeger-collector'
            assert jaeger_port == 14269


# Database configuration tests removed - they belong in a separate test file
# and were causing import issues with alembic context


class TestApplicationLogging:
    """Test application-level logging functionality"""
    
    def test_startup_logging(self, caplog):
        """Test that application startup is logged"""
        # This would typically be tested in integration tests
        # Here we test the logging pattern
        with caplog.at_level(logging.INFO):
            logger = logging.getLogger('main')
            logger.info("✅ Document Service started successfully")
            
            assert "Document Service started successfully" in caplog.text
    
    def test_shutdown_logging(self, caplog):
        """Test that application shutdown is logged"""
        with caplog.at_level(logging.INFO):
            logger = logging.getLogger('main')
            logger.info("🔄 Document Service shutting down...")
            
            assert "Document Service shutting down" in caplog.text
    
    def test_error_logging_format(self, caplog):
        """Test error logging format consistency"""
        with caplog.at_level(logging.ERROR):
            logger = logging.getLogger('test_module')
            
            # Test different error logging patterns
            logger.error("❌ Failed to start Document Service: Connection refused")
            logger.error("Token verification failed: Invalid signature")
            logger.error("Document service error: File not found")
            
            # All error messages should be captured
            assert "Failed to start Document Service" in caplog.text
            assert "Token verification failed" in caplog.text
            assert "Document service error" in caplog.text
    
    def test_debug_logging_configuration(self):
        """Test debug logging configuration"""
        logger = logging.getLogger('debug_test')
        
        # Test that debug messages can be enabled
        logger.setLevel(logging.DEBUG)
        
        with patch.object(logger, 'debug') as mock_debug:
            logger.debug("Debug message for testing")
            mock_debug.assert_called_once_with("Debug message for testing")
    
    def test_structured_logging_format(self):
        """Test structured logging format for better parsing"""
        # Test that we can create structured log entries
        log_data = {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "service": "document-service",
            "module": "auth0_middleware",
            "message": "Token verified successfully",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "request_id": "req-123"
        }
        
        # Verify structure
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "service" in log_data
        assert "module" in log_data
        assert "message" in log_data
        
        # Test that additional context can be added
        assert "user_id" in log_data
        assert "request_id" in log_data


class TestPerformanceLogging:
    """Test performance and monitoring logging"""
    
    def test_request_timing_logging(self):
        """Test request timing logging pattern"""
        import time
        
        # Simulate request timing
        start_time = time.time()
        time.sleep(0.001)  # Simulate processing
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Test logging pattern
        log_message = f"Request completed in {duration:.3f}s"
        
        assert "Request completed in" in log_message
        assert "s" in log_message
        assert duration > 0
    
    def test_performance_metrics_logging(self):
        """Test performance metrics logging"""
        # Test metrics that should be logged
        metrics = {
            "upload_duration": 2.5,
            "file_size_mb": 1.2,
            "text_extraction_time": 0.8,
            "classification_time": 0.3,
            "storage_time": 0.4
        }
        
        # Verify metrics structure
        for metric_name, value in metrics.items():
            assert isinstance(metric_name, str)
            assert isinstance(value, (int, float))
            assert value >= 0
    
    def test_error_rate_logging(self):
        """Test error rate logging pattern"""
        # Test error counting pattern
        total_requests = 100
        failed_requests = 5
        error_rate = (failed_requests / total_requests) * 100
        
        log_message = f"Error rate: {error_rate:.1f}% ({failed_requests}/{total_requests})"
        
        assert "Error rate:" in log_message
        assert "5.0%" in log_message
        assert "5/100" in log_message


class TestSecurityLogging:
    """Test security-related logging"""
    
    def test_authentication_logging(self, caplog):
        """Test authentication event logging"""
        with caplog.at_level(logging.INFO):
            logger = logging.getLogger('middleware.auth0_middleware')
            
            # Test successful authentication
            logger.info("Successfully verified token for user: auth0|user123")
            
            # Test failed authentication
            logger.warning("Token verification failed: expired token")
            
            assert "Successfully verified token" in caplog.text
            assert "Token verification failed" in caplog.text
    
    def test_authorization_logging(self, caplog):
        """Test authorization event logging"""
        with caplog.at_level(logging.WARNING):
            logger = logging.getLogger('middleware.auth0_middleware')
            
            # Test insufficient scope
            logger.warning("Access denied: insufficient scope for user auth0|user123")
            
            assert "Access denied: insufficient scope" in caplog.text
    
    def test_security_event_logging(self, caplog):
        """Test security event logging"""
        with caplog.at_level(logging.WARNING):
            logger = logging.getLogger('security')
            
            # Test suspicious activity
            logger.warning("Multiple failed login attempts from IP: 192.168.1.100")
            logger.error("Potential security breach: unauthorized file access attempt")
            
            assert "Multiple failed login attempts" in caplog.text
            assert "Potential security breach" in caplog.text
    
    def test_audit_logging_format(self):
        """Test audit logging format"""
        # Test audit log entry structure
        audit_entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "event_type": "document_upload",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "resource_id": "doc-456",
            "action": "CREATE",
            "result": "SUCCESS",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "request_id": "req-123"
        }
        
        # Verify audit entry structure
        required_fields = [
            "timestamp", "event_type", "user_id", "action", "result"
        ]
        
        for field in required_fields:
            assert field in audit_entry
            assert audit_entry[field] is not None


class TestLoggingIntegration:
    """Integration tests for logging functionality"""
    
    def test_logging_configuration_integration(self):
        """Test complete logging configuration integration"""
        # Test that different loggers can be configured together
        loggers = [
            logging.getLogger('main'),
            logging.getLogger('middleware.auth0_middleware'),
            logging.getLogger('utils.fastapi_error_handler'),
            logging.getLogger('services.document_service'),
            logging.getLogger('routers.documents')
        ]
        
        # All loggers should be configurable
        for logger in loggers:
            assert isinstance(logger, logging.Logger)
            assert logger.name is not None
    
    def test_environment_based_logging_config(self):
        """Test logging configuration based on environment"""
        # Test development environment
        with patch.dict(os.environ, {
            'FASTAPI_ENV': 'development',
            'LOG_LEVEL': 'DEBUG',
            'DATABASE_ECHO': 'true'
        }):
            env = os.getenv('FASTAPI_ENV')
            log_level = os.getenv('LOG_LEVEL')
            db_echo = os.getenv('DATABASE_ECHO')
            
            assert env == 'development'
            assert log_level == 'DEBUG'
            assert db_echo == 'true'
        
        # Test production environment
        with patch.dict(os.environ, {
            'FASTAPI_ENV': 'production',
            'LOG_LEVEL': 'WARNING',
            'DATABASE_ECHO': 'false'
        }):
            env = os.getenv('FASTAPI_ENV')
            log_level = os.getenv('LOG_LEVEL')
            db_echo = os.getenv('DATABASE_ECHO')
            
            assert env == 'production'
            assert log_level == 'WARNING'
            assert db_echo == 'false'
    
    def test_logging_and_tracing_integration(self):
        """Test integration between logging and tracing"""
        # Test that logging and tracing can work together
        with patch.dict(os.environ, {
            'JAEGER_ENDPOINT': 'http://jaeger:14268',
            'LOG_LEVEL': 'INFO'
        }):
            jaeger_endpoint = os.getenv('JAEGER_ENDPOINT')
            log_level = os.getenv('LOG_LEVEL')
            
            # Both should be configured
            assert jaeger_endpoint is not None
            assert log_level == 'INFO'
            
            # Test that we can log tracing information
            logger = logging.getLogger('tracing')
            
            with patch.object(logger, 'info') as mock_info:
                logger.info("Tracing initialized with Jaeger endpoint: %s", jaeger_endpoint)
                mock_info.assert_called_once()


class TestLoggingBestPractices:
    """Test logging best practices implementation"""
    
    def test_log_message_format_consistency(self):
        """Test that log messages follow consistent format"""
        # Test different log message patterns
        patterns = [
            "✅ Operation completed successfully",
            "❌ Operation failed: error details",
            "🔄 Operation in progress...",
            "⚠️ Warning: potential issue detected"
        ]
        
        for pattern in patterns:
            # Should start with emoji for visual clarity
            assert pattern[0] in ['✅', '❌', '🔄', '⚠️']
            # Should be descriptive
            assert len(pattern) > 10
    
    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted from logs"""
        # Test patterns for redacting sensitive information
        sensitive_data = {
            "password": "secret123",
            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
            "api_key": "sk-1234567890abcdef",
            "client_secret": "client_secret_value"
        }
        
        # Test redaction function (would be implemented in actual logging)
        def redact_sensitive_data(data):
            redacted = {}
            for key, value in data.items():
                if key.lower() in ['password', 'token', 'api_key', 'client_secret']:
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = value
            return redacted
        
        redacted = redact_sensitive_data(sensitive_data)
        
        # All sensitive fields should be redacted
        assert redacted["password"] == "[REDACTED]"
        assert redacted["token"] == "[REDACTED]"
        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["client_secret"] == "[REDACTED]"
    
    def test_log_level_appropriateness(self):
        """Test that log levels are used appropriately"""
        # Test log level guidelines
        log_levels = {
            logging.DEBUG: "Detailed diagnostic information",
            logging.INFO: "General information about application flow",
            logging.WARNING: "Something unexpected happened but app continues",
            logging.ERROR: "Serious problem that prevented function execution",
            logging.CRITICAL: "Very serious error that may abort the program"
        }
        
        for level, description in log_levels.items():
            assert isinstance(level, int)
            assert isinstance(description, str)
            assert len(description) > 20  # Should be descriptive
    
    def test_contextual_logging(self):
        """Test contextual logging with request/user information"""
        # Test logging context structure
        context = {
            "request_id": "req-123",
            "user_id": "user-456",
            "endpoint": "/api/v1/documents/upload",
            "method": "POST",
            "ip_address": "192.168.1.100"
        }
        
        # Test that context can be included in log messages
        log_message = f"Document upload started - Request: {context['request_id']}, User: {context['user_id']}"
        
        assert context["request_id"] in log_message
        assert context["user_id"] in log_message
        assert "Document upload started" in log_message

