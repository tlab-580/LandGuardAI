# 🌍 LandGuard AI

### AI-Powered Landslide Early Warning & Disaster Intelligence System

LandGuard AI is an **AI-powered disaster intelligence platform** designed to support **landslide risk assessment, early warning, geospatial visualization, and disaster preparedness**.

The system analyzes multiple environmental and terrain factors such as **rainfall, soil moisture, slope angle, elevation, and vegetation (NDVI)** to estimate landslide risk and present the results through an interactive web dashboard.

> **Turning environmental data into actionable disaster intelligence.**

---

## 🚨 Problem Statement

Landslides are a major disaster risk in India's vulnerable hilly regions, particularly during periods of intense and prolonged rainfall.

Traditional warning approaches may rely heavily on individual indicators such as rainfall thresholds and may not provide sufficiently localized and continuous risk assessment.

LandGuard AI addresses this challenge by combining multiple environmental parameters with machine learning to provide:

* 🧠 AI-based landslide risk classification
* 🗺️ Interactive geospatial risk visualization
* 📊 Multi-factor environmental analysis
* 🔮 7-day predictive risk forecasting framework
* ⚠️ Early-warning oriented risk information
* 🚑 Disaster preparedness and response support

---

# ✨ Key Features

## 🧠 AI-Based Risk Prediction

LandGuard AI uses a machine-learning classification model to analyze:

* 🌧️ Rainfall in the last 24 hours
* 🌧️ Cumulative 7-day rainfall
* 💧 Soil moisture
* ⛰️ Slope angle
* 📍 Elevation
* 🌱 NDVI / vegetation information

The model classifies the estimated landslide risk as:

* 🟢 **Low**
* 🟡 **Moderate**
* 🔴 **High**

---

## 🗺️ Interactive Risk Map

The frontend provides an interactive map using:

* React
* Leaflet
* OpenStreetMap

This allows risk information to be visualized geographically and provides a foundation for future regional risk-monitoring systems.

---

## 🔮 7-Day Forecasting

LandGuard AI includes a forecasting workflow designed to evaluate changing landslide risk over a **7-day period**.

The current prototype uses forecast rainfall inputs and combines them with terrain and environmental parameters.

Future versions can integrate real-time weather APIs and continuously updated environmental data.

---

## 📊 Disaster Intelligence Dashboard

The dashboard provides a centralized interface for:

* Current risk assessment
* Environmental inputs
* Risk classification
* Prediction confidence
* Geographic visualization
* Forecast information
* Disaster intelligence

---

## 🤖 Disaster Copilot

The project also includes a planned AI-assisted disaster intelligence interface designed to help users understand:

* Risk levels
* Potentially affected locations
* Emergency actions
* Disaster-management guidance
* Preparedness recommendations

---

# 🏗️ System Architecture

```text
                    ENVIRONMENTAL DATA
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Rainfall       Soil Moisture     Terrain Data
          │                │                │
          └────────────────┼────────────────┘
                           │
                         NDVI
                           │
                           ▼
                ┌─────────────────────┐
                │   Data Processing   │
                │ & Feature Handling  │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   ML Risk Model     │
                │   Scikit-learn      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Risk Classification │
                │ Low / Moderate/High│
                └──────────┬──────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Risk Dashboard              Interactive Map
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
                 Disaster Intelligence
```

---

# 🔄 Prediction Workflow

```text
User / Data Source
       │
       ▼
Environmental Parameters
       │
       ├── Rainfall 24h
       ├── Rainfall 7d
       ├── Soil Moisture
       ├── Slope Angle
       ├── Elevation
       └── NDVI
       │
       ▼
FastAPI Backend
       │
       ▼
Machine Learning Model
       │
       ▼
Risk Prediction
       │
       ├── Low
       ├── Moderate
       └── High
       │
       ▼
React Dashboard
       │
       ▼
Map + Risk Insights + Forecast
```

---

# 🛠️ Technology Stack

### Frontend

* React.js
* JavaScript / JSX
* Vite
* Leaflet
* OpenStreetMap
* CSS

### Backend

* Python
* FastAPI
* Uvicorn
* REST API

### AI / Machine Learning

* Scikit-learn
* Pandas
* NumPy
* Machine Learning Classification

### Data

* CSV-based landslide training dataset
* Rainfall
* Soil moisture
* Slope angle
* Elevation
* NDVI

### Development Tools

* Visual Studio Code
* Git
* GitHub

### Deployment

* Vercel — Frontend
* Render — Backend

---

# 📁 Project Structure

```text
LandGuardAI/
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
│
├── ml/
│   ├── create_dataset.py
│   ├── train_model.py
│   ├── predict.py
│   └── models/
│       └── landslide_risk_model.pkl
│
├── data/
│   └── landslide_training_data.csv
│
├── .gitignore
└── README.md
```

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/tlab-580/LandGuardAI.git
cd LandGuardAI
```

---

# 🐍 Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn pandas numpy scikit-learn
```

Run the backend:

```bash
uvicorn main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# ⚛️ Frontend Setup

Open another terminal and navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The frontend will usually be available at:

```text
http://localhost:5173
```

---

# 🔌 API

## Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "model": "loaded"
}
```

---

## Landslide Risk Prediction

