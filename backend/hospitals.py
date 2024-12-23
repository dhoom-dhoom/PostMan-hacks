# hospitals.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx

class Location(BaseModel):
    latitude: float
    longitude: float

class HospitalResponse(BaseModel):
    name: str
    address: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    opening_hours: Optional[dict] = None

class SearchResponse(BaseModel):
    hospitals: List[HospitalResponse]

# Create a FastAPI instance for hospitals
hospital_app = FastAPI()

hospital_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust based on your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@hospital_app.post("/search-hospitals/", response_model=SearchResponse)
async def search_hospitals(location: Location):
    api_key = "AIzaSyCTXX53Z7JgUVvMW4Cxy3wrpJt7rByKghg"  # Replace with your actual Google Places API key
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    params = {
        "key": api_key,
        "location": f"{location.latitude},{location.longitude}",
        "radius": 5000,  # Radius in meters
        "type": "hospital"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                error_detail = response.json().get("error_message", "Unknown error")
                raise HTTPException(status_code=response.status_code, detail=f"Google API Error: {error_detail}")
            
            data = response.json()
            hospitals = []
            
            for place in data.get("results", []):
                location_data = place.get("geometry", {}).get("location", {})
                hospital = HospitalResponse(
                    name=place.get("name", "Name not available"),
                    address=place.get("vicinity", "Address not available"),
                    rating=place.get("rating"),
                    user_ratings_total=place.get("user_ratings_total"),
                    latitude=location_data.get("lat"),
                    longitude=location_data.get("lng"),
                    place_id=place.get("place_id"),
                    opening_hours={ 
                        "open_now": place.get("opening_hours", {}).get("open_now", False)
                    } if place.get("opening_hours") else None
                )
                hospitals.append(hospital)
            
            return SearchResponse(hospitals=hospitals)
        
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
