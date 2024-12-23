from dotenv import load_dotenv
import os
from nylas import Client
from nylas.models.auth import CodeExchangeRequest
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

# Load environment variables from .env file
load_dotenv()

# Nylas configuration
nylas_config = {
    "client_id": os.getenv("NYLAS_CLIENT_ID"),
    "callback_uri": "http://localhost:8000/oauth/exchange",
    "api_key": os.getenv("NYLAS_API_KEY"),
    "api_uri": os.getenv("NYLAS_API_URI"),
}

# Initialize the Nylas client
nylas = Client(
    api_key=nylas_config["api_key"],
    api_uri=nylas_config["api_uri"],
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store session data (in-memory for simplicity; replace with persistent storage in production)
session = {}

class EventCreateRequest(BaseModel):
    start_time: int
    end_time: int

@app.get("/")
def home():
    return {"message": "Welcome to the Nylas OAuth Integration"}

@app.get("/nylas/auth")
def nylas_auth():
    auth_url = nylas.auth.url_for_oauth2({
        "client_id": nylas_config["client_id"],
        "redirect_uri": nylas_config["callback_uri"],
    })
    return RedirectResponse(auth_url)

@app.get("/oauth/exchange")
def oauth_exchange(code: str):
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code returned from Nylas")

    try:
        exchange_request = CodeExchangeRequest({
            "redirect_uri": nylas_config["callback_uri"],
            "code": code,
            "client_id": nylas_config["client_id"],
        })
        exchange = nylas.auth.exchange_code_for_token(exchange_request)
        session["grant_id"] = exchange.grant_id
        print(session,"session")

        return {
            "message": f"OAuth2 flow completed successfully for grant ID: {exchange.grant_id}",
            "grant_id": exchange.grant_id,
        }
    except Exception as e:
        logger.error(f"Error during token exchange: {e}")
        raise HTTPException(status_code=500, detail="Failed to exchange authorization code for token")

@app.get("/nylas/primary-calendar")
def primary_calendar():
    
    grant_id = session.get("grant_id")
    if not grant_id:
        raise HTTPException(status_code=400, detail="Grant ID not found in session. Please authenticate first.")

    try:
        calendars, _, _ = nylas.calendars.list(grant_id, {"limit": 5})

        if not calendars:
            raise HTTPException(status_code=404, detail="No calendars found for the authenticated user.")

        for calendar in calendars:
            if calendar.is_primary:
                session["calendar"] = calendar.id
                return {"primary_calendar_id": calendar.id}

        raise HTTPException(status_code=404, detail="No primary calendar found.")
    except Exception as e:
        logger.error(f"Error retrieving calendars: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving calendars: {e}")

@app.get("/nylas/list-events")
def list_events():
    grant_id = session.get("grant_id")
    if not grant_id:
        raise HTTPException(status_code=400, detail="Grant ID not found in session. Please authenticate first.")

    try:
        calendars, _, _ = nylas.calendars.list(grant_id, {"limit": 5})

        if not calendars:
            raise HTTPException(status_code=404, detail="No calendars found for the authenticated user.")

        for calendar in calendars:
            if calendar.is_primary:
                session["calendar"] = calendar.id
                
    except Exception as e:
        logger.error(f"Error retrieving calendars: {e}")
        
    try:
        grant_id = session.get("grant_id")
        if not grant_id:
            raise HTTPException(status_code=400, detail="Grant ID not found in session. Please authenticate first.")
        

        
        calendar_id = session.get("calendar")
        if not calendar_id:
            raise HTTPException(status_code=400, detail="Primary calendar not found. Please set it first.")

        query_params = {"calendar_id": calendar_id, "limit": 5}
        response = nylas.events.list(grant_id, query_params=query_params)

        if not response.data:
            raise HTTPException(status_code=404, detail="No events found for the primary calendar.")

        return response.data
    except Exception as e:
        logger.error(f"Error during list-events: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/nylas/create-event")
def create_event_with_params(event: EventCreateRequest):
    try:
        grant_id = session.get("grant_id")
        calendar_id = session.get("calendar")

        if not grant_id or not calendar_id:
            raise HTTPException(
                status_code=400, 
                detail="Grant ID or calendar not found. Please authenticate and set the primary calendar first."
            )

        request_body = {
            "when": {
                "start_time": event.start_time,
                "end_time": event.end_time,
            },
            "title": "Blocked for Patient",
            "description": "This time slot is reserved for patient-related activities.",
        }

        # Create the event
        nylas_event = nylas.events.create(
            grant_id,
            query_params={"calendar_id": calendar_id},
            request_body=request_body,
        )

        # Convert the event object to a JSON-serializable format
        return JSONResponse(content=nylas_event.as_json(), media_type="application/json")
    except Exception as e:
        logger.error(f"Error during create-event: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# @app.delete("/nylas/delete-event/{event_id}")
# def delete_event(event_id: str):
#     try:
#         grant_id = session.get("grant_id")
#         calendar_id = session.get("calendar")

#         if not grant_id or not calendar_id:
#             raise HTTPException(status_code=400, detail="Grant ID or calendar not found. Please authenticate and set the primary calendar first.")

#         # Use the Nylas API to delete the event
#         response = nylas.events.delete(grant_id, event_id)

#         # Check if the response indicates success
#         if response:
#             return JSONResponse(content={"message": f"Event {event_id} deleted successfully."}, media_type="application/json")
#         else:
#             raise HTTPException(status_code=404, detail="Event not found or could not be deleted.")

#     except Exception as e:
#         logger.error(f"Error during delete-event: {e}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
