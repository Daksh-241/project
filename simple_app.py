from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fhir_mapping import map_to_fhir_patient, map_to_fhir_observation, map_to_fhir_condition
from fhir.resources.bundle import Bundle
import json

app = FastAPI(title="FHIR Converter API")

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Resource(BaseModel):
    resourceType: str
    identifier: Optional[list] = None
    status: Optional[str] = None
    subject: Optional[dict] = None
    code: Optional[dict] = None
    effectiveDateTime: Optional[str] = None
    valueQuantity: Optional[dict] = None
    name: Optional[list] = None
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    address: Optional[list] = None
    telecom: Optional[list] = None

class RequestDetails(BaseModel):
    method: str
    url: str

class BundleEntry(BaseModel):
    fullUrl: Optional[str] = None
    resource: Resource
    request: RequestDetails

class FHIRResourceRequest(BaseModel):
    resourceType: str
    type: str
    entry: list[BundleEntry]

@app.get("/")
def read_root():
    return {"message": "FHIR Converter API running. Try /docs for API documentation."}

@app.post("/fhir_resource", response_model=Dict[str, Any])
async def create_fhir_resource(bundle: FHIRResourceRequest):
    """
    Process a FHIR Bundle transaction
    """
    try:
        # Validate bundle type
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
            
            # Store the resource with its UUID reference if provided
            if entry.fullUrl:
                resource_refs[entry.fullUrl] = resource.dict()
            
            # Add to processed resources
            processed_resources.append({
                "resource": resource.dict(),
                "request": entry.request.dict()
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

    if data.observation_name:
        obs = map_to_fhir_observation(data_dict, patient_id)
        resources.append(obs)
    
    if data.condition_name:
        cond = map_to_fhir_condition(data_dict, patient_id)
        resources.append(cond)

    # Create and return FHIR Bundle
    bundle = Bundle.construct(
        resourceType="Bundle",
        type="collection",
        entry=[{"resource": r.dict()} for r in resources]
    )
    return json.loads(bundle.json())