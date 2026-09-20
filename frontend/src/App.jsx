import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

function App() {
  // =========================================================
  // ENVIRONMENT INPUTS
  // =========================================================

  const [inputs, setInputs] = useState({
    rainfall_24h: 120,
    rainfall_7d: 450,
    soil_moisture: 82,
    slope_angle: 42,
    elevation: 1200,
    ndvi: 0.35,
  });

  // =========================================================
  // CURRENT 24-HOUR PREDICTION
  // =========================================================

  const [result, setResult] = useState(null);

  // =========================================================
  // 7-DAY FORECAST
  // =========================================================

  const [forecast, setForecast] = useState([]);
  const [forecastLoading, setForecastLoading] = useState(false);

  // =========================================================
  // GENERAL STATE
  // =========================================================

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // =========================================================
  // HANDLE INPUT CHANGES
  // =========================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setInputs({
      ...inputs,
      [name]: Number(value),
    });
  };

  // =========================================================
  // CURRENT AI RISK PREDICTION
  // =========================================================

  const predictRisk = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/predict-risk`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(inputs),
        }
      );

      if (!response.ok) {
        throw new Error("Prediction request failed");
      }

      const resultData = await response.json();

      setResult(resultData);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to LANDGUARD AI backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // 7-DAY FORECAST
  // =========================================================

  const getSevenDayForecast = async (event) => {
    // Prevent accidental form submission/page reload
    if (event) {
      event.preventDefault();
    }

    setForecastLoading(true);
    setError("");

    try {
      // -------------------------------------------------------
      // STEP 1: GET LIVE WEATHER FORECAST
      // -------------------------------------------------------

      const weatherResponse = await fetch(
        `${import.meta.env.VITE_API_URL}/weather-forecast`
      );

      if (!weatherResponse.ok) {
        throw new Error("Unable to fetch weather forecast");
      }

      const weatherData = await weatherResponse.json();

      // -------------------------------------------------------
      // STEP 2: EXTRACT RAINFALL + DATES
      // -------------------------------------------------------

      const rainfallForecast = weatherData.forecast.map(
        (day) => day.rainfall
      );

      const forecastDates = weatherData.forecast.map(
        (day) => day.date
      );

      // -------------------------------------------------------
      // STEP 3: SEND WEATHER DATA TO AI FORECAST MODEL
      // -------------------------------------------------------

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/forecast-7days`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            rainfall_forecast: rainfallForecast,
            forecast_dates: forecastDates,
            soil_moisture: inputs.soil_moisture,
            slope_angle: inputs.slope_angle,
            elevation: inputs.elevation,
            ndvi: inputs.ndvi,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to generate 7-day forecast");
      }

      const data = await response.json();

      setForecast(data.forecast);
    } catch (err) {
      console.error("7-Day Forecast Error:", err);

      setError(err.message);
    } finally {
      setForecastLoading(false);
    }
  };

  // =========================================================
  // CURRENT RISK
  // =========================================================

  const riskLevel = result?.risk_level || "Not Analyzed";
  const confidence = result?.confidence || 0;

  const riskClass =
    riskLevel === "High"
      ? "risk-high"
      : riskLevel === "Moderate"
      ? "risk-moderate"
      : riskLevel === "Low"
      ? "risk-low"
      : "risk-none";

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        <div className="logo">

          <div className="logo-icon">
            🏔️
          </div>

          <div>
            <h2>LANDGUARD</h2>

            <span>
              AI DISASTER INTELLIGENCE
            </span>
          </div>

        </div>

        <nav>

          <a className="active">
            📊 Dashboard
          </a>

          <a>
            🗺️ Risk Map
          </a>

          <a>
            📈 Predictions
          </a>

          <a>
            ⚠️ Alerts
          </a>

          <a>
            📷 Citizen Reports
          </a>

          <a>
            🤖 AI Copilot
          </a>

        </nav>

        <div className="system-status">

          <span className="status-dot"></span>

          <div>

            <strong>
              System Online
            </strong>

            <small>
              AI services operational
            </small>

          </div>

        </div>

      </aside>


      {/* =====================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="main-content">

        {/* ===================================================
            HEADER
        ==================================================== */}

        <header className="topbar">

          <div>

            <p className="eyebrow">
              DISASTER MANAGEMENT PLATFORM
            </p>

            <h1>
              LANDGUARD AI
            </h1>

            <p className="subtitle">
              Explainable landslide & cascading disaster
              early-warning system
            </p>

          </div>

          <div className="header-actions">

            <button
              type="button"
              className="location-btn"
            >
              📍 North Eastern Region
            </button>

            <button
              type="button"
              className="profile-btn"
            >
              TS
            </button>

          </div>

        </header>


        {/* ===================================================
            CURRENT RISK BANNER
        ==================================================== */}

        <section
          className={`risk-banner ${riskClass}`}
        >

          <div>

            <span className="section-label">
              AI RISK ASSESSMENT
            </span>

            <h2>
              {riskLevel.toUpperCase()}
            </h2>

            <p>
              {result
                ? `AI model confidence: ${confidence}%`
                : "Run an AI prediction to analyze current environmental conditions."
              }
            </p>

          </div>

          <div className="risk-score">

            <strong>
              {result ? confidence : "--"}
            </strong>

            <span>
              {result ? "%" : ""}
            </span>

            <small>
              Model Confidence
            </small>

          </div>

        </section>


        {/* ===================================================
            ENVIRONMENTAL INPUTS
        ==================================================== */}

        <section className="panel input-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                ENVIRONMENTAL INPUTS
              </span>

              <h2>
                AI Risk Analysis
              </h2>

            </div>

            <button
              type="button"
              className="predict-btn"
              onClick={predictRisk}
              disabled={loading}
            >
              {loading
                ? "Analyzing..."
                : "Run AI Prediction →"
              }
            </button>

          </div>


          <div className="input-grid">

            <div className="input-card">

              <label>
                Rainfall — 24 Hours (mm)
              </label>

              <input
                type="number"
                name="rainfall_24h"
                value={inputs.rainfall_24h}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Rainfall — 7 Days (mm)
              </label>

              <input
                type="number"
                name="rainfall_7d"
                value={inputs.rainfall_7d}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Soil Moisture (%)
              </label>

              <input
                type="number"
                name="soil_moisture"
                value={inputs.soil_moisture}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Slope Angle (°)
              </label>

              <input
                type="number"
                name="slope_angle"
                value={inputs.slope_angle}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Elevation (m)
              </label>

              <input
                type="number"
                name="elevation"
                value={inputs.elevation}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Vegetation Index — NDVI
              </label>

              <input
                type="number"
                step="0.01"
                name="ndvi"
                value={inputs.ndvi}
                onChange={handleChange}
              />

            </div>

          </div>


          {error && (

            <div className="error-message">
              ⚠️ {error}
            </div>

          )}

        </section>


        {/* ===================================================
            7-DAY FORECAST
        ==================================================== */}

        <section className="panel forecast-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                7-DAY AI FORECAST
              </span>

              <h2>
                Landslide Risk Forecast
              </h2>

              <p>
                Predictive risk assessment for the next
                seven days
              </p>

              <p className="weather-source">
                🟢 LIVE WEATHER DATA • Open-Meteo • Guwahati
              </p>

            </div>


            <button
              type="button"
              className="forecast-button"
              onClick={getSevenDayForecast}
              disabled={forecastLoading}
            >

              {forecastLoading
                ? "Generating..."
                : "Generate 7-Day Forecast →"
              }

            </button>

          </div>


          {/* =================================================
              RAINFALL + RISK TREND
          ================================================== */}

          {forecast.length > 0 && (

            <div className="forecast-chart">

              <div className="chart-title">

                <span className="section-label">
                  RAINFALL & RISK TREND
                </span>

                <p>
                  7-day weather-driven landslide risk outlook
                </p>

              </div>


              <ResponsiveContainer
                width="100%"
                height={320}
              >

                <LineChart
                  data={forecast}
                  margin={{
                    top: 20,
                    right: 20,
                    left: 0,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="date"
                  />

                  <YAxis />

                  <Tooltip />

                  <Legend />

                  <Line
                    type="monotone"
                    dataKey="rainfall"
                    name="Rainfall (mm)"
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />

                  <Line
                    type="monotone"
                    dataKey="risk_probability"
                    name="Risk Probability (%)"
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>

          )}


          {/* =================================================
              FORECAST RESULTS
          ================================================== */}

          {forecast.length > 0 && (

            <div className="forecast-grid">

              {forecast.map((day) => (

                <div
                  className={`forecast-card risk-${day.risk_level.toLowerCase()}`}
                  key={day.day}
                >

                  <span className="forecast-day">
                    DAY {day.day}
                  </span>

                  <span className="forecast-date">
                    {day.date}
                  </span>

                  <h3>
                    {day.risk_level}
                  </h3>

                  <p className="forecast-rainfall">
                    🌧️ Rainfall:
                    <strong>
                      {" "}
                      {day.rainfall} mm
                    </strong>
                  </p>

                  <p>
                    💧 Soil Moisture:
                    <strong>
                      {" "}
                      {day.soil_moisture}%
                    </strong>
                  </p>

                  <p>
                    📊 Risk Probability:
                    <strong>
                      {" "}
                      {day.risk_probability}%
                    </strong>
                  </p>

                </div>

              ))}

            </div>

          )}


          {/* =================================================
              BEFORE FORECAST IS GENERATED
          ================================================== */}

          {forecast.length === 0 && !forecastLoading && (

            <div className="forecast-empty">

              <div className="forecast-empty-icon">
                🔮
              </div>

              <h3>
                7-Day Forecast Ready
              </h3>

              <p>
                Click "Generate 7-Day Forecast" to
                analyze landslide risk for the next
                seven days.
              </p>

            </div>

          )}


          {/* =================================================
              RISK TREND CHART
          ================================================== */}

          {forecast.length > 0 && (

            <div className="forecast-chart">

              <div className="chart-header">

                <div>

                  <span className="section-label">
                    RISK TREND
                  </span>

                  <h3>
                    7-Day Risk Probability
                  </h3>

                  <p>
                    AI-predicted landslide risk probability
                    across the forecast period
                  </p>

                </div>

              </div>


              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <LineChart
                  data={forecast}
                  margin={{
                    top: 10,
                    right: 20,
                    left: 10,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="day"
                    tickFormatter={(day) =>
                      `Day ${day}`
                    }
                  />

                  <YAxis
                    domain={[0, 100]}
                    label={{
                      value: "Risk Probability (%)",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />

                  <Tooltip
                    formatter={(value) => [
                      `${value}%`,
                      "Risk Probability",
                    ]}
                    labelFormatter={(day) =>
                      `Day ${day}`
                    }
                  />

                  <Line
                    type="monotone"
                    dataKey="risk_probability"
                    strokeWidth={3}
                    dot={{ r: 5 }}
                    activeDot={{ r: 7 }}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>

          )}

        </section>


        {/* ===================================================
            STATISTICS
        ==================================================== */}

        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-top">

              <span>
                🌧️
              </span>

              <small>
                RAINFALL
              </small>

            </div>

            <h3>
              {inputs.rainfall_24h} mm
            </h3>

            <p>
              Last 24 hours
            </p>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                💧
              </span>

              <small>
                SOIL MOISTURE
              </small>

            </div>

            <h3>
              {inputs.soil_moisture}%
            </h3>

            <p>
              Current measurement
            </p>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                ⛰️
              </span>

              <small>
                SLOPE
              </small>

            </div>

            <h3>
              {inputs.slope_angle}°
            </h3>

            <p>
              Terrain inclination
            </p>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                🤖
              </span>

              <small>
                AI RESULT
              </small>

            </div>

            <h3>
              {result ? riskLevel : "--"}
            </h3>

            <p>
              Predicted risk
            </p>

          </div>

        </section>


        {/* ===================================================
            MAP + CURRENT PREDICTION
        ==================================================== */}

        <section className="dashboard-grid">

          {/* =================================================
              GIS MAP
          ================================================== */}

          <div className="panel map-panel">

            <div className="panel-header">

              <div>

                <span className="section-label">
                  GIS MONITORING
                </span>

                <h2>
                  Regional Risk Map
                </h2>

              </div>

              <button
                type="button"
                className="view-btn"
              >
                View Full Map →
              </button>

            </div>


            {/* =================================================
                IMPROVED 7-DAY OUTLOOK SUMMARY
            ================================================== */}

            {forecast.length > 0 && (() => {

              const peakDay = forecast.reduce(
                (max, day) =>
                  day.risk_probability >
                  max.risk_probability
                    ? day
                    : max
              );

              return (

                <div className="forecast-summary">
<div className="summary-card">
  <span className="summary-label">FORECAST STATUS</span>
  <strong className="summary-status">
    {forecast.length === 7 ? "7 DAYS READY" : "NOT READY"}
  </strong>
  <small>Forecast data available for risk monitoring</small>
</div>

                  {/* PEAK RISK */}

                  <div className="summary-card">

                    <span className="summary-label">
                      PEAK RISK
                    </span>

                    <strong
                      className={`summary-risk risk-${peakDay.risk_level.toLowerCase()}`}
                    >
                      {peakDay.risk_level}
                    </strong>

                    <small>
                      Highest predicted risk level
                    </small>

                  </div>


                  {/* PEAK PROBABILITY */}

                  <div className="summary-card">

                    <span className="summary-label">
                      PEAK PROBABILITY
                    </span>

                    <strong>
                      {peakDay.risk_probability}%
                    </strong>

                    <small>
                      Maximum predicted probability
                    </small>

                  </div>


                  {/* PEAK DAY */}

                  <div className="summary-card">

                    <span className="summary-label">
                      PEAK DAY
                    </span>

                    <strong>
                      Day {peakDay.day}
                    </strong>

                    <small>
                      Highest-risk forecast day
                    </small>

                  </div>

                </div>

              );

            })()}


            <div className="map-container">

              <MapContainer
                center={[26.2, 92.9]}
                zoom={6}
                scrollWheelZoom={true}
                style={{
                  height: "450px",
                  width: "100%",
                }}
              >

                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />


                {/* GUWAHATI - CURRENT AI RISK */}

                <CircleMarker
                  center={[26.1445, 91.7362]}
                  radius={20}
                  pathOptions={{
  color:
    riskLevel === "High"
      ? "#dc2626"
      : riskLevel === "Moderate"
      ? "#f59e0b"
      : riskLevel === "Low"
      ? "#16a34a"
      : "#64748b",
  fillColor:
    riskLevel === "High"
      ? "#dc2626"
      : riskLevel === "Moderate"
      ? "#f59e0b"
      : riskLevel === "Low"
      ? "#16a34a"
      : "#64748b",
  fillOpacity: 0.65,
  weight: 3,
}}
                >

                  <Popup>

                    <strong>
                      HIGH RISK ZONE
                    </strong>

                    <br />

                    Guwahati Region

                    <br />

                    Heavy rainfall detected

                  </Popup>

                </CircleMarker>


                {/* SHILLONG */}

                <CircleMarker
                  center={[25.5788, 91.8933]}
                  radius={14}
                  pathOptions={{
                    color: "orange",
                    fillColor: "orange",
                    fillOpacity: 0.6,
                  }}
                >

                  <Popup>

                    <strong>
                      MODERATE RISK
                    </strong>

                    <br />

                    Shillong Region

                  </Popup>

                </CircleMarker>


                {/* ASSAM */}

                <CircleMarker
                  center={[27.4728, 94.9120]}
                  radius={12}
                  pathOptions={{
                    color: "green",
                    fillColor: "green",
                    fillOpacity: 0.6,
                  }}
                >

                  <Popup>

                    <strong>
                      LOW RISK
                    </strong>

                    <br />

                    Assam Region

                  </Popup>

                </CircleMarker>

              </MapContainer>

            </div>

          </div>


          {/* =================================================
              CURRENT AI PREDICTION
          ================================================== */}

          <div className="panel prediction-panel">

            <div className="panel-header">

              <div>

                <span className="section-label">
                  AI FORECAST
                </span>

                <h2>
                  Risk Prediction
                </h2>

              </div>

            </div>


            <div className="prediction-result">

              <span className="prediction-label">
                CURRENT AI PREDICTION
              </span>

              <strong>
                {riskLevel}
              </strong>

              <p>
                Confidence:{" "}
                {result
                  ? `${confidence}%`
                  : "--"
                }
              </p>

            </div>


            {/* 6 HOURS */}

            <div className="prediction-item">

              <div>

                <strong>
                  6 Hours
                </strong>

                <span>
                  Forecast
                </span>

              </div>

              <div className="prediction-bar">

                <div
                  style={{
                    width: "58%",
                  }}
                ></div>

              </div>

              <b>
                58%
              </b>

            </div>


            {/* 12 HOURS */}

            <div className="prediction-item">

              <div>

                <strong>
                  12 Hours
                </strong>

                <span>
                  Forecast
                </span>

              </div>

              <div className="prediction-bar">

                <div
                  style={{
                    width: "71%",
                  }}
                ></div>

              </div>

              <b>
                71%
              </b>

            </div>


            {/* 24 HOURS */}

            <div className="prediction-item">

              <div>

                <strong>
                  24 Hours
                </strong>

                <span>
                  Forecast
                </span>

              </div>

              <div className="prediction-bar">

                <div
                  style={{
                    width: "82%",
                  }}
                ></div>

              </div>

              <b>
                82%
              </b>

            </div>

          </div>

        </section>


        {/* ===================================================
            CASCADING DISASTER + COPILOT
        ==================================================== */}

        <section className="bottom-grid">

          {/* =================================================
              CASCADE ANALYSIS
          ================================================== */}

          <div className="panel cascade-panel">

            <div className="panel-header">

              <div>

                <span className="section-label">
                  CASCADE ANALYSIS
                </span>

                <h2>
                  Potential Disaster Chain
                </h2>

              </div>

            </div>


            <div className="cascade-flow">

              {/* HEAVY RAIN */}

              <div className="cascade-node">

                <span>
                  🌧️
                </span>

                <strong>
                  Heavy Rain
                </strong>

                <small>

                  {inputs.rainfall_24h} mm / 24h

                  <br />

                  Status:{" "}

                  <strong>

                    {inputs.rainfall_24h >= 100
                      ? "HIGH"
                      : inputs.rainfall_24h >= 50
                      ? "MODERATE"
                      : "LOW"}

                  </strong>

                </small>

              </div>


              <div className="arrow">
                →
              </div>


              {/* SOIL SATURATION */}

              <div
                className={`cascade-node ${
                  inputs.soil_moisture >= 80
                    ? "danger"
                    : inputs.soil_moisture >= 60
                    ? "warning"
                    : ""
                }`}
              >

                <span>
                  💧
                </span>

                <strong>
                  Soil Saturation
                </strong>

                <small>

                  {inputs.soil_moisture}% moisture

                  <br />

                  Status:{" "}

                  <strong>

                    {inputs.soil_moisture >= 80
                      ? "HIGH"
                      : inputs.soil_moisture >= 60
                      ? "MODERATE"
                      : "LOW"}

                  </strong>

                </small>

              </div>


              <div className="arrow">
                →
              </div>


              {/* LANDSLIDE */}

              <div
                className={`cascade-node ${
                  riskLevel === "High"
                    ? "danger"
                    : riskLevel === "Moderate"
                    ? "warning"
                    : ""
                }`}
              >

                <span>
                  ⛰️
                </span>

                <strong>
                  Landslide
                </strong>

                <small>

                  AI Risk:{" "}

                  <strong>
                    {riskLevel}
                  </strong>

                </small>

              </div>


              <div className="arrow">
                →
              </div>


              {/* ROAD BLOCKAGE */}

              <div
                className={`cascade-node ${
                  riskLevel === "High"
                    ? "danger"
                    : riskLevel === "Moderate"
                    ? "warning"
                    : ""
                }`}
              >

                <span>
                  🛣️
                </span>

                <strong>
                  Road Blockage
                </strong>

                <small>

                  Status:{" "}

                  <strong>

                    {riskLevel === "High"
                      ? "HIGH"
                      : riskLevel === "Moderate"
                      ? "MODERATE"
                      : "LOW"}

                  </strong>

                </small>

              </div>


              <div className="arrow">
                →
              </div>


              {/* FLOOD / INFRASTRUCTURE */}

              <div
                className={`cascade-node ${
                  riskLevel === "High"
                    ? "danger"
                    : riskLevel === "Moderate"
                    ? "warning"
                    : ""
                }`}
              >

                <span>
                  🌊
                </span>

                <strong>
                  Flood / Infrastructure
                </strong>

                <small>

                  Status:{" "}

                  <strong>

                    {riskLevel === "High"
                      ? "HIGH"
                      : riskLevel === "Moderate"
                      ? "MODERATE"
                      : "LOW"}

                  </strong>

                </small>

              </div>

            </div>

          </div>


          {/* =================================================
              AI COPILOT
          ================================================== */}

          <div className="panel copilot-panel">

            <div className="copilot-icon">
              🤖
            </div>

            <div>

              <span className="section-label">
                AI ASSISTANT
              </span>

              <h2>
                Disaster Copilot
              </h2>

              <p>
                Ask about risk levels, affected
                locations, emergency actions,
                and disaster-management
                guidelines.
              </p>

              <button
                type="button"
                className="copilot-btn"
              >
                Open AI Copilot →
              </button>

            </div>

          </div>

        </section>


        {/* ===================================================
            FOOTER
        ==================================================== */}

        <footer>
          LANDGUARD AI • AI-powered disaster
          intelligence platform
        </footer>

      </main>

    </div>
  );
}

export default App;