from fastapi import FastAPI, HTTPException
from firebase_admin import credentials, firestore, initialize_app
from pydantic import BaseModel
from typing import List

# Initialize Firebase
cred = credentials.Certificate("path to firebase sdk json")  
initialize_app(cred)

db = firestore.client()

# FastAPI instance
app = FastAPI()

# Pydantic Models
class TimeSlot(BaseModel):
    time: str  # e.g., "10:00-10:30"
    is_booked: bool  # True if booked, False if available

class Doctor(BaseModel):
    doctor_id: str
    name: str
    speciality: str
    available_time_slots: List[TimeSlot]

# CRUD Endpoints

# Create a Doctor
@app.post("/doctors/")
async def create_doctor(doctor: Doctor):
    doc_ref = db.collection("doctors").document(doctor.doctor_id)
    if doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="Doctor already exists")
    doc_ref.set(doctor.dict())
    return {"message": "Doctor created successfully"}

# Read a Doctor
@app.get("/doctors/{doctor_id}")
async def read_doctor(doctor_id: str):
    doc = db.collection("doctors").document(doctor_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doc.to_dict()

# Update a Doctor
@app.put("/doctors/{doctor_id}")
async def update_doctor(doctor_id: str, updated_data: Doctor):
    doc_ref = db.collection("doctors").document(doctor_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doc_ref.update(updated_data.dict())
    return {"message": "Doctor updated successfully"}

# Delete a Doctor
@app.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: str):
    doc_ref = db.collection("doctors").document(doctor_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doc_ref.delete()
    return {"message": "Doctor deleted successfully"}

# Check Slot Availability
@app.get("/doctors/{doctor_id}/slots/{time}")
async def check_slot_availability(doctor_id: str, time: str):
    doc = db.collection("doctors").document(doctor_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_data = doc.to_dict()
    slots = doctor_data.get("available_time_slots", [])

    for slot in slots:
        if slot["time"] == time:
            return {"time": time, "is_booked": slot["is_booked"]}

    raise HTTPException(status_code=404, detail="Time slot not found")

# Book a Time Slot
@app.put("/doctors/{doctor_id}/slots/{time}/book")
async def book_time_slot(doctor_id: str, time: str):
    doc_ref = db.collection("doctors").document(doctor_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor_data = doc.to_dict()
    slots = doctor_data.get("available_time_slots", [])

    for slot in slots:
        if slot["time"] == time:
            if slot["is_booked"]:
                raise HTTPException(status_code=400, detail="Time slot already booked")
            slot["is_booked"] = True
            break
    else:
        raise HTTPException(status_code=404, detail="Time slot not found")

    doc_ref.update({"available_time_slots": slots})
    return {"message": "Time slot booked successfully"}
