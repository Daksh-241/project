import requests
import json
from pprint import pprint

def test_patient_encryption():
    """Test the FHIR Bundle endpoint with a Patient resource to verify encryption."""
    
    # Test bundle with sensitive patient information
    test_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [{
            "resource": {
                "resourceType": "Patient",
                "name": [{
                    "family": "Smith",
                    "given": ["John", "Robert"]
                }],
                "address": [{
                    "line": ["123 Main St", "Apt 4B"],
                    "city": "Boston",
                    "state": "MA",
                    "postalCode": "02115"
                }],
                "gender": "male",
                "birthDate": "1970-01-01"
            },
            "request": {
                "method": "POST",
                "url": "Patient"
            }
        }]
    }

    # Send the bundle to the server
    response = requests.post(
        "http://localhost:8000/fhir_resource",
        json=test_bundle
    )
    
    print("\n=== Test Results ===")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Get the processed Patient resource
        processed_patient = result["entry"][0]["resource"]
        
        print("\nProcessed Patient Resource:")
        pprint(processed_patient)
        
        # Verify encryption by checking if sensitive fields are different from original
        original_name = test_bundle["entry"][0]["resource"]["name"][0]
        processed_name = processed_patient["name"][0]
        
        print("\nEncryption Verification:")
        print(f"Original family name: {original_name['family']}")
        print(f"Encrypted family name: {processed_name['family']}")
        print(f"Original given names: {original_name['given']}")
        print(f"Encrypted given names: {processed_name['given']}")
        print(f"Original address line: {test_bundle['entry'][0]['resource']['address'][0]['line'][0]}")
        print(f"Encrypted address line: {processed_patient['address'][0]['line'][0]}")
        
        # Verify that non-sensitive fields remain unchanged
        print("\nNon-sensitive Field Verification:")
        print(f"Gender (should be unchanged): {processed_patient['gender']}")
        print(f"Birth Date (should be unchanged): {processed_patient['birthDate']}")
        print(f"City (should be unchanged): {processed_patient['address'][0]['city']}")
        
        # Basic verification that encryption occurred
        is_encrypted = (
            original_name['family'] != processed_name['family'] and
            original_name['given'] != processed_name['given'] and
            test_bundle['entry'][0]['resource']['address'][0]['line'][0] != 
            processed_patient['address'][0]['line'][0]
        )
        
        print(f"\nEncryption Test {'PASSED' if is_encrypted else 'FAILED'}")
        
    else:
        print("\nError Response:")
        pprint(response.json())

if __name__ == "__main__":
    test_patient_encryption()