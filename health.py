from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import logging


FHIR_API_URL = "http://localhost:8080/fhir"

app = FastAPI(
    title="Healthcare Management System",
    description="API for managing healthcare data.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthRecord(BaseModel):
    id: str
    patient_name: str
    gender: Optional[str]
    birth_date: Optional[str]
    address: Optional[List[dict]]
    contact: Optional[List[dict]]


def fetch_patient_records(patient_id: str):
    """
    Fetch patient records using the $everything operation from the HAPI FHIR server.
    """
    url = f"{FHIR_API_URL}/Patient/{patient_id}/$everything"
    
    try:
        logger.info(f"Fetching health records for patient {patient_id} from {url}")
        response = requests.get(url, headers={"Content-Type": "application/json"})

        if response.status_code == 200:
            data = response.json()
            
           
            if not data.get("entry"):
                logger.warning(f"No records found for patient {patient_id}.")
                return [] 

            return parse_health_records(data)
        else:
            logger.error(f"FHIR server returned error for patient {patient_id}: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        logger.error(f"Exception occurred while fetching health records for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def parse_health_records(data: dict):
    """
    Parse FHIR response to extract relevant patient data.
    """
    records = []
    patient_name = "Unknown"
    gender = None
    birth_date = None
    address = []
    contact = []

    
    logger.info(f"FHIR Response Data: {data}")

    
    if "entry" in data:
        for entry in data["entry"]:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

          
            if resource_type == "Patient":
                
                name = resource.get("name", [{}])[0]
                patient_name = f"{name.get('family', '')} {' '.join(name.get('given', []))}"

              
                gender = resource.get("gender", None)
                birth_date = resource.get("birthDate", None)

                
                address = resource.get("address", [])

            
                contact = resource.get("contact", [])

      
        record = HealthRecord(
            id=data.get("id", "Unknown"),
            patient_name=patient_name,
            gender=gender,
            birth_date=birth_date,
            address=address,
            contact=contact,
        )
        records.append(record)

    return records


@app.get("/api/v1/health_records/{patient_id}", response_model=List[HealthRecord])
async def get_health_records(patient_id: str):
    """
    Fetch and return health records for a patient.
    """
    try:
        records = fetch_patient_records(patient_id)
        if not records:  
            logger.info(f"No health records found for patient {patient_id}.")
        return records
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/add_patient")
async def add_patient(patient_data: dict):
    """
    Add a patient resource to the HAPI FHIR server.
    """
    url = f"{FHIR_API_URL}/Patient"
    try:
        response = requests.post(url, json=patient_data, headers={"Content-Type": "application/fhir+json"})
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error(f"Failed to add patient: {response.status_code}, {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while adding patient: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while adding patient: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/api/v1/test_connection")
async def test_connection():
    """
    Test connection to HAPI FHIR server.
    """
    try:
        url = f"{FHIR_API_URL}/metadata"  
        response = requests.get(url, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            return {"message": "Successfully connected to HAPI FHIR server"}
        else:
            logger.error(f"Failed to connect. Status code: {response.status_code}, Details: {response.text}")
            return {"error": f"Failed to connect. Status code: {response.status_code}", "details": response.text}
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        return {"error": "Connection failed", "details": str(e)}


@app.get("/")
async def root():
    return {"message": "Welcome to the Healthcare Management System API"}
