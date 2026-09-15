from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import joblib

app = FastAPI(
    title="LANDGUARD AI",
    description="AI-powered landslide early warning and disaster intelligence system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:5173",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5175",
    "https://landguardai-dun.vercel.app"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load trained ML model
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

model = joblib.load(
    BASE_DIR / "ml" / "models" / "landslide_risk_model.pkl"
)


# Input structure
class RiskInput(BaseModel):
    rainfall_24h: float
    rainfall_7d: float
    soil_moisture: float
    slope_angle: float
    elevation: float
    ndvi: float


@app.get("/")
def home():
    return {
        "project": "LANDGUARD AI",
        "status": "running",
        "message": "Landslide Intelligence System is online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "loaded"
    }


@app.post("/predict-risk")
def predict_risk(data: RiskInput):

    input_data = pd.DataFrame([{
        "rainfall_24h": data.rainfall_24h,
        "rainfall_7d": data.rainfall_7d,
        "soil_moisture": data.soil_moisture,
        "slope_angle": data.slope_angle,
        "elevation": data.elevation,
        "ndvi": data.ndvi
    }])

    prediction = model.predict(input_data)[0]

    probabilities = model.predict_proba(input_data)[0]

    classes = model.classes_

    confidence = probabilities[
        list(classes).index(prediction)
    ]

    return {
        "risk_level": prediction,
        "confidence": round(float(confidence) * 100, 2),
        "inputs": data.model_dump()
    }