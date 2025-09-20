import requests
import json
from pprint import pprint

def test_fhir_bundle():
    print("Testing FHIR Bundle endpoint...")
    
    # FHIR Bundle transaction
    fhir_bundle = {
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
        # First check if server is running
        health_check = requests.get("http://127.0.0.1:8000/")
        if health_check.ok:
            print("Server is running, proceeding with test...")
        else:
            print("Server health check failed. Make sure the server is running.")
            return

        # Send the FHIR Bundle
        print("\nSending FHIR Bundle transaction...")
        response = requests.post(
            "http://127.0.0.1:8000/fhir_resource",
            json=fhir_bundle,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.ok:
            print("\nSuccess! Transaction Response Bundle:")
            pprint(response.json())
        else:
            print("\nError Response:")
            pprint(response.json())
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nConnection Error: Could not connect to the server. Is it running?")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise

if __name__ == "__main__":
    test_fhir_bundle()