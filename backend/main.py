from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import joblib


# ============================================================
# LANDGUARD AI - FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="LANDGUARD AI",
    description="AI-powered landslide early warning and disaster intelligence system",
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

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


# ============================================================
# LOAD TRAINED ML MODEL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

model = joblib.load(
    BASE_DIR / "ml" / "models" / "landslide_risk_model.pkl"
)


# ============================================================
# INPUT STRUCTURES
# ============================================================

class RiskInput(BaseModel):
    rainfall_24h: float
    rainfall_7d: float
    soil_moisture: float
    slope_angle: float
    elevation: float
    ndvi: float


class ForecastInput(BaseModel):
    rainfall_forecast: list
    forecast_dates: list
    soil_moisture: float
    slope_angle: float
    elevation: float
    ndvi: float


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "project": "LANDGUARD AI",
        "status": "running",
        "message": "Landslide Intelligence System is online"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "loaded"
    }


# ============================================================
# CURRENT RISK PREDICTION
# ============================================================

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
        "confidence": round(
            float(confidence) * 100,
            2
        ),
        "inputs": data.model_dump()
    }


# ============================================================
# 7-DAY LANDSLIDE FORECAST
# ============================================================

@app.post("/forecast-7days")
def forecast_7days(data: ForecastInput):

    forecast_results = []

    current_soil_moisture = data.soil_moisture

    cumulative_rainfall = 0

    for day, rainfall in enumerate(
        data.rainfall_forecast,
        start=1
    ):

        # ----------------------------------------------------
        # Update cumulative rainfall
        # ----------------------------------------------------

        cumulative_rainfall += rainfall


        # ----------------------------------------------------
        # Simple soil moisture simulation
        # ----------------------------------------------------

        current_soil_moisture = (
            current_soil_moisture
            + (rainfall * 0.08)
            - 2
        )


        current_soil_moisture = max(
            0,
            min(
                100,
                current_soil_moisture
            )
        )


        # ----------------------------------------------------
        # Prepare ML input
        # ----------------------------------------------------

        input_data = pd.DataFrame([{
            "rainfall_24h": rainfall,
            "rainfall_7d": cumulative_rainfall,
            "soil_moisture": current_soil_moisture,
            "slope_angle": data.slope_angle,
            "elevation": data.elevation,
            "ndvi": data.ndvi
        }])


        # ----------------------------------------------------
        # Predict risk
        # ----------------------------------------------------

        prediction = model.predict(
            input_data
        )[0]


        probabilities = model.predict_proba(
            input_data
        )[0]


        classes = model.classes_


        confidence = probabilities[
            list(classes).index(prediction)
        ]


        # ----------------------------------------------------
        # Store forecast result
        # ----------------------------------------------------

        forecast_results.append({
    "day": day,
    "date": data.forecast_dates[day - 1],
    "rainfall": round(rainfall, 2),
    "soil_moisture": round(current_soil_moisture, 2),
    "risk_level": prediction,
    "risk_probability": round(float(confidence) * 100, 2)
})


    # --------------------------------------------------------
    # Return 7-day forecast
    # --------------------------------------------------------

    return {
        "forecast_days": 7,
        "forecast": forecast_results
    }


# ============================================================
# WEATHER FORECAST FEED
# ============================================================

# ============================================================
# WEATHER FORECAST FEED
# ============================================================

@app.get("/weather-forecast")
def weather_forecast():

    from urllib.request import urlopen
    import json

    latitude = 26.1445
    longitude = 91.7362

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&daily=rain_sum"
        "&forecast_days=7"
        "&timezone=auto"
    )

    with urlopen(url, timeout=15) as response:
        weather_data = json.loads(
            response.read().decode("utf-8")
        )

    rainfall = weather_data["daily"]["rain_sum"]
    dates = weather_data["daily"]["time"]

    forecast = []

    for day, (date, rain) in enumerate(
        zip(dates, rainfall),
        start=1
    ):
        forecast.append({
            "day": day,
            "date": date,
            "rainfall": round(float(rain or 0), 2)
        })

    return {
        "location": "Guwahati",
        "source": "Open-Meteo Weather Forecast",
        "forecast": forecast
    }