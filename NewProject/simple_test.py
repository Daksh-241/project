import requests
import json
from pprint import pprint
import uuid

def test_fhir_endpoint():
    print("Testing FHIR endpoint...")
    
    # Sample test data (flat structure)
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

    # Create a unique reference for the patient within this transaction
    patient_ref = f"urn:uuid:{uuid.uuid4()}"

    # Convert the flat sample_data into a FHIR transaction Bundle
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": patient_ref,
                "resource": {
                    "resourceType": "Patient",
                    "name": [{"family": sample_data["last_name"], "given": [sample_data["first_name"]]}],
                    "gender": sample_data["gender"],
                    "birthDate": sample_data["birth_date"],
                    "address": [{
                        "line": [sample_data["address"]],
                        "city": sample_data["city"],
                        "state": sample_data["state"],
                        "postalCode": sample_data["postal_code"],
                        "country": sample_data["country"]
                    }],
                    "telecom": [
                        {"system": "phone", "value": sample_data["phone"]},
                        {"system": "email", "value": sample_data["email"]}
                    ]
                },
                "request": {"method": "POST", "url": "Patient"}
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": sample_data["loinc_code"],
                            "display": sample_data["observation_name"]
                        }]
                    },
                    "subject": {"reference": patient_ref},
                    "effectiveDateTime": sample_data["observation_date"],
                    "valueQuantity": {
                        "value": sample_data["value"],
                        "unit": sample_data["unit"],
                        "system": "http://unitsofmeasure.org",
                        "code": sample_data["unit_code"]
                    }
                },
                "request": {"method": "POST", "url": "Observation"}
            }
        ]
    }


    try:
        # First check if the server is running
        response = requests.get("http://127.0.0.1:8000/")
        if not response.ok:
            print(f"Server check failed with status code: {response.status_code}")
            return

        print("\nServer is running. Sending FHIR transaction bundle...")
        
        # Send the FHIR Bundle
        response = requests.post(
            "http://127.0.0.1:8000/fhir_resource",
            json=fhir_bundle,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.ok:
            print("\nSuccess! FHIR Bundle Response:")
            pprint(response.json())
        else:
            print("\nError Response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError as e:
        print(f"\nConnection Error: Could not connect to the server. Is it running?")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        raise

if __name__ == "__main__":
    test_fhir_endpoint()