
import { useState, useEffect } from "react";

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
  ImageOverlay,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";


function App() {

  // =========================================================
  // ENVIRONMENT INPUTS
  // =========================================================

  const [inputs, setInputs] = useState({
    rainfall_1h: 80,
    rainfall_6h: 150,
    rainfall_24h: 250,
    rainfall_3d: 400,
    rainfall_7d: 600,

    forecast_rainfall_6h: 100,
    forecast_rainfall_24h: 200,
    forecast_rainfall_7d: 400,

    soil_moisture: 85,
    elevation: 100,
    slope: 5,
    distance_to_river: 0.3,
    drainage_density: 0.25,
  });


  // =========================================================
  // CURRENT PREDICTION
  // =========================================================

  const [result, setResult] = useState(null);


  // =========================================================
  // 7-DAY AI FORECAST
  // =========================================================

  const [forecast, setForecast] = useState([]);
  const [forecastLoading, setForecastLoading] = useState(false);


  // =========================================================
  // REAL METEOROLOGICAL FORECAST
  // =========================================================

  const [meteorologicalForecast, setMeteorologicalForecast] =
    useState([]);

  const [currentWeather, setCurrentWeather] =
    useState(null);

  const [currentWeatherLoading, setCurrentWeatherLoading] =
    useState(false);

  const [currentWeatherError, setCurrentWeatherError] =
    useState("");

  const [meteorologicalLoading, setMeteorologicalLoading] =
    useState(false);

  const [meteorologicalError, setMeteorologicalError] =
    useState("");


  // =========================================================
  // SATELLITE SAR INUNDATION MAP
  // =========================================================

  const [satelliteData, setSatelliteData] =
    useState(null);

  const [satelliteLoading, setSatelliteLoading] =
    useState(false);

  const [satelliteError, setSatelliteError] =
    useState("");


  // =========================================================
  // INTEGRATED HAZARD FUSION
  // =========================================================

  const [integratedRisk, setIntegratedRisk] =
    useState(null);

  const [integratedRiskLoading, setIntegratedRiskLoading] =
    useState(false);

  const [integratedRiskError, setIntegratedRiskError] =
    useState("");


  // =========================================================
  // GENERAL STATE
  // =========================================================

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


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
  // CURRENT AI SCENARIO RISK PREDICTION
  // =========================================================

  const predictRisk = async () => {

    setLoading(true);
    setError("");

    try {

      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/predict-inundation-risk`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(inputs),
        }
      );


      if (!response.ok) {

        const errorText =
          await response.text();

        throw new Error(
          `Prediction request failed: ${errorText}`
        );

      }


      const resultData =
        await response.json();


      console.log(
        "Current LandGuard AI scenario prediction:",
        resultData
      );


      setResult(resultData);


    } catch (err) {

      console.error(
        "Current prediction error:",
        err
      );


      setError(
        err.message ||
        "Unable to connect to LANDGUARD AI backend."
      );


    } finally {

      setLoading(false);

    }

  };


  // =========================================================
  // REAL METEOROLOGICAL FORECAST
  // =========================================================

  const fetchMeteorologicalForecast =
    async () => {

      setMeteorologicalLoading(true);
      setMeteorologicalError("");

      try {

        const latitude = 26.1445;
        const longitude = 91.7362;

        const apiUrl =
          import.meta.env.VITE_API_URL;


        console.log(
          "Meteorological API URL:",
          apiUrl
        );


        if (!apiUrl) {

          throw new Error(
            "VITE_API_URL is not configured."
          );

        }


        const url =
          `${apiUrl}/meteorological-forecast` +
          `?latitude=${latitude}` +
          `&longitude=${longitude}` +
          `&days=15`;


        console.log(
          "Fetching meteorological forecast:",
          url
        );


        const response =
          await fetch(url);


        console.log(
          "Meteorological response status:",
          response.status
        );


        if (!response.ok) {

          const errorText =
            await response.text();

          throw new Error(
            `Meteorological API error ${response.status}: ${errorText}`
          );

        }


        const data =
          await response.json();


        console.log(
          "Meteorological forecast response:",
          data
        );


        if (
          data.status !== "success" ||
          !Array.isArray(data.forecast)
        ) {

          throw new Error(
            "Invalid meteorological forecast response."
          );

        }


        setMeteorologicalForecast(
          data.forecast
        );


        console.log(
          `Loaded ${data.forecast.length} meteorological forecast records.`
        );


      } catch (error) {

        console.error(
          "Meteorological forecast error:",
          error
        );


        setMeteorologicalForecast([]);


        setMeteorologicalError(
          error.message ||
          "Unable to load real meteorological forecast data."
        );


      } finally {

        setMeteorologicalLoading(false);

      }

    };


  // =========================================================
  // CURRENT METEOROLOGICAL DATA
  // =========================================================

  const fetchCurrentWeather =
    async () => {

      setCurrentWeatherLoading(true);
      setCurrentWeatherError("");


      try {

        const latitude = 26.1445;
        const longitude = 91.7362;


        const response =
          await fetch(
            `${import.meta.env.VITE_API_URL}/current-weather?latitude=${latitude}&longitude=${longitude}`
          );


        if (!response.ok) {

          throw new Error(
            "Failed to fetch current weather"
          );

        }


        const data =
          await response.json();


        console.log(
          "Current meteorological data:",
          data
        );


        setCurrentWeather(data);


      } catch (error) {

        console.error(
          "Current weather error:",
          error
        );


        setCurrentWeatherError(
          error.message ||
          "Unable to load current meteorological data."
        );


      } finally {

        setCurrentWeatherLoading(false);

      }

    };


  // =========================================================
  // SENTINEL-1 PIXEL-LEVEL SATELLITE DATA
  //
  // BACKEND:
  // /satellite-inundation-map
  //
  // DATA:
  // Sentinel-1 pre/post VV change mask
  // =========================================================

  const fetchSatelliteData =
    async () => {

      setSatelliteLoading(true);
      setSatelliteError("");


      try {

        const apiUrl =
          import.meta.env.VITE_API_URL;


        if (!apiUrl) {

          throw new Error(
            "VITE_API_URL is not configured."
          );

        }


        const url =
          `${apiUrl}/satellite-inundation-map` +
          `?days_back=30` +
          `&min_gap_days=5` +
          `&threshold_db=-3`;


        console.log(
          "Fetching Sentinel-1 pixel-level inundation map:",
          url
        );


        const response =
          await fetch(url);


        console.log(
          "Sentinel-1 response status:",
          response.status
        );


        if (!response.ok) {

          const errorText =
            await response.text();


          throw new Error(
            `Sentinel-1 API error ${response.status}: ${errorText}`
          );

        }


        const data =
          await response.json();


        console.log(
          "Sentinel-1 pixel-level satellite data:",
          data
        );


        if (
          data.status !== "success" ||
          !data.image?.data ||
          !data.study_area?.bbox
        ) {

          throw new Error(
            "Invalid Sentinel-1 inundation map response."
          );

        }


        setSatelliteData(data);


      } catch (err) {

        console.error(
          "Satellite data error:",
          err
        );


        setSatelliteData(null);


        setSatelliteError(
          err.message ||
          "Unable to retrieve Sentinel-1 satellite observations."
        );


      } finally {

        setSatelliteLoading(false);

      }

    };




  // =========================================================
  // INTEGRATED HAZARD ASSESSMENT
  //
  // Combines:
  // 1. Current AI high-risk probability
  // 2. Peak 7-day AI forecast high-risk probability
  // 3. Sentinel-1 SAR candidate coverage
  // =========================================================

  const fetchIntegratedRisk = async () => {

    if (
      !result ||
      !Array.isArray(forecast) ||
      forecast.length === 0 ||
      !satelliteData
    ) {
      return;
    }

    setIntegratedRiskLoading(true);
    setIntegratedRiskError("");

    try {

      const apiUrl = import.meta.env.VITE_API_URL;

      if (!apiUrl) {
        throw new Error("VITE_API_URL is not configured.");
      }

      // Current AI high-risk probability
      const currentAIHighProbability = Number(
        result?.probabilities?.High ?? 0
      );

      // Peak high-risk probability across the 7-day AI forecast
      const forecastHighProbability = forecast.reduce(
        (maximum, day) =>
          Math.max(
            maximum,
            Number(day?.risk_probability ?? 0)
          ),
        0
      );

      // Sentinel-1 candidate coverage is evidence, not flood probability
      const satelliteCandidatePercent = Number(
        satelliteData?.mask?.potential_inundation_percent ?? 0
      );

      console.log("Integrated Hazard Inputs:", {
        currentAIHighProbability,
        forecastHighProbability,
        satelliteCandidatePercent,
      });

      const url =
        `${apiUrl}/integrated-risk` +
        `?ai_current_high_probability=${encodeURIComponent(
          currentAIHighProbability
        )}` +
        `&forecast_high_probability=${encodeURIComponent(
          forecastHighProbability
        )}` +
        `&satellite_candidate_percent=${encodeURIComponent(
          satelliteCandidatePercent
        )}`;

      const response = await fetch(url, {
        method: "POST",
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Integrated hazard request failed: ${errorText}`
        );
      }

      const data = await response.json();

      console.log("Integrated Hazard Assessment:", data);

      if (data.status !== "success" || !data.result) {
        throw new Error(
          "Invalid integrated hazard response."
        );
      }

      setIntegratedRisk(data.result);

    } catch (err) {

      console.error("Integrated hazard error:", err);

      setIntegratedRisk(null);

      setIntegratedRiskError(
        err.message ||
        "Unable to calculate integrated hazard assessment."
      );

    } finally {
      setIntegratedRiskLoading(false);
    }

  };


  // =========================================================
  // 7-DAY AI INUNDATION FORECAST
  //
  // REAL PIPELINE:
  //
  // ECMWF IFS
  //     ↓
  // Real rainfall forecast
  //     ↓
  // First 7 forecast days
  //     ↓
  // LandGuard AI
  //     ↓
  // Inundation risk
  // =========================================================

  const getSevenDayForecast =
    async (event) => {

      if (event) {
        event.preventDefault();
      }


      setForecastLoading(true);
      setError("");


      try {

        // -----------------------------------------------------
        // CHECK REAL METEOROLOGICAL FORECAST
        // -----------------------------------------------------

        if (
          !Array.isArray(meteorologicalForecast) ||
          meteorologicalForecast.length < 7
        ) {

          throw new Error(
            "Real meteorological forecast data for 7 days is not available yet. Please wait for the forecast to load and try again."
          );

        }


        // -----------------------------------------------------
        // EXTRACT REAL ECMWF RAINFALL
        // -----------------------------------------------------

        const realRainfallForecast =
          meteorologicalForecast
            .slice(0, 7)
            .map(
              (day) =>
                Number(day.rainfall || 0)
            );


        // -----------------------------------------------------
        // USE CURRENT SOIL MOISTURE
        // -----------------------------------------------------

        let currentSoilMoisture =
          Number(
            currentWeather?.soil_moisture ??
            inputs.soil_moisture
          );


        if (
          currentWeather?.soil_moisture != null &&
          currentSoilMoisture <= 1
        ) {

          currentSoilMoisture =
            currentSoilMoisture * 100;

        }


        currentSoilMoisture =
          Math.max(
            0,
            Math.min(
              100,
              currentSoilMoisture
            )
          );


        const currentRainfall =
          Number(
            currentWeather?.rainfall || 0
          );


        console.log(
          "Current weather used by LandGuard AI:",
          {
            rainfall:
              currentRainfall,

            soil_moisture:
              currentSoilMoisture,

            temperature:
              currentWeather?.temperature,

            humidity:
              currentWeather?.relative_humidity,
          }
        );


        // -----------------------------------------------------
        // LOG REAL ECMWF VALUES
        // -----------------------------------------------------

        console.log(
          "ECMWF rainfall used for AI forecast:",
          realRainfallForecast
        );


        // -----------------------------------------------------
        // SEND REAL RAINFALL TO LANDGUARD AI
        // -----------------------------------------------------

        const apiUrl =
          import.meta.env.VITE_API_URL;


        if (!apiUrl) {

          throw new Error(
            "VITE_API_URL is not configured."
          );

        }


        const response =
          await fetch(
            `${apiUrl}/forecast-7days`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",
              },

              body: JSON.stringify({

                rainfall_forecast:
                  realRainfallForecast,

                soil_moisture:
                  currentSoilMoisture,

                elevation:
                  Number(
                    inputs.elevation
                  ),

                slope:
                  Number(
                    inputs.slope
                  ),

                distance_to_river:
                  Number(
                    inputs.distance_to_river
                  ),

                drainage_density:
                  Number(
                    inputs.drainage_density
                  ),

              }),

            }
          );


        // -----------------------------------------------------
        // CHECK BACKEND RESPONSE
        // -----------------------------------------------------

        if (!response.ok) {

          const errorText =
            await response.text();


          throw new Error(
            `Failed to generate 7-day inundation forecast: ${errorText}`
          );

        }


        // -----------------------------------------------------
        // READ AI FORECAST
        // -----------------------------------------------------

        const data =
          await response.json();


        console.log(
          "LandGuard AI 7-day forecast:",
          data
        );


        if (
          !Array.isArray(data.forecast)
        ) {

          throw new Error(
            "Invalid 7-day AI forecast response."
          );

        }


        setForecast(
          data.forecast
        );


      } catch (err) {

        console.error(
          "7-Day Forecast Error:",
          err
        );


        setForecast([]);


        setError(
          err.message ||
          "Unable to generate 7-day inundation forecast."
        );


      } finally {

        setForecastLoading(false);

      }

    };


  // =========================================================
  // LOAD REAL DATA WHEN DASHBOARD STARTS
  // =========================================================

  useEffect(() => {

    fetchMeteorologicalForecast();
    fetchCurrentWeather();
    fetchSatelliteData();

  }, []);




  // =========================================================
  // AUTO-UPDATE INTEGRATED HAZARD ASSESSMENT
  // =========================================================

  useEffect(() => {

    if (
      result &&
      forecast.length > 0 &&
      satelliteData
    ) {
      fetchIntegratedRisk();
    }

  }, [result, forecast, satelliteData]);


  // =========================================================
  // CURRENT RISK
  // =========================================================

  const riskLevel =
    result?.risk_level ||
    "Not Analyzed";


  const confidence =
    result?.confidence ||
    0;


  const riskClass =
    riskLevel === "High"
      ? "risk-high"
      : riskLevel === "Moderate"
      ? "risk-moderate"
      : riskLevel === "Low"
      ? "risk-low"
      : "risk-none";


  // =========================================================
  // DYNAMIC IMPACT ASSESSMENT
  // =========================================================

  const impactStatus =
    riskLevel === "High"
      ? "HIGH PRIORITY"
      : riskLevel === "Moderate"
      ? "MONITOR"
      : riskLevel === "Low"
      ? "LOW PRIORITY"
      : "AWAITING ANALYSIS";


  const impactData = {

    settlements:
      riskLevel === "High"
        ? "High-priority monitoring of vulnerable residential areas is recommended."
        : riskLevel === "Moderate"
        ? "Vulnerable residential areas should be monitored closely."
        : riskLevel === "Low"
        ? "Routine monitoring of residential areas is appropriate."
        : "Run an AI prediction to assess settlement impact.",


    roads:
      riskLevel === "High"
        ? "Potential road connectivity disruption requires immediate assessment."
        : riskLevel === "Moderate"
        ? "Monitor low-lying and flood-prone road segments."
        : riskLevel === "Low"
        ? "No elevated road-disruption signal from the current model."
        : "Run an AI prediction to assess road connectivity.",


    infrastructure:
      riskLevel === "High"
        ? "Prioritize hospitals, schools and emergency facilities for assessment."
        : riskLevel === "Moderate"
        ? "Review vulnerable critical infrastructure locations."
        : riskLevel === "Low"
        ? "Routine preparedness monitoring is recommended."
        : "Run an AI prediction to assess infrastructure impact.",


    response:
      riskLevel === "High"
        ? "Immediate impact assessment and response planning recommended."
        : riskLevel === "Moderate"
        ? "Enhanced monitoring and preparedness are recommended."
        : riskLevel === "Low"
        ? "Continue routine disaster preparedness monitoring."
        : "Awaiting AI risk analysis.",

  };


  // =========================================================
  // IMPACT BADGE CLASS
  // =========================================================

  const impactBadgeClass =
    riskLevel === "High"
      ? "high"
      : riskLevel === "Moderate"
      ? "moderate"
      : riskLevel === "Low"
      ? "low"
      : "pending";


  // =========================================================
  // HELPER: CURRENT SOIL MOISTURE %
  // =========================================================

  const displaySoilMoisture =
    currentWeather?.soil_moisture != null
      ? (
          Number(currentWeather.soil_moisture) <= 1
            ? Number(currentWeather.soil_moisture) * 100
            : Number(currentWeather.soil_moisture)
        ).toFixed(1)
      : inputs.soil_moisture;


  // =========================================================
  // SATELLITE MAP HELPERS
  // =========================================================

  const satelliteBbox =
    satelliteData?.study_area?.bbox ||
    null;


  const satelliteBounds =
    satelliteBbox &&
    satelliteBbox.length === 4

      ? [
          [
            satelliteBbox[1],
            satelliteBbox[0],
          ],
          [
            satelliteBbox[3],
            satelliteBbox[2],
          ],
        ]

      : null;


  const satelliteImageUrl =
    satelliteData?.image?.data

      ? `data:image/png;base64,${satelliteData.image.data}`

      : null;


  const satelliteCandidatePercent =
    satelliteData?.mask?.potential_inundation_percent ??
    null;


  const satelliteCandidateArea =
    satelliteData?.mask?.estimated_candidate_area_km2 ??
    null;


  const satelliteClassification =
    satelliteData?.change_detection?.classification ??
    "NOT AVAILABLE";


  const satelliteActualGap =
    satelliteData?.change_detection?.actual_gap_days ??
    null;


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

            <h2>
              LANDGUARD
            </h2>

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
              LANDGUARD AI 2.0
            </h1>

            <p className="subtitle">
              Heavy rainfall & inundation early-warning
              and disaster intelligence system
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
            CURRENT SCENARIO RISK BANNER
        ==================================================== */}

        <section
          className={`risk-banner ${riskClass}`}
        >

          <div>

            <span className="section-label">
              SCENARIO RISK ASSESSMENT
            </span>

            <p className="risk-context">
              Risk calculated from the manually entered
              rainfall, terrain, and soil conditions.
            </p>

            <h2>
              {riskLevel.toUpperCase()}
            </h2>

            <p>

              {result
                ? `AI model confidence: ${confidence}%`
                : "Run an AI prediction to analyze the manually specified environmental scenario."
              }

            </p>


            {result?.probabilities && (

              <div className="main-risk-probabilities">

                <div className="main-probability-item">

                  <span>
                    🔴 High
                  </span>

                  <strong>
                    {result.probabilities.High ?? 0}%
                  </strong>

                </div>


                <div className="main-probability-item">

                  <span>
                    🟠 Moderate
                  </span>

                  <strong>
                    {result.probabilities.Moderate ?? 0}%
                  </strong>

                </div>


                <div className="main-probability-item">

                  <span>
                    🟢 Low
                  </span>

                  <strong>
                    {result.probabilities.Low ?? 0}%
                  </strong>

                </div>

              </div>

            )}

          </div>


          <div className="risk-score">

            <strong>
              {result
                ? confidence
                : "--"}
            </strong>

            <span>
              {result
                ? "%"
                : ""}
            </span>

            <small>
              Model Confidence
            </small>

          </div>

        </section>


        {/* ===================================================
            REAL METEOROLOGICAL FORECAST
        ==================================================== */}

        <section className="panel meteorological-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                REAL METEOROLOGICAL DATA
              </span>

              <h2>
                🌦️ Meteorological Forecast
              </h2>

              <p>
                Numerical Weather Prediction using
                ECMWF IFS data. Forecast values are obtained
                from a real meteorological forecast model
                rather than a synthetic scenario.
              </p>

            </div>


            <div className="meteorological-source-badge">
              🌍 ECMWF IFS • NWP
            </div>

          </div>


          {meteorologicalLoading && (

            <div className="meteorological-status">
              ⏳ Loading real meteorological forecast...
            </div>

          )}


          {meteorologicalError && (

            <div className="meteorological-error">
              ⚠️ {meteorologicalError}
            </div>

          )}


          {!meteorologicalLoading &&
            !meteorologicalError &&
            meteorologicalForecast.length > 0 && (

              <>

                <div className="meteorological-info">

                  <span>
                    📍 Guwahati, Northeast India
                  </span>

                  <span>
                    📡 Source: ECMWF IFS
                  </span>

                  <span>
                    📊 NWP Forecast
                  </span>

                  <span>
                    📅 {meteorologicalForecast.length}-Day Forecast
                  </span>

                </div>


                <div className="meteorological-grid">

                  {meteorologicalForecast.map(
                    (day) => (

                      <div
                        className="meteorological-card"
                        key={day.day}
                      >

                        <span className="meteo-day">
                          DAY {day.day}
                        </span>

                        <span className="meteo-date">
                          {day.date}
                        </span>


                        <div className="meteo-rainfall">

                          <span>
                            🌧️
                          </span>

                          <strong>
                            {day.rainfall ?? 0} mm
                          </strong>

                        </div>


                        <div className="meteo-details">

                          <div>

                            <span>
                              🌡️ Max
                            </span>

                            <strong>
                              {day.temperature_max ?? "—"}
                              {day.temperature_max != null
                                ? "°C"
                                : ""}
                            </strong>

                          </div>


                          <div>

                            <span>
                              🌡️ Min
                            </span>

                            <strong>
                              {day.temperature_min ?? "—"}
                              {day.temperature_min != null
                                ? "°C"
                                : ""}
                            </strong>

                          </div>


                          <div>

                            <span>
                              🌧️ Rain Hours
                            </span>

                            <strong>
                              {day.precipitation_hours ?? "—"}
                              {day.precipitation_hours != null
                                ? " h"
                                : ""}
                            </strong>

                          </div>

                        </div>


                        <div className="meteo-source">
                          ECMWF IFS • NWP
                        </div>

                      </div>

                    )
                  )}

                </div>

              </>

            )}

        </section>


        {/* ===================================================
            CURRENT METEOROLOGICAL CONDITIONS
        ==================================================== */}

        <section className="panel current-weather-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                🌦️ CURRENT CONDITIONS
              </span>

              <h2>
                Current Meteorological Conditions
              </h2>

              <p>
                Current meteorological data used
                alongside numerical weather prediction.
              </p>

            </div>


            <span className="forecast-badge">
              🌍 CURRENT WEATHER DATA
            </span>

          </div>


          {currentWeatherLoading && (

            <div className="weather-loading">
              Loading current meteorological conditions...
            </div>

          )}


          {currentWeatherError && (

            <div className="weather-error">
              ⚠️ {currentWeatherError}
            </div>

          )}


          {currentWeather &&
            !currentWeatherLoading && (

              <div className="current-weather-grid">

                <div className="weather-card">

                  <span>
                    🌡️
                  </span>

                  <small>
                    Temperature
                  </small>

                  <strong>
                    {currentWeather.temperature ?? "--"} °C
                  </strong>

                </div>


                <div className="weather-card">

                  <span>
                    💧
                  </span>

                  <small>
                    Humidity
                  </small>

                  <strong>
                    {currentWeather.relative_humidity ?? "--"} %
                  </strong>

                </div>


                <div className="weather-card">

                  <span>
                    🌧️
                  </span>

                  <small>
                    Current Rain
                  </small>

                  <strong>
                    {currentWeather.rainfall ?? "--"} mm
                  </strong>

                </div>


                <div className="weather-card">

                  <span>
                    💦
                  </span>

                  <small>
                    Precipitation
                  </small>

                  <strong>
                    {currentWeather.precipitation ?? "--"} mm
                  </strong>

                </div>


                <div className="weather-card">

                  <span>
                    🌬️
                  </span>

                  <small>
                    Wind Speed
                  </small>

                  <strong>
                    {currentWeather.wind_speed ?? "--"} km/h
                  </strong>

                </div>


                <div className="weather-card">

                  <span>
                    🌱
                  </span>

                  <small>
                    Soil Moisture
                  </small>

                  <strong>
                    {displaySoilMoisture} %
                  </strong>

                </div>

              </div>

            )}


          {currentWeather && (

            <div className="weather-source">

              Source: {currentWeather.provider}

              &nbsp; • &nbsp;

              {currentWeather.data_type}

              &nbsp; • &nbsp;

              Updated: {currentWeather.time}

            </div>

          )}

        </section>


        {/* ===================================================
            ENVIRONMENTAL INPUTS
        ==================================================== */}

        <section className="panel input-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                RAINFALL & INUNDATION INPUTS
              </span>

              <h2>
                AI Inundation Risk Analysis
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
                : "Run AI Prediction →"}

            </button>

          </div>


          <div className="input-grid">

            <div className="input-card">

              <label>
                Rainfall — 1 Hour (mm)
              </label>

              <input
                type="number"
                name="rainfall_1h"
                value={inputs.rainfall_1h}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Rainfall — 6 Hours (mm)
              </label>

              <input
                type="number"
                name="rainfall_6h"
                value={inputs.rainfall_6h}
                onChange={handleChange}
              />

            </div>


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
                Rainfall — 3 Days (mm)
              </label>

              <input
                type="number"
                name="rainfall_3d"
                value={inputs.rainfall_3d}
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
                Forecast Rainfall — 6 Hours (mm)
              </label>

              <input
                type="number"
                name="forecast_rainfall_6h"
                value={inputs.forecast_rainfall_6h}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Forecast Rainfall — 24 Hours (mm)
              </label>

              <input
                type="number"
                name="forecast_rainfall_24h"
                value={inputs.forecast_rainfall_24h}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Forecast Rainfall — 7 Days (mm)
              </label>

              <input
                type="number"
                name="forecast_rainfall_7d"
                value={inputs.forecast_rainfall_7d}
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
                Slope (°)
              </label>

              <input
                type="number"
                name="slope"
                value={inputs.slope}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Distance to River (km)
              </label>

              <input
                type="number"
                name="distance_to_river"
                step="0.1"
                value={inputs.distance_to_river}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>
                Drainage Density
              </label>

              <input
                type="number"
                name="drainage_density"
                step="0.01"
                value={inputs.drainage_density}
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
            7-DAY AI FORECAST
        ==================================================== */}

        <section className="panel forecast-panel">

          <div className="panel-header">

            <div>

              <span className="section-label">
                7-DAY AI FORECAST
              </span>

              <h2>
                Inundation Risk Forecast
              </h2>

              <p>
                Predictive risk assessment using
                real ECMWF IFS rainfall input.
              </p>

              <p className="weather-source">

                🌍 ECMWF IFS • REAL NWP RAINFALL INPUT •
                7-DAY INUNDATION OUTLOOK

              </p>

            </div>


            <button
              type="button"
              className="forecast-button"
              onClick={getSevenDayForecast}
              disabled={
                forecastLoading ||
                meteorologicalForecast.length < 7
              }
            >

              {forecastLoading
                ? "Generating..."
                : meteorologicalForecast.length < 7
                ? "Waiting for NWP Data..."
                : "Generate 7-Day Inundation Forecast →"}

            </button>

          </div>


          {/* =================================================
              METEOROLOGICAL → AI DATA PIPELINE
          ================================================== */}

          <div className="forecast-lineage">

            <div className="lineage-step">

              <span className="lineage-icon">
                🌦️
              </span>

              <div>

                <strong>
                  ECMWF IFS
                </strong>

                <small>
                  Numerical Weather Prediction
                </small>

              </div>

            </div>


            <div className="lineage-arrow">
              →
            </div>


            <div className="lineage-step">

              <span className="lineage-icon">
                🌧️
              </span>

              <div>

                <strong>
                  Rainfall Forecast
                </strong>

                <small>
                  Real meteorological input
                </small>

              </div>

            </div>


            <div className="lineage-arrow">
              →
            </div>


            <div className="lineage-step">

              <span className="lineage-icon">
                🤖
              </span>

              <div>

                <strong>
                  LandGuard AI
                </strong>

                <small>
                  Random Forest risk model
                </small>

              </div>

            </div>


            <div className="lineage-arrow">
              →
            </div>


            <div className="lineage-step">

              <span className="lineage-icon">
                🌊
              </span>

              <div>

                <strong>
                  Inundation Risk
                </strong>

                <small>
                  High / Moderate / Low
                </small>

              </div>

            </div>

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
                  7-day rainfall and inundation
                  risk outlook
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
                    dataKey="day"
                    tickFormatter={(day) =>
                      `Day ${day}`
                    }
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
              FORECAST RESULT CARDS
          ================================================== */}

          {forecast.length > 0 && (

            <div className="forecast-grid">

              {forecast.map((day) => (

                <div
                  className={`forecast-card risk-${String(
                    day.risk_level || "low"
                  ).toLowerCase()}`}
                  key={day.day}
                >

                  <span className="forecast-day">
                    DAY {day.day}
                  </span>

                  <span className="forecast-date">
                    {day.date ||
                      `Forecast Day ${day.day}`}
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

                    📊 High-Risk Probability:

                    <strong>
                      {" "}
                      {day.risk_probability}%
                    </strong>

                  </p>


                  <p>

                    🤖 AI Confidence:

                    <strong>
                      {" "}
                      {day.confidence ?? "—"}%
                    </strong>

                  </p>


                  {day.probabilities && (

                    <div className="forecast-probabilities">

                      <div className="probability-row">

                        <span>
                          🔴 High
                        </span>

                        <strong>
                          {day.probabilities.High ?? 0}%
                        </strong>

                      </div>


                      <div className="probability-row">

                        <span>
                          🟠 Moderate
                        </span>

                        <strong>
                          {day.probabilities.Moderate ?? 0}%
                        </strong>

                      </div>


                      <div className="probability-row">

                        <span>
                          🟢 Low
                        </span>

                        <strong>
                          {day.probabilities.Low ?? 0}%
                        </strong>

                      </div>

                    </div>

                  )}

                </div>

              ))}

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
                    AI-predicted inundation risk
                    probability across the
                    forecast period
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
                      value:
                        "Risk Probability (%)",
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
            INTEGRATED HAZARD ASSESSMENT
        ==================================================== */}

        <section className="panel integrated-risk-panel">

          <div className="panel-header">

            <div>
              <span className="section-label">
                🧠 MULTI-SOURCE DATA FUSION
              </span>

              <h2>
                Integrated Hazard Assessment
              </h2>

              <p>
                Combines current AI risk, 7-day forecast risk,
                and Sentinel-1 SAR change evidence.
              </p>
            </div>

            <span className="forecast-badge">
              🔗 DATA FUSION
            </span>

          </div>

          {integratedRiskLoading && (
            <div className="meteorological-status">
              ⏳ Calculating integrated hazard assessment...
            </div>
          )}

          {integratedRiskError && (
            <div className="meteorological-error">
              ⚠️ {integratedRiskError}
            </div>
          )}

          {integratedRisk && !integratedRiskLoading && (
            <>

              <div className="prediction-result">
                <span className="prediction-label">
                  INTEGRATED HAZARD INDEX
                </span>

                <strong>
                  {integratedRisk.index}
                </strong>

                <p>
                  Prototype multi-source evidence index • Not a calibrated flood probability
                </p>
              </div>

              <div className="current-weather-grid">

                <div className="weather-card">
                  <span>⚠️</span>
                  <small>Hazard Level</small>
                  <strong>{integratedRisk.level}</strong>
                </div>

                <div className="weather-card">
                  <span>🤖</span>
                  <small>Current AI Signal</small>
                  <strong>
                    {integratedRisk.components?.current_ai?.value ?? "--"}%
                  </strong>
                </div>

                <div className="weather-card">
                  <span>🌧️</span>
                  <small>Peak 7-Day Forecast Signal</small>
                  <strong>
                    {integratedRisk.components?.forecast?.value ?? "--"}%
                  </strong>
                </div>

                <div className="weather-card">
                  <span>🛰️</span>
                  <small>Sentinel-1 Candidate Coverage</small>
                  <strong>
                    {integratedRisk.components?.sentinel1_sar?.value ?? "--"}%
                  </strong>
                </div>

              </div>

              <div className="validation-flow">

                <div className="validation-card">
                  <span className="validation-icon">🤖</span>
                  <strong>Current AI</strong>
                  <small>Weight: 50%</small>
                  <div className="validation-status">
                    Contribution: {integratedRisk.components?.current_ai?.weighted_contribution ?? "--"}
                  </div>
                </div>

                <div className="validation-arrow">+</div>

                <div className="validation-card">
                  <span className="validation-icon">🌧️</span>
                  <strong>7-Day Forecast</strong>
                  <small>Weight: 30%</small>
                  <div className="validation-status">
                    Contribution: {integratedRisk.components?.forecast?.weighted_contribution ?? "--"}
                  </div>
                </div>

                <div className="validation-arrow">+</div>

                <div className="validation-card">
                  <span className="validation-icon">🛰️</span>
                  <strong>Sentinel-1 SAR</strong>
                  <small>Weight: 20%</small>
                  <div className="validation-status">
                    Contribution: {integratedRisk.components?.sentinel1_sar?.weighted_contribution ?? "--"}
                  </div>
                </div>

              </div>

              <div className="validation-note">
                <strong>Interpretation:</strong>{" "}
                {integratedRisk.interpretation}
              </div>

              {integratedRisk.evidence?.length > 0 && (
                <div className="validation-note">
                  <strong>Evidence:</strong>
                  <ul>
                    {integratedRisk.evidence.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="validation-note">
                <strong>⚠️ Validation status:</strong>{" "}
                {integratedRisk.validation_note}
              </div>

            </>
          )}

          {!integratedRisk &&
            !integratedRiskLoading &&
            !integratedRiskError && (
              <div className="validation-note">
                Integrated assessment will appear after the current AI prediction, 7-day AI forecast, and Sentinel-1 observation are available.
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
              {currentWeather?.rainfall ??
                inputs.rainfall_24h} mm
            </h3>

            <p>
              Current meteorological data
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
              {displaySoilMoisture}%
            </h3>

            <p>
              Current meteorological context
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
              {inputs.slope}°
            </h3>

            <p>
              Terrain inclination
            </p>

          </div>


          <div className="stat-card">

            <div className="stat-top">

              <span>
                🛰️
              </span>

              <small>
                SAR CANDIDATE
              </small>

            </div>

            <h3>
              {satelliteCandidatePercent != null
                ? `${satelliteCandidatePercent}%`
                : "--"}
            </h3>

            <p>
              Potential inundation candidate coverage
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
                  Inundation Risk & Impact Map
                </h2>

              </div>


              <button
                type="button"
                className="view-btn"
                onClick={fetchSatelliteData}
                disabled={satelliteLoading}
              >

                {satelliteLoading
                  ? "Loading SAR..."
                  : "Refresh Satellite →"}

              </button>

            </div>


            {/* =================================================
                7-DAY OUTLOOK SUMMARY
            ================================================== */}

            {forecast.length > 0 &&
              (() => {

                const peakDay =
                  forecast.reduce(
                    (max, day) =>
                      Number(
                        day.risk_probability || 0
                      ) >
                      Number(
                        max.risk_probability || 0
                      )
                        ? day
                        : max
                  );


                return (

                  <div className="forecast-summary">

                    <div className="summary-card">

                      <span className="summary-label">
                        FORECAST STATUS
                      </span>

                      <strong className="summary-status">
                        {forecast.length === 7
                          ? "7 DAYS READY"
                          : "NOT READY"}
                      </strong>

                      <small>
                        Forecast data available
                        for risk monitoring
                      </small>

                    </div>


                    <div className="summary-card">

                      <span className="summary-label">
                        PEAK RISK
                      </span>

                      <strong
                        className={`summary-risk risk-${String(
                          peakDay.risk_level || "low"
                        ).toLowerCase()}`}
                      >
                        {peakDay.risk_level}
                      </strong>

                      <small>
                        Highest predicted risk level
                      </small>

                    </div>


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


            {/* =================================================
                SATELLITE OBSERVATION & MODEL VALIDATION
            ================================================== */}

            <div className="panel satellite-validation-panel">

              <div className="panel-header">

                <div>

                  <span className="section-kicker">
                    🛰️ SENTINEL-1 SAR
                  </span>

                  <h2>
                    Satellite Observation & Model Validation
                  </h2>

                  <p>
                    Pixel-level Sentinel-1 pre/post
                    VV change detection for potential
                    inundation candidates.
                  </p>

                </div>


                <button
                  type="button"
                  className="forecast-badge"
                  onClick={fetchSatelliteData}
                  disabled={satelliteLoading}
                >

                  {satelliteLoading
                    ? "⏳ PROCESSING..."
                    : "🔄 REFRESH SAR"}

                </button>

              </div>


              <div className="validation-flow">


                {/* =================================================
                    SATELLITE
                ================================================== */}

                <div className="validation-card">

                  <span className="validation-icon">
                    🛰️
                  </span>


                  <strong>
                    Sentinel-1 Observation
                  </strong>


                  {satelliteLoading ? (

                    <small>
                      Processing Sentinel-1 SAR observations...
                    </small>

                  ) : satelliteError ? (

                    <>

                      <small className="error-text">
                        {satelliteError}
                      </small>

                      <div className="validation-status">
                        DATA UNAVAILABLE
                      </div>

                    </>

                  ) : satelliteData ? (

                    <>

                      <small>
                        Pixel-level pre/post SAR change
                      </small>


                      <div className="satellite-metrics">

                        <div>

                          <span>
                            Candidate Coverage
                          </span>

                          <strong>
                            {satelliteCandidatePercent != null
                              ? `${satelliteCandidatePercent}%`
                              : "—"}
                          </strong>

                        </div>


                        <div>

                          <span>
                            Candidate Area
                          </span>

                          <strong>
                            {satelliteCandidateArea != null
                              ? `${satelliteCandidateArea} km²`
                              : "—"}
                          </strong>

                        </div>

                      </div>


                      <small>

                        Pre-event:

                        {" "}

                        {satelliteData.pre_event?.datetime
                          ? new Date(
                              satelliteData.pre_event.datetime
                            ).toLocaleString()
                          : "—"}

                        <br />

                        Post-event:

                        {" "}

                        {satelliteData.post_event?.datetime
                          ? new Date(
                              satelliteData.post_event.datetime
                            ).toLocaleString()
                          : "—"}

                      </small>


                      <div className="validation-status">
                        🟢 PIXEL-LEVEL SAR DATA
                      </div>

                    </>

                  ) : (

                    <small>
                      Waiting for Sentinel-1 observations...
                    </small>

                  )}

                </div>


                <div className="validation-arrow">
                  →
                </div>


                {/* =================================================
                    SAR CHANGE
                ================================================== */}

                <div className="validation-card">

                  <span className="validation-icon">
                    📡
                  </span>


                  <strong>
                    SAR Change Detection
                  </strong>


                  <small>
                    VV backscatter change analysis
                  </small>


                  <div className="satellite-metrics">

                    <div>

                      <span>
                        Threshold
                      </span>

                      <strong>
                        {satelliteData?.change_detection?.threshold_db != null
                          ? `${satelliteData.change_detection.threshold_db} dB`
                          : "—"}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Time Gap
                      </span>

                      <strong>
                        {satelliteActualGap != null
                          ? `${satelliteActualGap} days`
                          : "—"}
                      </strong>

                    </div>

                  </div>


                  <div className="validation-status">

                    {satelliteData
                      ? satelliteClassification
                      : "WAITING FOR SAR"}

                  </div>

                </div>


                <div className="validation-arrow">
                  →
                </div>


                {/* =================================================
                    AI
                ================================================== */}

                <div className="validation-card">

                  <span className="validation-icon">
                    🤖
                  </span>


                  <strong>
                    LandGuard AI
                  </strong>


                  <small>
                    Predicted inundation risk
                  </small>


                  <div className="validation-status">
                    AI PREDICTION
                  </div>

                </div>


                <div className="validation-arrow">
                  →
                </div>


                {/* =================================================
                    VALIDATION
                ================================================== */}

                <div className="validation-card">

                  <span className="validation-icon">
                    📊
                  </span>


                  <strong>
                    Validation Pipeline
                  </strong>


                  <small>
                    Compare satellite-derived
                    candidate extent with
                    predicted inundation risk.
                  </small>


                  <div className="validation-status">
                    VALIDATION PIPELINE
                  </div>

                </div>

              </div>


              <div className="validation-note">

                <strong>
                  Satellite interpretation:
                </strong>

                {" "}

                {satelliteData

                  ? `Sentinel-1 detected ${satelliteCandidatePercent}% potential SAR-change coverage, corresponding to approximately ${satelliteCandidateArea} km² of candidate area. This is a potential inundation candidate mask, not a confirmed flood map.`

                  : "Sentinel-1 satellite observations will appear here when the satellite service responds."}

              </div>


              {/* =================================================
                  SAR DATA SUMMARY
              ================================================== */}

              {satelliteData && (

                <div className="meteorological-info">

                  <span>
                    🛰️ Sentinel-1 GRD
                  </span>

                  <span>
                    🎯 Threshold:
                    {" "}
                    {satelliteData.change_detection?.threshold_db ?? "—"} dB
                  </span>

                  <span>
                    📊 Valid Pixels:
                    {" "}
                    {satelliteData.mask?.valid_pixels?.toLocaleString() ?? "—"}
                  </span>

                  <span>
                    🔴 Candidate Pixels:
                    {" "}
                    {satelliteData.mask?.potential_inundation_pixels?.toLocaleString() ?? "—"}
                  </span>

                  <span>
                    📐 Candidate Area:
                    {" "}
                    {satelliteCandidateArea ?? "—"} km²
                  </span>

                </div>

              )}

            </div>


            {/* =================================================
                MAP
            ================================================== */}

            <div className="map-container">

              <MapContainer
                center={[26.15, 91.73]}
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


                {/* =================================================
                    SENTINEL-1 PIXEL-LEVEL SAR OVERLAY
                ================================================== */}

                {satelliteImageUrl &&
                  satelliteBounds && (

                    <ImageOverlay
                      url={satelliteImageUrl}
                      bounds={satelliteBounds}
                      opacity={0.70}
                      zIndex={400}
                      interactive={false}
                    />

                  )}


                {/* =================================================
                    SATELLITE OVERLAY LEGEND
                ================================================== */}

                {satelliteData && (

                  <div
                    style={{
                      position: "absolute",
                      bottom: "20px",
                      right: "20px",
                      zIndex: 1000,
                      background: "white",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
                      fontSize: "12px",
                      lineHeight: "1.5",
                    }}
                  >

                    <strong>
                      🛰️ Sentinel-1 SAR
                    </strong>

                    <div>
                      <span
                        style={{
                          display: "inline-block",
                          width: "12px",
                          height: "12px",
                          background: "#ff3232",
                          marginRight: "6px",
                          verticalAlign: "middle",
                        }}
                      ></span>

                      Potential inundation candidate
                    </div>

                    <div>
                      Coverage:
                      {" "}
                      {satelliteCandidatePercent}%
                    </div>

                  </div>

                )}


                {/* =================================================
                    GUWAHATI
                ================================================== */}

                <CircleMarker
                  center={[
                    26.1445,
                    91.7362
                  ]}
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
                      CURRENT SCENARIO RISK
                    </strong>

                    <br />

                    Guwahati Region

                    <br />

                    Risk Level:
                    {" "}
                    {riskLevel}

                    <br />

                    Confidence:
                    {" "}
                    {result
                      ? `${confidence}%`
                      : "Not analyzed"}

                  </Popup>

                </CircleMarker>


                {/* =================================================
                    SHILLONG
                ================================================== */}

                <CircleMarker
                  center={[
                    25.5788,
                    91.8933
                  ]}
                  radius={14}
                  pathOptions={{
                    color: "orange",
                    fillColor: "orange",
                    fillOpacity: 0.6,
                  }}
                >

                  <Popup>

                    <strong>
                      MONITORING ZONE
                    </strong>

                    <br />

                    Shillong Region

                    <br />

                    Potential inundation
                    monitoring area

                  </Popup>

                </CircleMarker>


                {/* =================================================
                    ASSAM
                ================================================== */}

                <CircleMarker
                  center={[
                    27.4728,
                    94.9120
                  ]}
                  radius={12}
                  pathOptions={{
                    color: "green",
                    fillColor: "green",
                    fillOpacity: 0.6,
                  }}
                >

                  <Popup>

                    <strong>
                      REGIONAL MONITORING ZONE
                    </strong>

                    <br />

                    Assam Region

                    <br />

                    Regional area for
                    continued monitoring

                  </Popup>

                </CircleMarker>


              </MapContainer>

            </div>

          </div>


          {/* =================================================
              CURRENT AI SCENARIO PREDICTION
          ================================================== */}

          <div className="panel prediction-panel">

            <div className="panel-header">

              <div>

                <span className="section-label">
                  AI SCENARIO ANALYSIS
                </span>

                <h2>
                  Inundation Risk Prediction
                </h2>

              </div>

            </div>


            <div className="prediction-result">

              <span className="prediction-label">
                CURRENT SCENARIO PREDICTION
              </span>

              <strong>
                {riskLevel}
              </strong>

              <p>
                Confidence:
                {" "}
                {result
                  ? `${confidence}%`
                  : "--"}
              </p>

            </div>


            {/* =================================================
                FORECAST HORIZONS
            ================================================== */}

            <div className="prediction-horizon-card">

              <h3>
                Forecast Horizons
              </h3>


              <div className="prediction-item">

                <span>
                  6 Hours
                </span>

                <strong>
                  Not available
                </strong>

              </div>


              <div className="prediction-item">

                <span>
                  12 Hours
                </span>

                <strong>
                  Not available
                </strong>

              </div>


              <div className="prediction-item">

                <span>
                  24 Hours
                </span>

                <strong>
                  Not available
                </strong>

              </div>


              <p className="prediction-note">

                Short-horizon nowcasting will be added
                after radar and high-frequency
                observational data integration.

              </p>

            </div>

          </div>

        </section>


        {/* ===================================================
            INUNDATION IMPACT CHAIN + COPILOT
        ==================================================== */}

        <section className="bottom-grid">


          {/* IMPACT CHAIN */}

          <div className="panel impact-chain-panel">

            <div className="panel-header">

              <div>

                <span className="section-label">
                  SCENARIO IMPACT CHAIN
                </span>

                <h2>
                  Potential Disaster Chain
                </h2>

                <p>
                  Scenario-based impact chain generated
                  from the manually specified hazard
                  conditions.
                </p>

              </div>

            </div>


            <div className="impact-chain-flow">


              <div className="impact-chain-node">

                <span>
                  🌧️
                </span>

                <strong>
                  Heavy Rain
                </strong>

                <small>

                  {inputs.rainfall_24h}
                  {" "}mm / 24h

                  <br />

                  Status:

                  {" "}

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


              <div
                className={`impact-chain-node ${
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

                  {inputs.soil_moisture}%
                  moisture

                  <br />

                  Status:

                  {" "}

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


              <div
                className={`impact-chain-node ${
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
                  Inundation
                </strong>

                <small>

                  AI Scenario Risk:

                  {" "}

                  <strong>
                    {riskLevel}
                  </strong>

                </small>

              </div>


              <div className="arrow">
                →
              </div>


              <div
                className={`impact-chain-node ${
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

                  Status:

                  {" "}

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


              <div
                className={`impact-chain-node ${
                  riskLevel === "High"
                    ? "danger"
                    : riskLevel === "Moderate"
                    ? "warning"
                    : ""
                }`}
              >

                <span>
                  🏥
                </span>

                <strong>
                  Infrastructure Impact
                </strong>

                <small>

                  Status:

                  {" "}

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


          {/* AI COPILOT */}

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
            DYNAMIC IMPACT ASSESSMENT
        ==================================================== */}

        <section className="panel impact-assessment-card">

          <div className="panel-header">

            <div>

              <span className="section-label">
                IMPACT ASSESSMENT
              </span>

              <h2>
                Potential Inundation Impact
              </h2>

              <p>
                AI-assisted assessment of areas
                and infrastructure that may require
                increased attention under the
                predicted scenario conditions.
              </p>

            </div>

          </div>


          <div className="impact-status">

            <span className="section-label">
              CURRENT STATUS
            </span>

            <strong>
              {impactStatus}
            </strong>

          </div>


          <div className="impact-grid">


            {/* SETTLEMENTS */}

            <div className="impact-item">

              <span className="impact-icon">
                🏘️
              </span>

              <div>

                <strong>
                  Settlements
                </strong>

                <span
                  className={`impact-badge ${impactBadgeClass}`}
                >
                  {impactStatus}
                </span>

                <p>
                  {impactData.settlements}
                </p>

              </div>

            </div>


            {/* ROADS */}

            <div className="impact-item">

              <span className="impact-icon">
                🛣️
              </span>

              <div>

                <strong>
                  Road Connectivity
                </strong>

                <span
                  className={`impact-badge ${impactBadgeClass}`}
                >
                  {impactStatus}
                </span>

                <p>
                  {impactData.roads}
                </p>

              </div>

            </div>


            {/* INFRASTRUCTURE */}

            <div className="impact-item">

              <span className="impact-icon">
                🏥
              </span>

              <div>

                <strong>
                  Critical Infrastructure
                </strong>

                <span
                  className={`impact-badge ${impactBadgeClass}`}
                >
                  {impactStatus}
                </span>

                <p>
                  {impactData.infrastructure}
                </p>

              </div>

            </div>


            {/* RESPONSE */}

            <div className="impact-item">

              <span className="impact-icon">
                🚨
              </span>

              <div>

                <strong>
                  Response Priority
                </strong>

                <span
                  className={`impact-badge ${impactBadgeClass}`}
                >
                  {impactStatus}
                </span>

                <p>
                  {impactData.response}
                </p>

              </div>

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
