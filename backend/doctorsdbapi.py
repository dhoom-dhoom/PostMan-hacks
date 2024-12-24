from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from pydantic import BaseModel
from typing import List

# Initialize Firebase
cred = credentials.Certificate("C:\\Users\\ayush\\OneDrive\\Documents\\nylas_setup\\bitshackathon-564f0-firebase-adminsdk-k32o9-64eac88ab0.json")
initialize_app(cred)

# Initialize Firestore
db = firestore.client()

app = FastAPI()

# Models for Users, Doctors, and Appointments
class User(BaseModel):
    user_id: str
    name: str
    email: str
    appointments: List[str]  # List of appointment IDs


class Doctor(BaseModel):
    doctor_id: str
    name: str
    specialty: str
    department: str
    slots: List[dict]  # Example: [{"time": "10:00 AM", "date": "2024-12-25", "available": True}]


class Appointment(BaseModel):
    appointment_id: str
    user_id: str
    doctor_id: str
    time: str
    date: str


# CRUD Operations
@app.post("/users/")
def create_user(user: User):
    try:
        user_ref = db.collection("users").document(user.user_id)
        user_ref.set(user.dict())
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}")
def get_user(user_id: str):
    try:
        user_ref = db.collection("users").document(user_id)
        user_data = user_ref.get()
        if user_data.exists:
            return user_data.to_dict()
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/doctors/")
def create_doctor(doctor: Doctor):
    try:
        doctor_ref = db.collection("doctors").document(doctor.doctor_id)
        doctor_ref.set(doctor.dict())
        return {"message": "Doctor created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    try:
        doctor_ref = db.collection("doctors").document(doctor_id)
        doctor_data = doctor_ref.get()
        if doctor_data.exists:
            return doctor_data.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Doctor not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments/")
def create_appointment(appointment: Appointment):
    try:
        appointment_ref = db.collection("appointments").document(appointment.appointment_id)
        appointment_ref.set(appointment.dict())
        return {"message": "Appointment created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: str):
    try:
        appointment_ref = db.collection("appointments").document(appointment_id)
        appointment_data = appointment_ref.get()
        if appointment_data.exists:
            return appointment_data.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
