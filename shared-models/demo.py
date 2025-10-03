#!/usr/bin/env python3
"""
Demonstration of shared-models usage for Resume Match Pro.

This script shows how other microservices can use the shared models
to interact with the document-service API in a type-safe way.
"""

import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add src to path for demo
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_ai_text_extract_usage():
    """Demonstrate how ai-text-extract service would use shared models."""
    print("🤖 AI Text Extract Service - Using Shared Models")
    print("=" * 50)
    
    from shared_models.generated.document_service import (
        DocumentUpdateRequest,
        Feature,
        FeatureProperties
    )
    
    # AI service extracts features from a CV
    print("1. Creating extracted features...")
    
    features = [
        Feature(
            name="Python",
            type="skill",
            properties=FeatureProperties(
                years=5,
                level="expert",
                description="Advanced Python programming with Django and FastAPI"
            )
        ),
        Feature(
            name="AWS Solutions Architect",
            type="certification",
            properties=FeatureProperties(
                grade="Professional",
                year_obtained=2023,
                expires=2026
            )
        ),
        Feature(
            name="Machine Learning",
            type="skill",
            properties=FeatureProperties(
                years=3,
                level="advanced",
                description="Experience with scikit-learn, TensorFlow, and PyTorch"
            )
        ),
        Feature(
            name="Spanish",
            type="language",
            properties=FeatureProperties(
                fluency="fluent",
                certification="DELE B2"
            )
        )
    ]
    
    for feature in features:
        print(f"   - {feature.name} ({feature.type})")
        if feature.properties.years:
            print(f"     Years: {feature.properties.years}")
        if feature.properties.level:
            print(f"     Level: {feature.properties.level}")
    
    # Create update request to send to document-service
    print("\n2. Creating document update request...")
    
    update_request = DocumentUpdateRequest(
        file_type="cv",
        text_content="""# John Doe
Senior Software Engineer

## Contact
- Email: john.doe@email.com
- Phone: +1-555-0123
- LinkedIn: linkedin.com/in/johndoe

## Experience

### Senior Python Developer | Tech Corp (2021-Present)
- Led development of microservices architecture using FastAPI
- Implemented CI/CD pipelines reducing deployment time by 60%
- Mentored junior developers and conducted code reviews

### Software Engineer | StartupXYZ (2019-2021)
- Built machine learning models for recommendation system
- Developed RESTful APIs serving 1M+ requests daily
- Collaborated with cross-functional teams using Agile methodology

## Skills
- **Programming**: Python, JavaScript, SQL
- **Frameworks**: Django, FastAPI, React
- **Cloud**: AWS (EC2, S3, Lambda, RDS)
- **Databases**: PostgreSQL, MongoDB, Redis
- **Tools**: Docker, Kubernetes, Git, Jenkins

## Education
- **M.S. Computer Science** | University of Technology (2019)
- **B.S. Software Engineering** | State University (2017)

## Certifications
- AWS Certified Solutions Architect - Professional (2023)
- Certified Kubernetes Administrator (2022)""",
        role="Senior Python Developer",
        features=features,
        metadata={
            "processing_version": "2.1.0",
            "confidence_score": 0.96,
            "processing_time_ms": 1234,
            "extracted_sections": ["contact", "experience", "skills", "education", "certifications"]
        }
    )
    
    print(f"   File Type: {update_request.file_type}")
    print(f"   Role: {update_request.role}")
    print(f"   Features: {len(update_request.features)} extracted")
    print(f"   Confidence: {update_request.metadata['confidence_score']}")
    
    # Serialize for API call
    print("\n3. Serializing for API call...")
    json_data = update_request.model_dump()
    print(f"   JSON size: {len(str(json_data))} characters")
    print(f"   Features in JSON: {len(json_data['features'])}")
    
    print("✅ AI Text Extract service can now send this to document-service PUT /api/v1/documents/{id}")
    print()


