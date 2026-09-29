# 🌧️ LandGuard AI 2.0

### AI-Powered Heavy Rainfall, Inundation Forecasting & Disaster Intelligence System

> **Predict the hazard. Map the impact. Prioritize the response.**

LandGuard AI 2.0 is an AI-powered disaster intelligence platform designed to support **heavy rainfall early warning, inundation risk assessment, satellite-based change detection, geospatial monitoring, and disaster-response prioritization**.

The system combines meteorological forecast data, machine-learning-based risk prediction, Sentinel-1 SAR analysis, GIS visualization, and impact assessment into a unified disaster-management dashboard.

---

## 🚨 Problem

Heavy rainfall can rapidly trigger:

- 🌊 Urban and rural inundation
- 🛣️ Road and transport disruption
- 🏠 Community and infrastructure exposure
- ⛰️ Terrain-related hazards
- ⚠️ Difficulties in timely emergency response

Traditional monitoring systems often rely on individual data sources and may not provide a unified view of **forecast rainfall + hazard risk + spatial impact**.

LandGuard AI 2.0 addresses this challenge by integrating multiple information sources into a single decision-support platform.

---

## 💡 Solution

LandGuard AI 2.0 follows the pipeline:

```text
Satellite + Weather + NWP
            ↓
       Data Fusion
            ↓
 Heavy Rainfall Forecast
            ↓
  Inundation Risk Prediction
            ↓
 Probability + Confidence
            ↓
        GIS Risk Map
            ↓
 Villages + Roads + Assets
            ↓
     Impact Assessment
            ↓
 Response Prioritization
            ↓
       Early Warning
```

### Core Workflow

**Sense → Predict → Map → Assess → Prioritize → Warn → Respond**

---

# ✨ Key Features

## 🌦️ Real-Time Meteorological Data

The platform retrieves live meteorological information including:

- Temperature
- Relative humidity
- Rainfall
- Precipitation
- Wind speed
- Soil moisture
- Weather conditions

The dashboard can use **Open-Meteo / ECMWF IFS** meteorological data when the backend provider is unavailable.

---

## 📅 15-Day Numerical Weather Prediction

LandGuard AI 2.0 uses **ECMWF IFS numerical weather prediction data** for a 15-day meteorological outlook.

The system displays:

- Daily rainfall
- Maximum temperature
- Minimum temperature
- Precipitation hours
- Forecast source and model

This forecast provides the meteorological input used by the downstream hazard-analysis pipeline.

---

## 🤖 AI-Based Inundation Risk Prediction

A machine-learning model evaluates environmental inputs to estimate inundation-risk conditions.

Current model inputs include:

```text
Rainfall
Soil Moisture
Slope Angle
Elevation
NDVI
```

The model produces risk probabilities for:

- 🔴 High
- 🟠 Moderate
- 🟢 Low

The dashboard presents the corresponding AI confidence/probability to support scenario analysis.

---

## 📊 7-Day AI Hazard Forecast

Meteorological rainfall forecasts are passed through the AI prediction pipeline to produce a **7-day hazard forecast**.

For each forecast day, the dashboard provides:

- Forecast rainfall
- High-risk probability
- Moderate-risk probability
- Low-risk probability
- Risk classification

This allows users to inspect the evolution of hazard conditions over the upcoming week.

---

## 🛰️ Sentinel-1 SAR Inundation Candidate Detection

LandGuard AI 2.0 integrates **Sentinel-1 Synthetic Aperture Radar (SAR)** imagery for change detection.

The SAR workflow compares:

```text
Pre-event Sentinel-1 SAR
          ↓
Backscatter Comparison
          ↓
Post-event Sentinel-1 SAR
          ↓
Change Detection
          ↓
Potential Inundation Candidates
```

The current implementation calculates:

- Pre-event acquisition
- Post-event acquisition
- Time gap
- Detection threshold
- Valid pixels
- Candidate pixels
- Candidate coverage
- Candidate area

### Important

The SAR output is currently a **potential inundation candidate mask**, not a fully validated flood boundary product.

---

## 🗺️ GIS Monitoring

The dashboard provides a geospatial monitoring interface for visualizing the disaster scenario.

The GIS layer is intended to help identify:

- Potentially affected regions
- Hazard zones
- Infrastructure exposure
- Roads
- Settlements
- Other response-relevant locations

---

## 🔗 Integrated Hazard Index

