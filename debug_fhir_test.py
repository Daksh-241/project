import requests
import json
import sys
from pprint import pprint

def test_fhir_endpoint():
    print("Testing FHIR endpoint...")
    print("Connecting to FastAPI server...")
    
    sample_data = {
        "patient_id": "123",
        "first_name": "John",
        "last_name": "Doe",
        "gender": "male",
        "birth_date": "1980-01-01",
        "address": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "12345",
        "country": "USA",
        "phone": "555-1234",
        "email": "john.doe@example.com",
        "observation_name": "Blood Pressure",
        "loinc_code": "85354-9",
        "value": 120,
        "unit": "mmHg",
        "unit_code": "mm[Hg]",
        "observation_date": "2025-09-20T10:00:00Z",
        "condition_name": "Hypertension",
        "snomed_code": "38341003",
        "onset_date": "2020-01-01"
    }

    try:
        print("Sending request to http://127.0.0.1:8000/fhir_resource...")
        response = requests.post(
            "http://127.0.0.1:8000/fhir_resource",
            json=sample_data,
            timeout=30  # 30 seconds timeout
        )
        
        print(f"Status Code: {response.status_code}")
        if response.ok:
            print("\nSuccess! FHIR Bundle Response:")
            pprint(response.json())
        else:
            print("\nError Response:")
            pprint(response.text)
            
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Could not connect to the server. Is it running?")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    test_fhir_endpoint()