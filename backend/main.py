
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services.rainfall_service import (
    generate_rainfall_scenario,
    generate_meteorological_forecast,
    generate_current_weather
)

from backend.services.satellite_service import (
    get_sentinel1_statistics,
    get_sentinel1_change_detection,
)

from backend.services.sar_inundation_service import (
    get_sentinel1_inundation_map
)

from backend.services.integrated_risk_service import (
    calculate_integrated_hazard
)

from pathlib import Path
import pandas as pd
import joblib


# ============================================================
# LANDGUARD AI 2.0 - FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="LANDGUARD AI 2.0",
    description=(
        "AI-powered heavy rainfall early warning "
        "and inundation prediction system"
    ),
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

        "project":
            "LANDGUARD AI 2.0",

        "status":
            "running",

        "message":
            (
                "Heavy Rainfall and Inundation "
                "Intelligence System is online"
            )
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "model":
            "inundation_risk_model",

        "model_loaded":
            True,

        "version":
            "2.0.0"
    }


# ============================================================
# SENTINEL-1 AGGREGATED SATELLITE OBSERVATION
# ============================================================

@app.get("/satellite-inundation")
def satellite_inundation(
    days_back: int = 10,
    min_gap_days: int = 3
):

    if days_back < 5:

        raise HTTPException(
            status_code=400,
            detail="days_back must be at least 5."
        )

    if min_gap_days < 1:

        raise HTTPException(
            status_code=400,
            detail="min_gap_days must be at least 1."
        )

    try:

        satellite_data = (
            get_sentinel1_change_detection(
                days_back=days_back,
                min_gap_days=min_gap_days
            )
        )

        return satellite_data

    except Exception as error:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                "Sentinel-1 SAR change detection failed: "
                f"{str(error)}"
            )
        )


# ============================================================
# SENTINEL-1 PIXEL-LEVEL INUNDATION MAP
# ============================================================

@app.get("/satellite-inundation-map")
def satellite_inundation_map(
    days_back: int = 30,
    min_gap_days: int = 5,
    threshold_db: float = -3.0
):

    if days_back < 5:

        raise HTTPException(
            status_code=400,
            detail="days_back must be at least 5."
        )

    if min_gap_days < 1:

        raise HTTPException(
            status_code=400,
            detail="min_gap_days must be at least 1."
        )

    if threshold_db > 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "threshold_db should normally be "
                "0 or a negative value."
            )
        )

    try:

        satellite_map = (
            get_sentinel1_inundation_map(
                days_back=days_back,
                min_gap_days=min_gap_days,
                threshold_db=threshold_db
            )
        )

        return satellite_map

    except Exception as error:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                "Sentinel-1 pixel-level inundation "
                "mapping failed: "
                f"{str(error)}"
            )
        )


# ============================================================
# RAINFALL SCENARIO FORECAST SERVICE
# ============================================================

@app.get("/rainfall-forecast")
def rainfall_forecast(
    base_rainfall: float = 100,
    days: int = 7
):

    """
    Returns an AI-generated rainfall scenario.

    This is a scenario generator and is not the
    live meteorological forecast service.
    """

    if days < 1 or days > 30:

        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 30"
        )

    if base_rainfall < 0:

        raise HTTPException(
            status_code=400,
            detail="base_rainfall cannot be negative"
        )

    forecast = generate_rainfall_scenario(
        base_rainfall=base_rainfall,
        days=days
    )

    return {

        "status":
            "success",

        "source":
            "AI Scenario",

        "forecast_type":
            "AI rainfall scenario outlook",

        "forecast_days":
            days,

        "forecast":
            forecast
    }


# ============================================================
# REAL METEOROLOGICAL FORECAST
# ============================================================

@app.get("/meteorological-forecast")
def meteorological_forecast(
    latitude: float = 26.1445,
    longitude: float = 91.7362,
    days: int = 15
):

    """
    Returns real numerical weather prediction data
    using the ECMWF IFS model through Open-Meteo.
    """

    if days < 1 or days > 15:

        raise HTTPException(
            status_code=400,
            detail=(
                "days must be between 1 and 15 "
                "for the ECMWF forecast."
            )
        )

    if latitude < -90 or latitude > 90:

        raise HTTPException(
            status_code=400,
            detail=(
                "latitude must be between -90 and 90."
            )
        )

    if longitude < -180 or longitude > 180:

        raise HTTPException(
            status_code=400,
            detail=(
                "longitude must be between -180 and 180."
            )
        )

    try:

        result = generate_meteorological_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days
        )

        return {

            "status":
                "success",

            "source":
                "ECMWF IFS",

            "provider":
                "Open-Meteo",

            "forecast_type":
                "Numerical Weather Prediction",

            "forecast_days":
                days,

            "location":
                result["location"],

            "forecast":
                result["forecast"]
        }

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=(
                "Meteorological forecast service error: "
                f"{str(error)}"
            )
        )


# ============================================================
# CURRENT METEOROLOGICAL DATA
# ============================================================

