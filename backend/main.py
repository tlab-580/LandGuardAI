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
class ForecastInput(BaseModel):
    rainfall_forecast: list[float]
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
@app.post("/forecast-7days")
def forecast_7days(data: ForecastInput):

    forecast_results = []

    current_soil_moisture = data.soil_moisture
    cumulative_rainfall = 0

    for day, rainfall in enumerate(data.rainfall_forecast, start=1):

        # Update cumulative rainfall
        cumulative_rainfall += rainfall

        # Estimate future soil moisture
        current_soil_moisture = (
            current_soil_moisture
            + (rainfall * 0.08)
            - 2
        )

        # Keep soil moisture between 0 and 100
        current_soil_moisture = max(
            0,
            min(100, current_soil_moisture)
        )

        # Prepare model input
        input_data = pd.DataFrame([{
            "rainfall_24h": rainfall,
            "rainfall_7d": cumulative_rainfall,
            "soil_moisture": current_soil_moisture,
            "slope_angle": data.slope_angle,
            "elevation": data.elevation,
            "ndvi": data.ndvi
        }])

        # Predict risk
        prediction = model.predict(input_data)[0]

        probabilities = model.predict_proba(input_data)[0]
        classes = model.classes_

        confidence = probabilities[
            list(classes).index(prediction)
        ]

        forecast_results.append({
            "day": day,
            "rainfall": round(rainfall, 2),
            "soil_moisture": round(
                current_soil_moisture,
                2
            ),
            "risk_level": prediction,
            "risk_probability": round(
                float(confidence) * 100,
                2
            )
        })

    return {
        "forecast_days": 7,
        "forecast": forecast_results
    }