def demo_matches_service_usage():
    """Demonstrate how matches-service would use shared models."""
    print("🎯 Matches Service - Using Shared Models")
    print("=" * 40)
    
    from shared_models.generated.document_service import (
        DocumentResponse,
        DocumentListResponse,
        Feature,
        FeatureProperties
    )
    
    # Simulate receiving document data from document-service
    print("1. Processing documents from document-service...")
    
    # Create sample CV document
    cv_features = [
        Feature(name="Python", type="skill", properties=FeatureProperties(years=5, level="expert")),
        Feature(name="React", type="skill", properties=FeatureProperties(years=3, level="advanced")),
        Feature(name="AWS", type="skill", properties=FeatureProperties(years=4, level="advanced")),
    ]
    
    cv_document = DocumentResponse(
        id=uuid4(),
        user_id=uuid4(),
        organization_id=uuid4(),
        filename="john_doe_resume.pdf",
        file_type="cv",
        content_type="application/pdf",
        file_size=1024000,
        storage_path="documents/org123/user456/john_doe_resume.pdf",
        text_content="# John Doe\nSenior Software Engineer...",
        role="Senior Python Developer",
        features=cv_features,
        processing_status="completed",
        metadata={"confidence_score": 0.96},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create sample JD document
    jd_features = [
        Feature(name="Python", type="skill", properties=FeatureProperties(required=True, min_years=3)),
        Feature(name="React", type="skill", properties=FeatureProperties(preferred=True, min_years=2)),
        Feature(name="AWS", type="skill", properties=FeatureProperties(required=True, min_years=2)),
        Feature(name="Machine Learning", type="skill", properties=FeatureProperties(preferred=True)),
    ]
    
    jd_document = DocumentResponse(
        id=uuid4(),
        user_id=uuid4(),
        organization_id=uuid4(),
        filename="senior_python_job.pdf",
        file_type="jd",
        content_type="application/pdf",
        file_size=512000,
        storage_path="documents/org123/user789/senior_python_job.pdf",
        text_content="# Senior Python Developer\n\nWe are looking for...",
        role="Senior Python Developer",
        features=jd_features,
        processing_status="completed",
        metadata={"confidence_score": 0.94},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    print(f"   CV: {cv_document.filename} ({len(cv_document.features)} features)")
    print(f"   JD: {jd_document.filename} ({len(jd_document.features)} features)")
    
    # Calculate match score (simplified)
    print("\n2. Calculating match scores...")
    
    cv_skills = {f.name: f.properties for f in cv_document.features if f.type == "skill"}
    jd_requirements = {f.name: f.properties for f in jd_document.features if f.type == "skill"}
    
    matches = 0
    total_requirements = 0
    
    for skill, requirements in jd_requirements.items():
        total_requirements += 1
        if skill in cv_skills:
            cv_skill = cv_skills[skill]
            matches += 1
            
            # Check experience requirements
            if requirements.min_years and cv_skill.years:
                meets_experience = cv_skill.years >= requirements.min_years
                print(f"   ✅ {skill}: {cv_skill.years} years (required: {requirements.min_years}) - {'✓' if meets_experience else '✗'}")
            else:
                print(f"   ✅ {skill}: Present")
        else:
            required_text = "REQUIRED" if requirements.required else "PREFERRED"
            print(f"   ❌ {skill}: Missing ({required_text})")
    
    match_score = (matches / total_requirements) * 100 if total_requirements > 0 else 0
    print(f"\n   Overall Match Score: {match_score:.1f}% ({matches}/{total_requirements} skills matched)")
    
    print("✅ Matches service can process documents with full type safety")
    print()


def demo_serialization_features():
    """Demonstrate serialization features."""
    print("📦 Serialization & Validation Features")
    print("=" * 38)
    
    from shared_models.generated.document_service import Feature, FeatureProperties
    from pydantic import ValidationError
    
    print("1. JSON serialization...")
    
    feature = Feature(
        name="Python",
        type="skill",
        properties=FeatureProperties(years=5, level="expert")
    )
    
    # Serialize to dict
    data = feature.model_dump()
    print(f"   Dict: {data}")
    
    # Serialize to JSON string
    json_str = feature.model_dump_json()
    print(f"   JSON: {json_str}")
    
    print("\n2. Validation...")
    
    # Valid data
    try:
        valid_feature = Feature(name="JavaScript", type="skill")
        print("   ✅ Valid feature created")
    except ValidationError as e:
        print(f"   ❌ Validation failed: {e}")
    
    # Invalid data
    try:
        invalid_feature = Feature(name="", type="skill")  # Empty name
        print("   ❌ Should have failed validation")
    except ValidationError as e:
        print(f"   ✅ Validation correctly caught error: {e.error_count()} errors")
    
    print("\n3. Flexible properties...")
    
    # Properties can have arbitrary fields
    props = FeatureProperties(
        years=3,
        level="intermediate",
        custom_field="custom_value",
        certification_date="2023-06-15",
        vendor="Microsoft"
    )
    
    print(f"   Standard fields: years={props.years}, level={props.level}")
    print(f"   Custom fields: certification_date, vendor, custom_field")
    print(f"   Serialized: {props.model_dump()}")
    
    print("✅ Models provide flexible, type-safe data handling")
    print()


def main():
    """Run all demonstrations."""
    print("🚀 Resume Match Pro - Shared Models Demo")
    print("=" * 60)
    print()
    
    demo_ai_text_extract_usage()
    demo_matches_service_usage()
    demo_serialization_features()
    
    print("🎉 Demo completed!")
    print("\nThe shared-models package provides:")
    print("  ✅ Type-safe API integration")
    print("  ✅ Automatic validation")
    print("  ✅ JSON serialization/deserialization")
    print("  ✅ IDE support with auto-completion")
    print("  ✅ Runtime error detection")
    print("  ✅ Flexible, extensible data structures")
    print("\nReady for use across all Resume Match Pro microservices! 🎯")


if __name__ == "__main__":
    main()