LandGuard AI 2.0 combines multiple evidence sources into an integrated prototype hazard index.

Current components:

```text
Current AI Risk
      +
7-Day Forecast Risk
      +
Sentinel-1 Candidate Evidence
      ↓
Integrated Hazard Index
```

Current prototype weighting:

```text
AI Current Risk       = 50%
Forecast Risk         = 30%
SAR Evidence          = 20%
```

Hazard bands:

```text
75+     → VERY HIGH
50–74   → HIGH
25–49   → MODERATE
0–24    → LOW
```

### ⚠️ Important Note

The integrated index is a **prototype evidence-fusion score** and should not be interpreted as a calibrated probability of flooding.

The weights and thresholds require validation against historical disaster events and field observations before operational deployment.

---

# 🧠 AI Architecture

```text
                ┌─────────────────────┐
                │ Meteorological Data │
                │  Weather + NWP      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Data Processing   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   ML Risk Model     │
                └──────────┬──────────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
          7-Day Risk Forecast   Current Risk
                  │                 │
                  └────────┬────────┘
                           ▼
                ┌─────────────────────┐
                │ Sentinel-1 SAR      │
                │ Change Detection    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Integrated Hazard   │
                │      Index          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ GIS + Impact        │
                │ Assessment          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Early Warning &     │
                │ Decision Support    │
                └─────────────────────┘
```

---

# 🛠️ Technology Stack

## Frontend

- React
- Vite
- JavaScript
- React Leaflet
- Leaflet
- Recharts
- CSS

## Backend

- Python
- FastAPI
- REST APIs
- Uvicorn

## Machine Learning

- Python
- Scikit-learn
- Pickle model serialization
- Feature-based risk prediction

## Satellite / Remote Sensing

- Sentinel-1 SAR
- Copernicus Data Space Ecosystem
- SAR backscatter change detection

## Weather / NWP

- Open-Meteo
- ECMWF IFS
- Meteorological forecast data

## Deployment

- **Frontend:** Vercel
- **Backend:** Render
- **Source Control:** GitHub

---

# 📁 Project Structure

```text
LANDGUARD-AI/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   │
│   └── services/
│       ├── __init__.py
│       ├── rainfall_service.py
│       ├── satellite_service.py
│       ├── sar_inundation_service.py
│       └── integrated_risk_service.py
│
├── data/
│   ├── legacy_landslide_training_data.csv
│   └── rainfall_inundation_training_data.csv
│
├── frontend/
│   ├── .env
│   ├── package.json
│   ├── vite.config.js
│   │
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
│
├── ml/
│   ├── create_dataset.py
│   ├── train_model.py
│   ├── predict.py
│   │
│   └── models/
│       ├── legacy_landslide_risk_model.pkl
│       └── inundation_risk_model.pkl
│
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

---

# 🔌 API Endpoints

The FastAPI backend currently exposes endpoints including:

```text
GET  /
GET  /health
GET  /weather-config-status
GET  /current-weather
GET  /meteorological-forecast
GET  /rainfall-forecast
GET  /satellite-inundation
GET  /satellite-inundation-map

POST /predict-inundation-risk

GET  /forecast-7days
GET  /integrated-risk
```

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "model": "inundation_risk_model",
  "model_loaded": true,
  "version": "2.0.0"
}
```

---

# 📡 Data Sources

LandGuard AI 2.0 is designed around multiple disaster-intelligence data sources:

| Data Source | Purpose |
|---|---|
| ECMWF IFS | Numerical weather prediction |
| Open-Meteo | Meteorological data access |
| Sentinel-1 SAR | Surface/backscatter change detection |
| Copernicus Data Space | Sentinel satellite data access |
| ML Model | Hazard-risk prediction |
| GIS Data | Spatial monitoring and impact assessment |

---

# 📈 Example SAR Analysis

A representative Sentinel-1 processing result from the prototype:

```text
Candidate Coverage : 13.04%
Candidate Area     : 14.4699 km²
Threshold          : -3 dB
Time Gap           : 5.01 days
Valid Pixels       : 44,472
Candidate Pixels   : 5,798
```

These values demonstrate the current SAR change-detection workflow for a test region.

---

# 🚀 Running Locally

## 1. Clone the Repository

```bash
git clone https://github.com/tlab-580/LandGuardAI.git
cd LandGuardAI
```

---

## 2. Create Python Environment

