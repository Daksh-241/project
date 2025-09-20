import sys
import logging
import traceback
from typing import List, Literal, Any, Dict, Optional    
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json
from cryptography.fernet import Fernet
import base64
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SECURITY WARNING: In a production environment, NEVER hardcode encryption keys!
# Keys should be:
# 1. Stored in a secure key management system
# 2. Rotated regularly
# 3. Different for each environment (dev/staging/prod)
# 4. Backed up securely
# Consider using services like AWS KMS, Azure Key Vault, or HashiCorp Vault
ENCRYPTION_KEY = Fernet.generate_key()  # Generate a new key each time the server starts
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_string(text: str) -> str:
    """Encrypt a string using Fernet symmetric encryption."""
    if not text:
        return text
    return base64.urlsafe_b64encode(
        fernet.encrypt(text.encode())
    ).decode('utf-8')

def decrypt_string(encrypted_text: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    if not encrypted_text:
        return encrypted_text
    try:
        decrypted = fernet.decrypt(
            base64.urlsafe_b64decode(encrypted_text.encode())
        )
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt string: {str(e)}")

def encrypt_patient_data(patient_resource: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive fields in a Patient resource."""
    if not isinstance(patient_resource, dict):
        return patient_resource
        
    # Handle name fields
    if "name" in patient_resource and isinstance(patient_resource["name"], list):
        for name in patient_resource["name"]:
            if isinstance(name, dict):
                if "family" in name:
                    name["family"] = encrypt_string(name["family"])
                if "given" in name and isinstance(name["given"], list):
                    name["given"] = [encrypt_string(g) for g in name["given"]]
    
    # Handle address fields
    if "address" in patient_resource and isinstance(patient_resource["address"], list):
        for addr in patient_resource["address"]:
            if isinstance(addr, dict) and "line" in addr and isinstance(addr["line"], list):
                if addr["line"]:  # Encrypt only the first line
                    addr["line"][0] = encrypt_string(addr["line"][0])
    
    return patient_resource

try:
    logger.debug("Initializing FastAPI application...")
    app = FastAPI(title="FHIR Converter API")

    # Add CORS middleware
    logger.debug("Configuring CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("CORS middleware configured successfully")
except Exception as e:
    logger.error(f"Error during application initialization: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# FHIR Resource Models
class Identifier(BaseModel):
    system: str
    value: str

class HumanName(BaseModel):
    family: str
    given: List[str]

class Address(BaseModel):
    line: List[str]
    city: str
    state: str
    postalCode: str
    country: str

class Telecom(BaseModel):
    system: str
    value: str

class Coding(BaseModel):
    system: str
    code: str
    display: str

class CodeableConcept(BaseModel):
    coding: List[Coding]

class Quantity(BaseModel):
    value: float
    unit: str
    system: Optional[str] = None
    code: str

class Reference(BaseModel):
    reference: str

class Patient(BaseModel):
    resourceType: str = "Patient"
    identifier: Optional[List[Identifier]] = None
    name: List[HumanName]
    gender: str
    birthDate: str
    address: Optional[List[Address]] = None
    telecom: Optional[List[Telecom]] = None

class Observation(BaseModel):
    resourceType: str = "Observation"
    status: str
    code: CodeableConcept
    subject: Reference
    effectiveDateTime: str
    valueQuantity: Optional[Quantity] = None

class RequestDetails(BaseModel):
    method: str
    url: str

class BundleEntry(BaseModel):
    fullUrl: Optional[str] = None
    resource: Dict[str, Any]
    request: RequestDetails

class FHIRResourceRequest(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["transaction", "batch", "collection"] = "transaction"
    entry: List[BundleEntry]

@app.get("/")
def read_root():
    return {"message": "FHIR Converter API running. Try /docs for API documentation."}

@app.post("/fhir_resource", response_model=Dict[str, Any])
async def create_fhir_resource(bundle: FHIRResourceRequest):
    """
    Process a FHIR Bundle transaction and create/update resources.
    Sensitive data in Patient resources will be encrypted before storage.
    """
    try:
        if bundle.type != "transaction":
            raise HTTPException(
                status_code=400,
                detail="Only transaction bundles are supported"
            )

        # Process each resource in the bundle
        processed_resources = []
        resource_refs = {}

        for entry in bundle.entry:
            resource = entry.resource
            resource_type = resource.get("resourceType")

            # Store the resource with its UUID reference if provided
            if entry.fullUrl:
                resource_refs[entry.fullUrl] = resource

            # Process based on resource type
            if resource_type == "Patient":
                try:
                    # Validate the Patient resource first
                    Patient(**resource)
                    # Encrypt sensitive patient data
                    resource = encrypt_patient_data(resource)
                except Exception as e:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid Patient resource: {str(e)}"
                    )

            elif resource_type == "Observation":
                try:
                    Observation(**resource)
                except Exception as e:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Invalid Observation resource: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported resource type: {resource_type}"
                )

            # Add processed resource to response
            processed_resources.append({
                "fullUrl": entry.fullUrl,
                "resource": resource,
                "response": {
                    "status": "201",
                    "location": f"{resource_type}/{resource.get('id', 'new')}"
                }
            })

        # Create response bundle
        response_bundle = {
            "resourceType": "Bundle",
            "type": "transaction-response",
            "entry": processed_resources
        }

        return response_bundle

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing bundle: {str(e)}"
        )

    # Create and return FHIR Bundle
    bundle = Bundle.construct(
        resourceType="Bundle",
        type="collection",
        entry=[{"resource": r.dict()} for r in resources]
    )
    return json.loads(bundle.json())    