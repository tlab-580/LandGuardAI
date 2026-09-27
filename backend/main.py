from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import joblib


# ============================================================
# LANDGUARD AI 2.0 - FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="LANDGUARD AI 2.0",
    description="AI-powered heavy rainfall early warning and inundation prediction system",
    version="2.0.0"
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
# LOAD TRAINED INUNDATION MODEL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "ml"
    / "models"
    / "inundation_risk_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ============================================================
# INPUT STRUCTURE
# ============================================================

class InundationRiskInput(BaseModel):

    rainfall_1h: float
    rainfall_6h: float
    rainfall_24h: float
    rainfall_3d: float
    rainfall_7d: float

    forecast_rainfall_6h: float
    forecast_rainfall_24h: float
    forecast_rainfall_7d: float

    soil_moisture: float
    elevation: float
    slope: float
    distance_to_river: float
    drainage_density: float


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "project": "LANDGUARD AI 2.0",
        "status": "running",
        "message": "Heavy Rainfall and Inundation Intelligence System is online"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model": "inundation_risk_model",
        "model_loaded": True,
        "version": "2.0.0"
    }


# ============================================================
# INUNDATION RISK PREDICTION
# ============================================================

@app.post("/predict-inundation-risk")
def predict_inundation_risk(data: InundationRiskInput):

    # --------------------------------------------------------
    # Prepare model input
    # --------------------------------------------------------

    input_data = pd.DataFrame([{
        "rainfall_1h": data.rainfall_1h,
        "rainfall_6h": data.rainfall_6h,
        "rainfall_24h": data.rainfall_24h,
        "rainfall_3d": data.rainfall_3d,
        "rainfall_7d": data.rainfall_7d,

        "forecast_rainfall_6h": data.forecast_rainfall_6h,
        "forecast_rainfall_24h": data.forecast_rainfall_24h,
        "forecast_rainfall_7d": data.forecast_rainfall_7d,

        "soil_moisture": data.soil_moisture,
        "elevation": data.elevation,
        "slope": data.slope,
        "distance_to_river": data.distance_to_river,
        "drainage_density": data.drainage_density
    }])


    # --------------------------------------------------------
    # Predict risk
    # --------------------------------------------------------

    prediction = model.predict(input_data)[0]


    # --------------------------------------------------------
    # Prediction probabilities
    # --------------------------------------------------------

    probabilities = model.predict_proba(input_data)[0]

    classes = model.classes_

    class_probabilities = {
        risk_class: round(
            float(probability) * 100,
            2
        )
        for risk_class, probability
        in zip(classes, probabilities)
    }


    # --------------------------------------------------------
    # Model confidence
    # --------------------------------------------------------

    confidence = max(probabilities) * 100


    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    feature_importance = dict(
        zip(
            input_data.columns,
            model.feature_importances_
        )
    )

    top_features = sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]


    top_contributing_features = [
        {
            "feature": feature,
            "importance": round(
                float(importance) * 100,
                2
            )
        }
        for feature, importance in top_features
    ]


    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {

        "risk_level": prediction,

        "confidence": round(
            float(confidence),
            2
        ),

        "probabilities": class_probabilities,

        "top_contributing_features":
            top_contributing_features,

        "inputs": data.model_dump()
    }