```http
POST /predict-risk
```

Example input:

```json
{
  "rainfall_24h": 120,
  "rainfall_7d": 450,
  "soil_moisture": 82,
  "slope_angle": 42,
  "elevation": 1200,
  "ndvi": 0.35
}
```

Example output:

```json
{
  "risk_level": "High",
  "confidence": 0.95
}
```

---

# 📈 Machine Learning Model

The prototype uses a supervised machine-learning classification approach.

### Input Features

| Feature       | Description                                |
| ------------- | ------------------------------------------ |
| Rainfall 24h  | Rainfall received during the last 24 hours |
| Rainfall 7d   | Cumulative rainfall over seven days        |
| Soil Moisture | Estimated soil saturation/moisture         |
| Slope Angle   | Terrain slope                              |
| Elevation     | Elevation above sea level                  |
| NDVI          | Vegetation index                           |

### Output

```text
Low
Moderate
High
```

### Prototype Model Performance

The current training experiment achieved approximately:

**93.5% overall accuracy**

Class-level performance varies because the available prototype dataset is not evenly distributed across risk categories. Further validation using larger, geographically diverse datasets is required before operational deployment.

---

# 🌧️ 7-Day Forecasting

LandGuard AI is designed to move beyond single-time-point risk assessment toward continuous predictive monitoring.

The forecasting pipeline can use:

```text
Weather Forecast
      +
Soil Moisture
      +
Terrain
      +
Vegetation
      +
Historical Landslide Data
      ↓
AI Risk Assessment
      ↓
7-Day Risk Forecast
```

The current prototype demonstrates this workflow using forecast rainfall inputs.

---

# 🌐 Live Deployment

### 🚀 Frontend

https://landguardai-dun.vercel.app/

### ⚡ Backend API

https://landguardai-uah8.onrender.com

### 📚 API Documentation

```text
https://landguardai-uah8.onrender.com/docs
```

### 💻 GitHub Repository

https://github.com/tlab-580/LandGuardAI

---

# 🎯 Impact

LandGuard AI is designed to support multiple stakeholders.

### 🏛️ Disaster Management Authorities

* Location-aware risk information
* Preparedness support
* Resource prioritization

### 🚑 Emergency Response Teams

* Identify potentially vulnerable areas
* Support inspection and response planning
* Improve situational awareness

### 👨‍👩‍👧‍👦 Communities

* Earlier awareness of changing risk conditions
* Disaster preparedness information
* Risk communication

### 🛣️ Infrastructure Stakeholders

* Visibility into potentially vulnerable roads and infrastructure
* Support for preventive planning

---

# 💡 Innovation

LandGuard AI combines multiple environmental factors instead of relying only on a single rainfall threshold.

### Key innovation areas:

* Multi-factor AI risk assessment
* Interactive GIS visualization
* Machine-learning-based classification
* 7-day forecasting framework
* Disaster intelligence dashboard
* Scalable API-based architecture

---

# 🔮 Future Scope

The project can be expanded through:

* 🌦️ Real-time weather API integration
* 🛰️ Satellite imagery integration
* 🌍 Advanced GIS and terrain datasets
* 💧 IoT soil-moisture sensors
* 📡 Continuous real-time monitoring
* 🔮 Improved 7-day predictive forecasting
* 📱 SMS and mobile application alerts
* 📧 Email notifications
* 🚨 Automated emergency-response workflows
* 🧠 Advanced deep-learning models
* 📚 Larger historical landslide datasets
* 🗺️ Expansion to additional landslide-prone regions

---

# ⚠️ Limitations

This repository represents a prototype and research-oriented implementation.

Current limitations include:

* Prototype dataset size and geographic coverage
* Dependence on the quality of input environmental data
* Forecasting currently uses simulated/demo rainfall inputs
* No direct IoT sensor integration yet
* No operational emergency-alert infrastructure
* Model performance requires validation on larger real-world datasets

**LandGuard AI should not be treated as a replacement for official disaster warnings or professional geological assessment.**

---

# 🧪 Future Development Pipeline

```text
Current Prototype
       │
       ▼
Real-Time Weather APIs
       │
       ▼
Satellite & GIS Data
       │
       ▼
IoT Environmental Sensors
       │
       ▼
Continuous Data Pipeline
       │
       ▼
Advanced ML / Deep Learning
       │
       ▼
Localized 7-Day Forecasting
       │
       ▼
Automated Alerts
       │
       ▼
Disaster Response Integration
```

---

# 👩‍💻 Project

**LandGuard AI**

Developed as an AI/ML and disaster-intelligence project focused on improving landslide risk assessment and preparedness.

### Repository

https://github.com/tlab-580/LandGuardAI

### Live Demo

https://landguardai-dun.vercel.app/

---

# 📜 References

* Geological Survey of India — Landslide Hazard and Landslide Early Warning research
* ISRO — Landslide Atlas of India
* OpenStreetMap
* Scikit-learn documentation
* FastAPI documentation
* React documentation
* Leaflet documentation

---

## ⭐ If you find this project useful

Consider giving the repository a ⭐ and following the project for future updates.

---

### LANDGUARD AI

**AI-driven risk assessment • GIS visualization • Disaster intelligence • Early-warning support**
