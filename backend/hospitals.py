from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
from typing import List, Optional
import json

#Input is Location Coordinates
class Location(BaseModel):
    latitude: float
    longitude: float

#Atributes of hospitals
class HospitalResponse(BaseModel):
    name: str
    address: str
    rating: Optional[float]
    user_ratings_total: Optional[int]

#list containing hospitals this is returned 
class SearchResponse(BaseModel):
    hospitals: List[HospitalResponse]

app = FastAPI()

#CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search-hospitals/", response_model=SearchResponse)
async def search_hospitals(location: Location):
    # API key
    api_key = "API KEY"
    
    
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount",
        "Content-Type": "application/json"
    }
    
    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                },
                "radius": 5000.0
            }
        }
    }
    
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            
            
            response.raise_for_status()
            data = response.json()
            
            hospitals = []
            for place in data.get("places", []):
                try:
                    hospital = HospitalResponse(
                        name=place["displayName"]["text"],
                        address=place.get("formattedAddress", "Address not available"),
                        rating=place.get("rating"),
                        user_ratings_total=place.get("userRatingCount")
                    )
                    hospitals.append(hospital)
                except KeyError as e:
                    print(f"Error processing hospital data: {e}")
                    print(f"Problem hospital data: {place}")
            
            return SearchResponse(hospitals=hospitals)
            
        except httpx.HTTPError as e:
            error_msg = f"Error fetching hospitals: {str(e)}"
            print(error_msg)
            print(f"Full error details: {e.__dict__}")
            raise HTTPException(status_code=500, detail=error_msg)