@app.get("/current-weather")
def current_weather(
    latitude: float = 26.1445,
    longitude: float = 91.7362
):

    """
    Returns current meteorological conditions
    for the selected location.
    """

    if not -90 <= latitude <= 90:

        raise HTTPException(
            status_code=400,
            detail=(
                "Latitude must be between -90 and 90."
            )
        )

    if not -180 <= longitude <= 180:

        raise HTTPException(
            status_code=400,
            detail=(
                "Longitude must be between -180 and 180."
            )
        )

    try:

        weather = generate_current_weather(
            latitude,
            longitude
        )

        return {

            "status":
                "success",

            **weather
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# INUNDATION RISK PREDICTION
# ============================================================

@app.post("/predict-inundation-risk")
def predict_inundation_risk(
    data: InundationRiskInput
):

    # --------------------------------------------------------
    # PREPARE MODEL INPUT
    # --------------------------------------------------------

    input_data = pd.DataFrame([{

        "rainfall_1h":
            data.rainfall_1h,

        "rainfall_6h":
            data.rainfall_6h,

        "rainfall_24h":
            data.rainfall_24h,

        "rainfall_3d":
            data.rainfall_3d,

        "rainfall_7d":
            data.rainfall_7d,

        "forecast_rainfall_6h":
            data.forecast_rainfall_6h,

        "forecast_rainfall_24h":
            data.forecast_rainfall_24h,

        "forecast_rainfall_7d":
            data.forecast_rainfall_7d,

        "soil_moisture":
            data.soil_moisture,

        "elevation":
            data.elevation,

        "slope":
            data.slope,

        "distance_to_river":
            data.distance_to_river,

        "drainage_density":
            data.drainage_density

    }])


    # --------------------------------------------------------
    # PREDICT RISK
    # --------------------------------------------------------

    prediction = model.predict(
        input_data
    )[0]


    # --------------------------------------------------------
    # PREDICTION PROBABILITIES
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        input_data
    )[0]

    classes = model.classes_

    class_probabilities = {

        risk_class:
            round(
                float(probability) * 100,
                2
            )

        for risk_class, probability
        in zip(
            classes,
            probabilities
        )
    }


    # --------------------------------------------------------
    # MODEL CONFIDENCE
    # --------------------------------------------------------

    confidence = (
        max(probabilities)
        * 100
    )


    # --------------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------------

    feature_importance = dict(

        zip(
            input_data.columns,
            model.feature_importances_
        )
    )

    top_features = sorted(

        feature_importance.items(),

        key=lambda x:
            x[1],

        reverse=True

    )[:5]


    top_contributing_features = [

        {

            "feature":
                feature,

            "importance":
                round(
                    float(importance) * 100,
                    2
                )
        }

        for feature, importance in top_features
    ]


    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "risk_level":
            prediction,

        "confidence":
            round(
                float(confidence),
                2
            ),

        "probabilities":
            class_probabilities,

        "top_contributing_features":
            top_contributing_features,

        "inputs":
            data.model_dump()
    }


# ============================================================
# 7-DAY AI RAINFALL & INUNDATION FORECAST
# ============================================================

