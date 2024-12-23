import React, { useState, useEffect } from "react";
import { GoogleMap, LoadScript, Marker, InfoWindow } from "@react-google-maps/api";
import axios from "axios";

// Define map container style
const containerStyle = {
  width: "100%",
  height: "100vh",
};
const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_API_KEY;

// Wrapper component for loading Google Maps API script
const MapWrapper = ({ children }) => {
  return (
    <LoadScript googleMapsApiKey= {GOOGLE_API_KEY} >
      {children}
    </LoadScript>
  );
};

// HospitalSearch component
const HospitalSearch = () => {
  const [location, setLocation] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedHospital, setSelectedHospital] = useState(null); // To track the selected hospital for InfoWindow

  // Get the current location of the user
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          setError("Unable to retrieve your location.");
        }
      );
    } else {
      setError("Geolocation is not supported by this browser.");
    }
  }, []);

  // Fetch hospitals when location is available
  useEffect(() => {
    if (location) {
      setLoading(true);
      axios
        .post("http://localhost:8000/search-hospitals/", location)
        .then((response) => {
          setHospitals(response.data.hospitals);
        })
        .catch((err) => {
          setError("Error fetching hospitals.");
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [location]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <MapWrapper>
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={location ? { lat: location.latitude, lng: location.longitude } : { lat: 0, lng: 0 }}
        zoom={13}
      >
        {hospitals.map((hospital) => (
          <Marker
            key={hospital.place_id}
            position={{
              lat: hospital.latitude,
              lng: hospital.longitude,
            }}
            onClick={() => setSelectedHospital(hospital)} // Set the selected hospital when the marker is clicked
          >
            {selectedHospital && selectedHospital.place_id === hospital.place_id && ( // Only show InfoWindow for the clicked marker
              <InfoWindow onCloseClick={() => setSelectedHospital(null)}>
                <div>
                  <strong>{hospital.name}</strong>
                  <p>{hospital.address}</p>
                  {hospital.rating && (
                    <p>
                      Rating: {hospital.rating} ({hospital.user_ratings_total} reviews)
                    </p>
                  )}
                  {hospital.opening_hours && hospital.opening_hours.open_now && (
                    <p style={{ color: "green" }}>Open Now</p>
                  )}
                </div>
              </InfoWindow>
            )}
          </Marker>
        ))}
      </GoogleMap>
    </MapWrapper>
  );
};

const App = () => {
  return (
    <div>
      <HospitalSearch />
    </div>
  );
};

export default App;
