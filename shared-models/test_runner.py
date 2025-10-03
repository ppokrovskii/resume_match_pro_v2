"""Simple test runner to validate our models work."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test that we can import all the models."""
    try:
        from shared_models.generated.document_service import (
            Feature,
            FeatureProperties,
            DocumentResponse,
            DocumentUpdateRequest,
            DocumentListResponse,
            BulkUploadResponse,
        )
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_feature_creation():
    """Test creating a Feature with properties."""
    try:
        from shared_models.generated.document_service import Feature, FeatureProperties
        
        # Test basic feature
        feature = Feature(name="Python", type="skill")
        assert feature.name == "Python"
        assert feature.type == "skill"
        print("✅ Basic feature creation works")
        
        # Test feature with properties
        props = FeatureProperties(years=5, level="expert")
        feature_with_props = Feature(
            name="Python",
            type="skill", 
            properties=props
        )
        assert feature_with_props.properties.years == 5
        assert feature_with_props.properties.level == "expert"
        print("✅ Feature with properties creation works")
        
        return True
    except Exception as e:
        print(f"❌ Feature creation failed: {e}")
        return False

def test_document_update_request():
    """Test creating a DocumentUpdateRequest."""
    try:
        from shared_models.generated.document_service import (
            DocumentUpdateRequest,
            Feature,
            FeatureProperties
        )
        
        feature = Feature(
            name="Python",
            type="skill",
            properties=FeatureProperties(years=5, level="expert")
        )
        
        request = DocumentUpdateRequest(
            file_type="cv",
            text_content="# John Doe\n\nSoftware Engineer...",
            role="Senior Python Developer",
            features=[feature],
            metadata={"confidence_score": 0.95}
        )
        
        assert request.file_type == "cv"
        assert request.role == "Senior Python Developer"
        assert len(request.features) == 1
        assert request.features[0].name == "Python"
        assert request.metadata["confidence_score"] == 0.95
        
        print("✅ DocumentUpdateRequest creation works")
        return True
    except Exception as e:
        print(f"❌ DocumentUpdateRequest creation failed: {e}")
        return False

def test_json_serialization():
    """Test JSON serialization/deserialization."""
    try:
        from shared_models.generated.document_service import Feature, FeatureProperties
        
        feature = Feature(
            name="Python",
            type="skill",
            properties=FeatureProperties(years=5, level="expert")
        )
        
        # Test serialization
        json_data = feature.model_dump()
        assert json_data["name"] == "Python"
        assert json_data["type"] == "skill"
        assert json_data["properties"]["years"] == 5
        
        # Test deserialization
        new_feature = Feature(**json_data)
        assert new_feature.name == feature.name
        assert new_feature.type == feature.type
        assert new_feature.properties.years == feature.properties.years
        
        print("✅ JSON serialization/deserialization works")
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running shared-models validation tests...\n")
    
    tests = [
        test_basic_imports,
        test_feature_creation,
        test_document_update_request,
        test_json_serialization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The shared-models package is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