```bash
python -m venv venv
```

### Windows

```bash
source venv/Scripts/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

or:

```bash
pip install -r backend/requirements.txt
```

---

## 4. Configure Environment Variables

Create:

```text
backend/.env
```

Store required API credentials/configuration there.

**Do not commit secrets to GitHub.**

The repository uses `.gitignore` to prevent sensitive environment files from being committed.

---

## 5. Start FastAPI Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 6. Start Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server will provide the local frontend URL.

---

# 🏗️ Build Frontend for Production

```bash
cd frontend
npm run build
```

The production files are generated in:

```text
frontend/dist/
```

---

# ☁️ Deployment

## Frontend

The React frontend is deployed through **Vercel**.

## Backend

The FastAPI backend is deployed through **Render**.

### Live Application

**Frontend:**  
https://landguardai-dun.vercel.app/

**Backend:**  
https://landguardai-uah8.onrender.com/

---

# 🌍 Intended Use

LandGuard AI 2.0 is designed as a **disaster-management decision-support prototype** for applications such as:

- District disaster management
- Heavy-rainfall monitoring
- Inundation-risk screening
- Emergency planning
- Infrastructure monitoring
- Community warning systems
- GIS-based disaster intelligence
- Post-event satellite assessment

The platform can be extended for use by:

- District administrations
- Disaster Management Authorities
- Emergency response teams
- Infrastructure departments
- Researchers
- Local communities

---

# 🔮 Future Enhancements

The current system provides a foundation for a more comprehensive disaster-intelligence platform.

Planned enhancements include:

### 📡 Radar Integration

Integration of high-frequency weather-radar observations for improved short-term rainfall monitoring.

### ⏱️ 6–24 Hour Nowcasting

High-frequency observational and radar data can be incorporated to support:

```text
6-hour
12-hour
24-hour
```

short-horizon predictions.

### 🌊 Improved Inundation Mapping

Future versions can incorporate:

- DEM-based hydrological modelling
- Drainage networks
- River/water-level observations
- Historical flood masks
- Higher-resolution satellite imagery

### 🧠 Advanced ML Models

The prediction pipeline can be expanded using:

- Gradient boosting
- Random Forest
- XGBoost
- Temporal models
- LSTM/GRU
- Spatiotemporal deep learning
- Ensemble forecasting

### 🎯 Impact-Based Warning

Future versions can generate warnings based on:

```text
Hazard
   +
Population Exposure
   +
Infrastructure Exposure
   +
Accessibility
   +
Critical Facilities
```

to prioritize response actions.

---

# ⚠️ Current Limitations

LandGuard AI 2.0 is currently a **prototype research/hackathon system**.

Important limitations:

1. The integrated hazard index is an evidence-fusion score and is not a calibrated flood probability.

2. Sentinel-1 processing currently identifies potential inundation candidates rather than producing a fully validated flood map.

3. The 7-day AI forecast currently uses meteorological rainfall forecast inputs while current soil-moisture context is used for the prediction scenario.

4. High-frequency radar/observational data integration for operational 6–24 hour nowcasting is not yet implemented.

5. The model and integrated scoring system require validation using historical events, field observations, and larger geographically diverse datasets before operational deployment.

---

# 🎯 Vision

The long-term goal of LandGuard AI is to create an integrated disaster-intelligence platform that transforms raw environmental data into actionable information.

```text
Raw Data
   ↓
Intelligence
   ↓
Risk
   ↓
Impact
   ↓
Priority
   ↓
Action
```

**LandGuard AI 2.0 aims to move disaster management from reactive response toward data-driven, predictive decision support.**

---

# 👩‍💻 Project

**LandGuard AI 2.0**

AI-Powered Heavy Rainfall, Inundation Forecasting & Disaster Intelligence System

### Project Theme

**Disaster Management + Artificial Intelligence + Remote Sensing + GIS + Weather Intelligence**

---

# 📜 License

This project is intended for educational, research, prototype, and hackathon purposes.

A production deployment should undergo appropriate validation, calibration, reliability testing, data-quality assessment, and disaster-management authority review before being used for real-world emergency decisions.

---

# ⭐ Acknowledgement

Built as an AI/ML and geospatial disaster-management prototype integrating:

**Artificial Intelligence • Machine Learning • Numerical Weather Prediction • Remote Sensing • SAR • GIS • Disaster Intelligence**
