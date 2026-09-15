import pandas as pd
import numpy as np

np.random.seed(42)

rows = 2000

rainfall_24h = np.random.uniform(0, 250, rows)
rainfall_7d = np.random.uniform(10, 800, rows)
soil_moisture = np.random.uniform(20, 100, rows)
slope_angle = np.random.uniform(5, 60, rows)
elevation = np.random.uniform(50, 2500, rows)
ndvi = np.random.uniform(0.05, 0.9, rows)

risk_score = (
    rainfall_24h * 0.22
    + rainfall_7d * 0.06
    + soil_moisture * 0.30
    + slope_angle * 0.65
    + elevation * 0.005
    - ndvi * 18
)

risk_score = np.clip(risk_score, 0, 100)

risk_level = np.where(
    risk_score >= 70,
    "High",
    np.where(risk_score >= 40, "Moderate", "Low")
)

df = pd.DataFrame({
    "rainfall_24h": rainfall_24h,
    "rainfall_7d": rainfall_7d,
    "soil_moisture": soil_moisture,
    "slope_angle": slope_angle,
    "elevation": elevation,
    "ndvi": ndvi,
    "risk_score": risk_score,
    "risk_level": risk_level
})

df.to_csv("data/landslide_training_data.csv", index=False)

print("Dataset created successfully!")
print(f"Rows: {len(df)}")
print(df.head())