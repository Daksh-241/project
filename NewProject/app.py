from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from s import search_disease, read_excel_smart, prepare_merged
from db import init_db, get_db, User, LookupLog
from fhir_mapping import map_to_fhir_patient, map_to_fhir_observation, map_to_fhir_condition
from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryResponse
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
import json
from fhir.resources.operationoutcome import OperationOutcome, OperationOutcomeIssue

# Initialize these as None first
siddha_df = None
unani_df = None
merged_df = None

# Will load these when needed
SIDDHA_PATH = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/NATIONAL SIDDHA MORBIDITY CODES.xls")
UNANI_PATH  = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/NATIONAL UNANI MORBIDITY CODES.xls")
MERGED_PATH = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/merged_dataset.xlsx")

app = FastAPI(title="AYUSH Lookup API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Initializes the database and loads data files on application startup."""
    global siddha_df, unani_df, merged_df
    init_db()
    
    print("Loading data files...")
    if SIDDHA_PATH.exists():
        siddha_df = read_excel_smart(SIDDHA_PATH)
        print("Siddha data loaded successfully.")
    else:
        print(f"Warning: Siddha data file not found at {SIDDHA_PATH}")

    if UNANI_PATH.exists():
        unani_df = read_excel_smart(UNANI_PATH)
        print("Unani data loaded successfully.")
    else:
        print(f"Warning: Unani data file not found at {UNANI_PATH}")

    if MERGED_PATH.exists():
        merged_df = prepare_merged(read_excel_smart(MERGED_PATH))
        print("Merged data loaded successfully.")
    else:
        print(f"Warning: Merged data file not found at {MERGED_PATH}")

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str

class LookupRequest(BaseModel):
    user_id: Optional[int] = None
    disease_text: str
    fuzzy_threshold: int = 85
    fuzzy_top_k: int = 5

class LookupResponse(BaseModel):
    user_id: Optional[int] = None
    result: Dict

class ProfileResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str]
    lookups: List[Dict]

class SaveLookupRequest(BaseModel):
    user_id: int
    disease_text: str
    result: Dict

@app.get("/")
def root():
    return {"message": "AYUSH Lookup API running. Check /docs"}

@app.post("/users", response_model=Dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

@app.post("/login", response_model=Dict)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}


@app.post("/lookup", response_model=LookupResponse)
def lookup(req: LookupRequest, db: Session = Depends(get_db)):
    text = (req.disease_text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="disease_text is required")

    out = search_disease(
        text,
        siddha_df=siddha_df,
        unani_df=unani_df,
        merged_df=merged_df,
        fuzzy_top_k=req.fuzzy_top_k,
        fuzzy_threshold=req.fuzzy_threshold,
    )

    # log = LookupLog(user_id=req.user_id, disease_text=text, result_json=out)
    # db.add(log)
    # db.commit()
    # db.refresh(log)

    return {"user_id": req.user_id, "result": out}

@app.post("/save_lookup")
def save_lookup(req: SaveLookupRequest, db: Session = Depends(get_db)):
    log = LookupLog(user_id=req.user_id, disease_text=req.disease_text, result_json=req.result)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Lookup saved successfully"}

@app.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    lookups = [
        {"disease_text": l.disease_text, "result": l.result_json, "created_at": l.created_at}
        for l in user.lookups
    ]
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "lookups": lookups,
    }

def encrypt(value: str) -> str:
    """A simple placeholder for an encryption function."""
    return "<encrypted>"

@app.post("/fhir_resource")
def process_fhir_bundle(bundle: Bundle):
    """
    Processes a FHIR Bundle transaction containing Patient and Observation resources.
    Validates the resources, encrypts sensitive Patient data, and returns a
    transaction response bundle.
    """
    if bundle.resource_type != "Bundle" or bundle.type != "transaction":
        raise HTTPException(status_code=400, detail="Only transaction bundles are supported")

    if not bundle.entry:
        raise HTTPException(status_code=400, detail="Bundle must contain at least one entry")

    response_entries = []
    for entry in bundle.entry:
        resource = entry.resource
        response_entry = BundleEntry(
            fullUrl=entry.fullUrl,
            response=BundleEntryResponse(status="201 Created")
        )

        if resource.resource_type == "Patient":
            try:
                patient = Patient(**resource.dict())
                # Basic validation from docs
                if not patient.name or not patient.name[0].family or not patient.name[0].given:
                    raise ValueError("Patient name with family and given is required.")
                if not patient.gender or not patient.birthDate:
                    raise ValueError("Patient gender and birthDate are required.")

                # "Encrypt" sensitive fields as per documentation
                if patient.name and patient.name[0]:
                    patient.name[0].family = encrypt(patient.name[0].family)
                    patient.name[0].given = [encrypt(name) for name in patient.name[0].given]
                if patient.address and patient.address[0] and patient.address[0].line:
                    patient.address[0].line[0] = encrypt(patient.address[0].line[0])

                response_entry.resource = patient
                response_entry.response.location = f"Patient/{entry.fullUrl.split(':')[-1]}"
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid Patient resource: {e}")

        elif resource.resource_type == "Observation":
            try:
                # Basic validation from docs
                obs = Observation(**resource.dict())
                if not all([obs.status, obs.code, obs.subject, obs.effectiveDateTime, obs.valueQuantity]):
                     raise ValueError("Observation is missing required fields.")

                # No encryption for Observation
                response_entry.resource = obs
                response_entry.response.location = f"Observation/{entry.fullUrl.split(':')[-1]}"
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid Observation resource: {e}")

        else:
            # Handle other resource types if necessary, or reject them
            outcome = OperationOutcome(issue=[OperationOutcomeIssue(
                severity="error",
                code="not-supported",
                diagnostics=f"Resource type '{resource.resource_type}' not supported."
            )])
            response_entry.response.status = "400 Bad Request"
            response_entry.response.outcome = outcome

        response_entries.append(response_entry)

    response_bundle = Bundle.construct(
        resourceType="Bundle",
        type="transaction-response",
        entry=response_entries
    )

    # Return as a dictionary to be automatically converted to JSON by FastAPI
    return json.loads(response_bundle.json(exclude_none=True))
