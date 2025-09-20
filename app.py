from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from s import search_disease, read_excel_smart, prepare_merged
from db import init_db, get_db, User, LookupLog
from fhir_mapping import map_to_fhir_patient, map_to_fhir_observation, map_to_fhir_condition
from fhir.resources.bundle import Bundle
import json

# Initialize these as None first
siddha_df = None
unani_df = None
merged_df = None

# Will load these when needed
# SIDDHA_PATH = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/NATIONAL SIDDHA MORBIDITY CODES.xls")
# UNANI_PATH  = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/NATIONAL UNANI MORBIDITY CODES.xls")
# MERGED_PATH = Path(r"C:/Users/DY15D/OneDrive/Desktop/NewProject/NewProject/merged_dataset.xlsx")

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
    init_db()

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

class FHIRResourceRequest(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    gender: str
    birth_date: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    observation_name: Optional[str] = None
    loinc_code: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    unit_code: Optional[str] = None
    observation_date: Optional[str] = None
    condition_name: Optional[str] = None
    snomed_code: Optional[str] = None
    onset_date: Optional[str] = None

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

@app.post("/fhir_resource")
def create_fhir_resource(data: FHIRResourceRequest):
    """
    Accepts FHIR resource data and returns a FHIR Bundle JSON.
    """
    # Convert Pydantic model to dict for compatibility
    data = data.dict()
    patient = map_to_fhir_patient(data)
    patient_id = patient.id or "1"
    resources = [patient]

    if 'observation_name' in data:
        obs = map_to_fhir_observation(data, patient_id)
        resources.append(obs)
    if 'condition_name' in data:
        cond = map_to_fhir_condition(data, patient_id)
        resources.append(cond)

    bundle = Bundle.construct(
        resourceType="Bundle",
        type="collection",
        entry=[{"resource": r.dict()} for r in resources]
    )
    return json.loads(bundle.json())
