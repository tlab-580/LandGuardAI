import { useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";

function App() {
  const [inputs, setInputs] = useState({
    rainfall_24h: 120,
    rainfall_7d: 450,
    soil_moisture: 82,
    slope_angle: 42,
    elevation: 1200,
    ndvi: 0.35,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setInputs({
      ...inputs,
      [name]: Number(value),
    });
  };

  const predictRisk = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/predict-risk`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(data),
});

      if (!response.ok) {
        throw new Error("Prediction request failed");
      }

      const data = await response.json();

      setResult(data);
    } catch (err) {
      console.error(err);
      setError(
        "Unable to connect to LANDGUARD AI backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="app">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="logo">
          <div className="logo-icon">🏔️</div>

          <div>
            <h2>LANDGUARD</h2>
            <span>AI DISASTER INTELLIGENCE</span>
          </div>
        </div>

        <nav>
          <a className="active">📊 Dashboard</a>
          <a>🗺️ Risk Map</a>
          <a>📈 Predictions</a>
          <a>⚠️ Alerts</a>
          <a>📷 Citizen Reports</a>
          <a>🤖 AI Copilot</a>
        </nav>

        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <strong>System Online</strong>
            <small>AI services operational</small>
          </div>
        </div>

      </aside>


      {/* MAIN */}
      <main className="main-content">

        {/* HEADER */}
        <header className="topbar">

          <div>
            <p className="eyebrow">
              DISASTER MANAGEMENT PLATFORM
            </p>

            <h1>LANDGUARD AI</h1>

            <p className="subtitle">
              Explainable landslide & cascading disaster early-warning system
            </p>
          </div>

          <div className="header-actions">

            <button className="location-btn">
              📍 North Eastern Region
            </button>

            <button className="profile-btn">
              TS
            </button>

          </div>

        </header>


        {/* RISK BANNER */}
        <section className={`risk-banner ${riskClass}`}>

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


        {/* ENVIRONMENT INPUTS */}
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
              className="predict-btn"
              onClick={predictRisk}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Run AI Prediction →"}
            </button>

          </div>


          <div className="input-grid">

            <div className="input-card">

              <label>Rainfall — 24 Hours (mm)</label>

              <input
                type="number"
                name="rainfall_24h"
                value={inputs.rainfall_24h}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>Rainfall — 7 Days (mm)</label>

              <input
                type="number"
                name="rainfall_7d"
                value={inputs.rainfall_7d}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>Soil Moisture (%)</label>

              <input
                type="number"
                name="soil_moisture"
                value={inputs.soil_moisture}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>Slope Angle (°)</label>

              <input
                type="number"
                name="slope_angle"
                value={inputs.slope_angle}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>Elevation (m)</label>

              <input
                type="number"
                name="elevation"
                value={inputs.elevation}
                onChange={handleChange}
              />

            </div>


            <div className="input-card">

              <label>Vegetation Index — NDVI</label>

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


        {/* RESULT */}
        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-top">
              <span>🌧️</span>
              <small>RAINFALL</small>
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
              <span>💧</span>
              <small>SOIL MOISTURE</small>
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
              <span>⛰️</span>
              <small>SLOPE</small>
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
              <span>🤖</span>
              <small>AI RESULT</small>
            </div>

            <h3>
              {result ? riskLevel : "--"}
            </h3>

            <p>
              Predicted risk
            </p>

          </div>

        </section>


        {/* DASHBOARD GRID */}
        <section className="dashboard-grid">

          {/* MAP */}
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

              <button className="view-btn">
                View Full Map →
              </button>

            </div>
<div className="map-container">
  <MapContainer
    center={[26.2, 92.9]}
    zoom={6}
    scrollWheelZoom={true}
    style={{ height: "450px", width: "100%" }}
  >
    <TileLayer
      attribution='&copy; OpenStreetMap contributors'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
    />

    <CircleMarker
      center={[26.1445, 91.7362]}
      radius={18}
      pathOptions={{
        color: "red",
        fillColor: "red",
        fillOpacity: 0.6,
      }}
    >
      <Popup>
        <strong>HIGH RISK ZONE</strong>
        <br />
        Guwahati Region
        <br />
        Heavy rainfall detected
      </Popup>
    </CircleMarker>

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
        <strong>MODERATE RISK</strong>
        <br />
        Shillong Region
      </Popup>
    </CircleMarker>

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
        <strong>LOW RISK</strong>
        <br />
        Assam Region
      </Popup>
    </CircleMarker>
  </MapContainer>
</div>


                    {/* PREDICTION */}
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
                Confidence: {result ? `${confidence}%` : "--"}
              </p>

            </div>

            <div className="prediction-item">

              <div>
                <strong>6 Hours</strong>
                <span>Forecast</span>
              </div>

              <div className="prediction-bar">
                <div style={{ width: "58%" }}></div>
              </div>

              <b>58%</b>

            </div>

            <div className="prediction-item">

              <div>
                <strong>12 Hours</strong>
                <span>Forecast</span>
              </div>

              <div className="prediction-bar">
                <div style={{ width: "71%" }}></div>
              </div>

              <b>71%</b>

            </div>

            <div className="prediction-item">

              <div>
                <strong>24 Hours</strong>
                <span>Forecast</span>
              </div>

              <div className="prediction-bar">
                <div style={{ width: "82%" }}></div>
              </div>

              <b>82%</b>

            </div>

                   </div>

        </div>

        </section>


        {/* BOTTOM */}
        <section className="bottom-grid">

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

  <div className="cascade-node">
    <span>🌧️</span>
    <strong>Heavy Rain</strong>
    <small>
      {inputs.rainfall_24h} mm / 24h
    </small>
  </div>

  <div className="arrow">→</div>

  <div className="cascade-node">
    <span>💧</span>
    <strong>Soil Saturation</strong>
    <small>
      {inputs.soil_moisture}% moisture
    </small>
  </div>

  <div className="arrow">→</div>

  <div className={`cascade-node ${riskLevel === "High" ? "danger" : ""}`}>
    <span>⛰️</span>
    <strong>Landslide</strong>
    <small>
      AI Risk: {riskLevel}
    </small>
  </div>

  <div className="arrow">→</div>

  <div className={`cascade-node ${riskLevel === "High" ? "danger" : ""}`}>
    <span>🛣️</span>
    <strong>Road Blockage</strong>
    <small>
      Potential impact
    </small>
   </div>
</div>

          </div>

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
                Ask about risk levels, affected locations,
                emergency actions, and disaster-management
                guidelines.
              </p>

              <button className="copilot-btn">
                Open AI Copilot →
              </button>

            </div>

          </div>

        </section>


        <footer>
          LANDGUARD AI • AI-powered disaster intelligence platform
        </footer>

      </main>

    </div>
  );
}

export default App;