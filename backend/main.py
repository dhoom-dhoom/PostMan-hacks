# main.py
from fastapi import FastAPI
from hospitals import hospital_app  # Import the FastAPI app from hospitals.py

# Create the main FastAPI app
app = FastAPI()

# Mount the hospital app under the /hospitals route
app.mount("/hospitals", hospital_app)  # This will mount the hospital app under the /hospitals endpoint