@app.post("/forecast-7days")
def forecast_7days(
    data: dict
):

    # --------------------------------------------------------
    # READ RAINFALL FORECAST
    # --------------------------------------------------------

    rainfall_forecast = data.get(
        "rainfall_forecast",
        []
    )

    if not rainfall_forecast:

        return {

            "error":
                "rainfall_forecast is required."
        }

    if len(rainfall_forecast) != 7:

        return {

            "error":
                (
                    "Exactly 7 rainfall forecast "
                    "values are required."
                )
        }


    # --------------------------------------------------------
    # ENVIRONMENTAL PARAMETERS
    # --------------------------------------------------------

    soil_moisture = float(
        data.get(
            "soil_moisture",
            85
        )
    )

    elevation = float(
        data.get(
            "elevation",
            100
        )
    )

    slope = float(
        data.get(
            "slope",
            5
        )
    )

    distance_to_river = float(
        data.get(
            "distance_to_river",
            0.3
        )
    )

    drainage_density = float(
        data.get(
            "drainage_density",
            0.25
        )
    )


    # --------------------------------------------------------
    # GENERATE DAILY PREDICTIONS
    # --------------------------------------------------------

    results = []

    previous_rainfall = 0


    for day in range(7):

        rainfall = float(
            rainfall_forecast[day]
        )


        # ----------------------------------------------------
        # DERIVED RAINFALL WINDOWS
        # ----------------------------------------------------

        rainfall_1h = (
            rainfall * 0.30
        )

        rainfall_6h = (
            rainfall * 0.60
        )

        rainfall_24h = (
            rainfall
        )

        rainfall_3d = (
            previous_rainfall
            + rainfall
        )

        rainfall_7d = (
            rainfall_3d
            + rainfall * 1.5
        )


        # ----------------------------------------------------
        # FORECAST RAINFALL FEATURES
        # ----------------------------------------------------

        forecast_rainfall_6h = (
            rainfall * 0.40
        )

        forecast_rainfall_24h = (
            rainfall
        )

        forecast_rainfall_7d = (
            rainfall * 2.0
        )


        # ----------------------------------------------------
        # PREPARE ML INPUT
        # ----------------------------------------------------

        input_data = pd.DataFrame([{

            "rainfall_1h":
                rainfall_1h,

            "rainfall_6h":
                rainfall_6h,

            "rainfall_24h":
                rainfall_24h,

            "rainfall_3d":
                rainfall_3d,

            "rainfall_7d":
                rainfall_7d,

            "forecast_rainfall_6h":
                forecast_rainfall_6h,

            "forecast_rainfall_24h":
                forecast_rainfall_24h,

            "forecast_rainfall_7d":
                forecast_rainfall_7d,

            "soil_moisture":
                soil_moisture,

            "elevation":
                elevation,

            "slope":
                slope,

            "distance_to_river":
                distance_to_river,

            "drainage_density":
                drainage_density

        }])


        # ----------------------------------------------------
        # AI PREDICTION
        # ----------------------------------------------------

        prediction = model.predict(
            input_data
        )[0]


        # ----------------------------------------------------
        # PREDICTION PROBABILITIES
        # ----------------------------------------------------

        probabilities = model.predict_proba(
            input_data
        )[0]

        class_probabilities = dict(

            zip(
                model.classes_,
                probabilities
            )
        )


        # ----------------------------------------------------
        # MODEL CONFIDENCE
        # ----------------------------------------------------

        confidence = (
            max(probabilities)
            * 100
        )


        # ----------------------------------------------------
        # HIGH-RISK PROBABILITY
        # ----------------------------------------------------

        high_probability = (
            class_probabilities.get(
                "High",
                0
            ) * 100
        )


        # ----------------------------------------------------
        # MODERATE PROBABILITY
        # ----------------------------------------------------

        moderate_probability = (
            class_probabilities.get(
                "Moderate",
                0
            ) * 100
        )


        # ----------------------------------------------------
        # LOW PROBABILITY
        # ----------------------------------------------------

        low_probability = (
            class_probabilities.get(
                "Low",
                0
            ) * 100
        )


        # ----------------------------------------------------
        # STORE RESULT
        # ----------------------------------------------------

        results.append({

            "day":
                day + 1,

            "date":
                f"Forecast Day {day + 1}",

            "rainfall":
                round(
                    rainfall,
                    2
                ),

            "soil_moisture":
                round(
                    soil_moisture,
                    2
                ),

            "risk_level":
                prediction,

            "risk_probability":
                round(
                    float(
                        high_probability
                    ),
                    2
                ),

            "confidence":
                round(
                    float(
                        confidence
                    ),
                    2
                ),

            "probabilities": {

                "High":
                    round(
                        float(
                            high_probability
                        ),
                        2
                    ),

                "Moderate":
                    round(
                        float(
                            moderate_probability
                        ),
                        2
                    ),

                "Low":
                    round(
                        float(
                            low_probability
                        ),
                        2
                    )
            }
        })


        previous_rainfall = rainfall


    # --------------------------------------------------------
    # RETURN COMPLETE FORECAST
    # --------------------------------------------------------

    return {

        "forecast_type":
            "AI rainfall scenario outlook",

        "forecast_days":
            7,

        "forecast":
            results
    }

# ============================================================
# INTEGRATED HAZARD FUSION
# ============================================================

@app.post("/integrated-risk")
def integrated_risk(
    ai_current_high_probability: float,
    forecast_high_probability: float,
    satellite_candidate_percent: float,
):

    """
    Combines the current AI high-risk probability,
    peak 7-day forecast high-risk probability, and
    Sentinel-1 candidate coverage into an explainable
    Integrated Hazard Index.

    IMPORTANT:
    The resulting index is not a calibrated probability
    of flooding. Fusion weights and hazard bands require
    historical/event-based validation before operational use.
    """

    if not 0 <= ai_current_high_probability <= 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "ai_current_high_probability must be "
                "between 0 and 100."
            )
        )

    if not 0 <= forecast_high_probability <= 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "forecast_high_probability must be "
                "between 0 and 100."
            )
        )

    if not 0 <= satellite_candidate_percent <= 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "satellite_candidate_percent must be "
                "between 0 and 100."
            )
        )

    try:

        fusion_result = calculate_integrated_hazard(
            ai_current_high_probability=(
                ai_current_high_probability
            ),

            forecast_high_probability=(
                forecast_high_probability
            ),

            satellite_candidate_percent=(
                satellite_candidate_percent
            ),
        )

        return {

            "status":
                "success",

            "system":
                "LANDGUARD AI 2.0",

            "assessment_type":
                "INTEGRATED HAZARD INDEX",

            "result":
                fusion_result
        }

    except Exception as error:

        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                "Integrated hazard fusion failed: "
                f"{str(error)}"
            )
        )

