import requests
import json

try:
    # Fetch OpenAPI spec from running service
    response = requests.get('http://localhost:5001/openapi.json', timeout=10)
    response.raise_for_status()
    
    # Parse and save the spec
    openapi_spec = response.json()
    
    with open('document_service_openapi.json', 'w', encoding='utf-8') as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
    
    print("✅ OpenAPI spec fetched and saved successfully!")
    print(f"   Title: {openapi_spec.get('info', {}).get('title')}")
    print(f"   Version: {openapi_spec.get('info', {}).get('version')}")
    print(f"   Paths: {len(openapi_spec.get('paths', {}))}")
    print(f"   Components: {len(openapi_spec.get('components', {}).get('schemas', {}))}")
    
except Exception as e:
    print(f"❌ Error fetching OpenAPI spec: {e}")

