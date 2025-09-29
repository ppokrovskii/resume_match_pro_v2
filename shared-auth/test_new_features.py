#!/usr/bin/env python3
"""
Test script for new startup validation and OpenTelemetry features.
"""

import os
import sys
sys.path.insert(0, 'src')

from shared_auth import validate_auth0_config, Auth0Middleware
from shared_auth.exceptions import ConfigurationError

def test_startup_validation():
    """Test startup configuration validation."""
    print("[TEST] Testing startup validation...")
    
    # Clear environment
    for key in ["AUTH0_DOMAIN", "AUTH0_API_IDENTIFIER"]:
        if key in os.environ:
            del os.environ[key]
    
    # Test 1: Missing configuration should fail
    try:
        validate_auth0_config()
        print("[FAIL] Should have failed with missing config")
        return False
    except ConfigurationError as e:
        print(f"[PASS] Correctly failed with missing config: {e}")
    
    # Test 2: Invalid domain format should fail
    try:
        validate_auth0_config(domain="invalid-domain", api_identifier="https://api.test.com")
        print("[FAIL] Should have failed with invalid domain")
        return False
    except ConfigurationError as e:
        print(f"[PASS] Correctly failed with invalid domain: {e}")
    
    # Test 3: Invalid API identifier should fail
    try:
        validate_auth0_config(domain="test.auth0.com", api_identifier="not-a-url")
        print("[FAIL] Should have failed with invalid API identifier")
        return False
    except ConfigurationError as e:
        print(f"[PASS] Correctly failed with invalid API identifier: {e}")
    
    # Test 4: Valid configuration should pass
    try:
        config = validate_auth0_config(
            domain="test.auth0.com",
            api_identifier="https://api.test.com"
        )
        print(f"[PASS] Valid configuration passed: {config}")
        return True
    except Exception as e:
        print(f"[FAIL] Valid configuration failed: {e}")
        return False

def test_opentelemetry_integration():
    """Test OpenTelemetry integration."""
    print("\n[TEST] Testing OpenTelemetry integration...")
    
    # Set valid environment
    os.environ["AUTH0_DOMAIN"] = "test.auth0.com"
    os.environ["AUTH0_API_IDENTIFIER"] = "https://api.test.com"
    
    try:
        # Initialize middleware (should work with or without OpenTelemetry)
        middleware = Auth0Middleware()
        print("[PASS] Middleware initialized with tracing support")
        
        # Check if tracing is available
        from shared_auth.middleware import TRACING_ENABLED
        if TRACING_ENABLED:
            print("[PASS] OpenTelemetry tracing is enabled")
        else:
            print("[INFO] OpenTelemetry not available, graceful fallback active")
        
        return True
    except Exception as e:
        print(f"[FAIL] OpenTelemetry integration failed: {e}")
        return False

def test_domain_validation():
    """Test domain format validation."""
    print("\n[TEST] Testing domain validation...")
    
    from shared_auth.middleware import _is_valid_auth0_domain
    
    valid_domains = [
        "tenant.auth0.com",
        "my-tenant.auth0.com", 
        "tenant.us.auth0.com",
        "tenant.eu.auth0.com",
        "custom-domain.com",
        "http://tenant.auth0.com",  # Should work after protocol removal
        "https://tenant.auth0.com"  # Should work after protocol removal
    ]
    
    invalid_domains = [
        "",
        "invalid",
        ".auth0.com",
        "tenant.",
        "http://invalid-domain"  # Invalid even after protocol removal
    ]
    
    for domain in valid_domains:
        if _is_valid_auth0_domain(domain):
            print(f"[PASS] Valid domain accepted: {domain}")
        else:
            print(f"[FAIL] Valid domain rejected: {domain}")
            return False
    
    for domain in invalid_domains:
        if not _is_valid_auth0_domain(domain):
            print(f"[PASS] Invalid domain rejected: {domain}")
        else:
            print(f"[FAIL] Invalid domain accepted: {domain}")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing new features...\n")
    
    success = True
    success &= test_startup_validation()
    success &= test_opentelemetry_integration() 
    success &= test_domain_validation()
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[ERROR] Some tests failed!")
        sys.exit(1)
