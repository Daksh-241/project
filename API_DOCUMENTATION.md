# FHIR Resource API Documentation

## Overview
This API provides an endpoint for processing FHIR Bundle transactions containing Patient and Observation resources. The API validates the resources, encrypts sensitive Patient data, and returns a transaction response bundle.

## Base URL
```
http://localhost:8000
```

## Endpoints

### Process FHIR Bundle
Process a FHIR Bundle containing Patient and Observation resources.

**URL**: `/fhir_resource`  
**Method**: `POST`  
**Auth required**: No

#### Request Body

The request must be a valid FHIR Bundle with the following structure:

```json
{
    "resourceType": "Bundle",
    "type": "transaction",
    "entry": [
        {
            "fullUrl": "urn:uuid:example-patient-id",
            "resource": {
                "resourceType": "Patient",
                "name": [
                    {
                        "family": "Smith",
                        "given": ["John", "Robert"]
                    }
                ],
                "gender": "male",
                "birthDate": "1970-01-01",
                "address": [
                    {
                        "line": ["123 Main St", "Apt 4B"],
                        "city": "Boston",
                        "state": "MA",
                        "postalCode": "02115",
                        "country": "USA"
                    }
                ],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "555-0123"
                    }
                ]
            },
            "request": {
                "method": "POST",
                "url": "Patient"
            }
        },
        {
            "fullUrl": "urn:uuid:example-observation-id",
            "resource": {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }
                    ]
                },
                "subject": {
                    "reference": "urn:uuid:example-patient-id"
                },
                "effectiveDateTime": "2025-09-20T15:30:00Z",
                "valueQuantity": {
                    "value": 120,
                    "unit": "mmHg",
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
```

#### Validation Rules

1. Bundle Requirements:
   - Must have `resourceType` set to "Bundle"
   - Must have `type` set to "transaction"
   - Must contain at least one resource in `entry` array

2. Patient Resource Requirements:
   - Must have `resourceType` set to "Patient"
   - Must include at least one `name` with `family` and `given` fields
   - `gender` and `birthDate` are required
   - `address` and `telecom` are optional

3. Observation Resource Requirements:
   - Must have `resourceType` set to "Observation"
   - Must have `status` field
   - Must have `code` with `coding` array
   - Must have `subject` reference to a Patient
   - Must have `effectiveDateTime`
   - `valueQuantity` is required with `value` and `unit`

#### Response

**Success Response (200 OK)**

```json
{
    "resourceType": "Bundle",
    "type": "transaction-response",
    "entry": [
        {
            "fullUrl": "urn:uuid:example-patient-id",
            "resource": {
                "resourceType": "Patient",
                "name": [
                    {
                        "family": "<encrypted>",
                        "given": ["<encrypted>", "<encrypted>"]
                    }
                ],
                "gender": "male",
                "birthDate": "1970-01-01",
                "address": [
                    {
                        "line": ["<encrypted>", "Apt 4B"],
                        "city": "Boston",
                        "state": "MA",
                        "postalCode": "02115",
                        "country": "USA"
                    }
                ]
            },
            "response": {
                "status": "201",
                "location": "Patient/example-patient-id"
            }
        },
        {
            "fullUrl": "urn:uuid:example-observation-id",
            "resource": {
                // Original Observation resource
            },
            "response": {
                "status": "201",
                "location": "Observation/example-observation-id"
            }
        }
    ]
}
```

**Error Responses**

1. Invalid Bundle Type (400 Bad Request)
```json
{
    "detail": "Only transaction bundles are supported"
}
```

2. Invalid Resource (422 Unprocessable Entity)
```json
{
    "detail": "Invalid Patient resource: [error details]"
}
```

3. Server Error (500 Internal Server Error)
```json
{
    "detail": "Error processing bundle: [error details]"
}
```

## Notes

1. Security Features:
   - Patient resource sensitive fields (family name, given names, first address line) are automatically encrypted
   - Other Patient fields remain unencrypted
   - Observation resources are not encrypted

2. Resource Processing:
   - Each resource is validated before processing
   - Resources are processed in the order they appear in the bundle
   - Cross-references between resources are maintained

3. Performance:
   - The API supports processing multiple resources in a single bundle
   - Large bundles may take longer to process due to encryption overhead

## Examples

### Minimal Valid Request

```json
{
    "resourceType": "Bundle",
    "type": "transaction",
    "entry": [
        {
            "resource": {
                "resourceType": "Patient",
                "name": [{"family": "Doe", "given": ["Jane"]}],
                "gender": "female",
                "birthDate": "1990-01-01"
            },
            "request": {
                "method": "POST",
                "url": "Patient"
            }
        }
    ]
}
```