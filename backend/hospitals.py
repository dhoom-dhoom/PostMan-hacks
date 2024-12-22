from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Location(BaseModel):
    latitude: float
    longitude: float

class HospitalResponse(BaseModel):
    name: str
    address: str
    rating: Optional[float]
    user_ratings_total: Optional[int]
    photo_url: Optional[str]
    place_id: str

class SearchResponse(BaseModel):
    hospitals: List[HospitalResponse]

@app.post("/search-hospitals/", response_model=SearchResponse)
async def search_hospitals(location: Location):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.photos,places.id",
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
                # Get photo reference if available
                photo_url = None
                if place.get("photos") and len(place["photos"]) > 0:
                    photo_url = f"https://places.googleapis.com/v1/{place['photos'][0]['name']}/media?key={api_key}&maxHeightPx=300&maxWidthPx=400"

                hospital = HospitalResponse(
                    name=place["displayName"]["text"],
                    address=place.get("formattedAddress", "Address not available"),
                    rating=place.get("rating"),
                    user_ratings_total=place.get("userRatingCount"),
                    photo_url=photo_url,
                    place_id=place["id"]
                )
                hospitals.append(hospital)
            
            return SearchResponse(hospitals=hospitals)
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching hospitals: {str(e)}")
        except KeyError as e:
            raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")
