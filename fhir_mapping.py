import json
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from typing import Dict, Any

def map_to_fhir_patient(data: Dict[str, Any]) -> Patient:
    return Patient(
        id=str(data.get('patient_id', '')),
        name=[{
            'family': data.get('last_name', ''),
            'given': [data.get('first_name', '')]
        }],
        gender=data.get('gender', ''),
        birthDate=data.get('birth_date', ''),
        address=[{
            'line': [data.get('address', '')],
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'postalCode': data.get('postal_code', ''),
            'country': data.get('country', '')
        }],
        telecom=[
            {'system': 'phone', 'value': data.get('phone', '')},
            {'system': 'email', 'value': data.get('email', '')}
        ]
    )

def map_to_fhir_observation(data: Dict[str, Any], patient_id: str) -> Observation:
    return Observation(
        subject={'reference': f'Patient/{patient_id}'},
        code={
            'coding': [{
                'system': 'http://loinc.org',
                'code': data.get('loinc_code', ''),
                'display': data.get('observation_name', '')
            }]
        },
        valueQuantity={
            'value': data.get('value', ''),
            'unit': data.get('unit', ''),
            'code': data.get('unit_code', '')
        },
        effectiveDateTime=data.get('observation_date', '')
    )

def map_to_fhir_condition(data: Dict[str, Any], patient_id: str) -> Condition:
    return Condition(
        subject={'reference': f'Patient/{patient_id}'},
        code={
            'coding': [{
                'system': 'http://snomed.info/sct',
                'code': data.get('snomed_code', ''),
                'display': data.get('condition_name', '')
            }]
        },
        onsetDateTime=data.get('onset_date', '')
    )
