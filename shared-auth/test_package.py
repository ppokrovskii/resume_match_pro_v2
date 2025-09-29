#!/usr/bin/env python3
"""
Simple test script to verify the shared-auth package works correctly.
"""

import os
import sys

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all main imports work correctly."""
    print("Testing imports...")
    
    try:
        from shared_auth import (
            Auth0Middleware,
            AuthUser,
            require_auth,
            require_admin,
            auth0_subject_to_uuid,
            InvalidTokenError,
            ExpiredTokenError,
        )
        print("[OK] All imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_auth_user_model():
    """Test AuthUser model functionality."""
    print("Testing AuthUser model...")
    
    try:
        from shared_auth import AuthUser
        
        # Test basic creation
        user = AuthUser(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            roles=["admin", "member"],
            scopes=["read:documents", "write:documents"]
        )
        
        # Test properties
        assert user.is_admin == True
        assert user.has_role("admin") == True
        assert user.has_scope("read:documents") == True
        assert user.has_any_role(["admin", "staff"]) == True
        assert user.has_all_roles(["admin", "member"]) == True
        
        # Test serialization
        user_dict = user.to_dict()
        user2 = AuthUser.from_dict(user_dict)
        assert user2.user_id == user.user_id
        assert user2.email == user.email
        
        print("[OK] AuthUser model tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] AuthUser model test failed: {e}")
        return False

def test_utilities():
    """Test utility functions."""
    print("Testing utility functions...")
    
    try:
        from shared_auth import auth0_subject_to_uuid, is_valid_uuid, normalize_user_id
        
        # Test auth0_subject_to_uuid
        subject = "google-oauth2|107180533664024577076"
        uuid_result = auth0_subject_to_uuid(subject)
        assert len(uuid_result) == 36  # UUID format
        assert uuid_result.count("-") == 4
        
        # Test deterministic conversion
        uuid_result2 = auth0_subject_to_uuid(subject)
        assert uuid_result == uuid_result2
        
        # Test is_valid_uuid
        assert is_valid_uuid(uuid_result) == True
        assert is_valid_uuid("not-a-uuid") == False
        
        # Test normalize_user_id
        normalized = normalize_user_id(uuid_result)
        assert normalized == uuid_result
        
        normalized2 = normalize_user_id(subject)
        assert normalized2 == uuid_result
        
        print("[OK] Utility function tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Utility function test failed: {e}")
        return False

def test_middleware_creation():
    """Test Auth0Middleware can be created."""
    print("Testing Auth0Middleware creation...")
    
    try:
        from shared_auth import Auth0Middleware
        from shared_auth.exceptions import ConfigurationError
        
        # Test successful creation
        middleware = Auth0Middleware(
            domain="test.auth0.com",
            api_identifier="https://test-api.example.com"
        )
        
        assert middleware.domain == "test.auth0.com"
        assert middleware.api_identifier == "https://test-api.example.com"
        assert middleware.algorithms == ["RS256"]
        
        # Test missing domain
        try:
            Auth0Middleware(api_identifier="https://test-api.example.com")
            assert False, "Should have raised ConfigurationError"
        except ConfigurationError:
            pass  # Expected
        
        print("[OK] Auth0Middleware creation tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Auth0Middleware creation test failed: {e}")
        return False

def test_exceptions():
    """Test exception classes."""
    print("Testing exception classes...")
    
    try:
        from shared_auth.exceptions import (
            AuthenticationError,
            InvalidTokenError,
            ExpiredTokenError,
            InsufficientScopeError,
            InsufficientRoleError,
        )
        
        # Test base exception
        error = AuthenticationError("Test error", "TEST_ERROR", {"key": "value"})
        error_dict = error.to_dict()
        assert error_dict["success"] == False
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Test error"
        
        # Test specific exceptions
        invalid_token = InvalidTokenError("Invalid token")
        assert invalid_token.error_code == "INVALID_TOKEN"
        
        expired_token = ExpiredTokenError()
        assert expired_token.error_code == "TOKEN_EXPIRED"
        
        scope_error = InsufficientScopeError("write:documents", ["read:documents"])
        assert scope_error.required_scope == "write:documents"
        assert scope_error.user_scopes == ["read:documents"]
        
        role_error = InsufficientRoleError("admin", ["member"])
        assert role_error.required_role == "admin"
        assert role_error.user_roles == ["member"]
        
        print("[OK] Exception tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Exception test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running shared-auth package tests...\n")
    
    tests = [
        test_imports,
        test_auth_user_model,
        test_utilities,
        test_middleware_creation,
        test_exceptions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All tests passed! The shared-auth package is working correctly.")
        return 0
    else:
        print("FAILURE: Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
