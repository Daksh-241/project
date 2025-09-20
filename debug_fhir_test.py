import requests
import json
import sys
from pprint import pprint

def test_fhir_endpoint():
    print("Testing FHIR endpoint...")
    print("Connecting to FastAPI server...")
    
    # Create a FHIR Bundle transaction
    sample_data = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": "urn:uuid:13a456c7-3932-426b-8c50-c8205dcd0e10",
                "resource": {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": "http://example.org/patient_id",
                            "value": "123"
                        }
                    ],
                    "name": [
                        {
                            "family": "Doe",
                            "given": ["John"]
                        }
                    ],
                    "gender": "male",
                    "birthDate": "1980-01-01",
                    "address": [
                        {
                            "line": ["123 Main St"],
                            "city": "Metropolis",
                            "state": "NY",
                            "postalCode": "12345",
                            "country": "USA"
                        }
                    ],
                    "telecom": [
                        {
                            "system": "phone",
                            "value": "555-1234"
                        },
                        {
                            "system": "email",
                            "value": "john.doe@example.com"
                        }
                    ]
                },
                "request": {
                    "method": "POST",
                    "url": "Patient"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "85354-9",
                                "display": "Blood Pressure"
                            }
                        ]
                    },
                    "subject": {
                        "reference": "urn:uuid:13a456c7-3932-426b-8c50-c8205dcd0e10"
                    },
                    "effectiveDateTime": "2025-09-20T10:00:00Z",
                    "valueQuantity": {
                        "value": 120,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mm[Hg]"
                    }
                },
                "request": {
                    "method": "POST",
                    "url": "Observation"
                }
            }
        ]
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