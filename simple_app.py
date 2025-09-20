from typing import List, Literal, Any, Dict, Optional    
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import json

app = FastAPI(title="FHIR Converter API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    Process a FHIR Bundle transaction and create/update resources
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
                    Patient(**resource)
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