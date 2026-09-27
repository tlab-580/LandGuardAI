import numpy as np
import pandas as pd

# Reproducible results
np.random.seed(42)

# Number of training samples
n_samples = 3000

# Generate rainfall features
rainfall_1h = np.random.uniform(0, 120, n_samples)

rainfall_6h = rainfall_1h + np.random.uniform(0, 180, n_samples)

rainfall_24h = rainfall_6h + np.random.uniform(0, 250, n_samples)

rainfall_3d = rainfall_24h + np.random.uniform(0, 350, n_samples)

rainfall_7d = rainfall_3d + np.random.uniform(0, 500, n_samples)

# Forecast rainfall
forecast_rainfall_6h = np.random.uniform(0, 150, n_samples)

forecast_rainfall_24h = (
    forecast_rainfall_6h + np.random.uniform(0, 250, n_samples)
)

forecast_rainfall_7d = (
    forecast_rainfall_24h + np.random.uniform(0, 500, n_samples)
)

# Environmental features
soil_moisture = np.random.uniform(10, 100, n_samples)

elevation = np.random.uniform(5, 2500, n_samples)

slope = np.random.uniform(0, 45, n_samples)

distance_to_river = np.random.uniform(0.05, 10, n_samples)

drainage_density = np.random.uniform(0.05, 1.0, n_samples)

# --------------------------------------------------
# Calculate an initial inundation risk score
# --------------------------------------------------

risk_score = (
    rainfall_1h * 0.08
    + rainfall_6h * 0.05
    + rainfall_24h * 0.035
    + rainfall_3d * 0.015
    + rainfall_7d * 0.01
    + forecast_rainfall_6h * 0.05
    + forecast_rainfall_24h * 0.025
    + forecast_rainfall_7d * 0.008
    + soil_moisture * 0.25
    - elevation * 0.006
    - slope * 0.15
    - distance_to_river * 4
    - drainage_density * 15
)

# Add small random variation
risk_score += np.random.normal(0, 5, n_samples)

# Convert numerical score into classes
inundation_risk = np.where(
    risk_score >= 45,
    "High",
    np.where(
        risk_score >= 25,
        "Moderate",
        "Low"
    )
)

# Create dataframe
df = pd.DataFrame({
    "rainfall_1h": rainfall_1h,
    "rainfall_6h": rainfall_6h,
    "rainfall_24h": rainfall_24h,
    "rainfall_3d": rainfall_3d,
    "rainfall_7d": rainfall_7d,
    "forecast_rainfall_6h": forecast_rainfall_6h,
    "forecast_rainfall_24h": forecast_rainfall_24h,
    "forecast_rainfall_7d": forecast_rainfall_7d,
    "soil_moisture": soil_moisture,
    "elevation": elevation,
    "slope": slope,
    "distance_to_river": distance_to_river,
    "drainage_density": drainage_density,
    "inundation_risk": inundation_risk
})

# Save dataset
output_path = "data/rainfall_inundation_training_data.csv"

df.to_csv(output_path, index=False)

print(f"Dataset created successfully: {output_path}")
print(f"Total samples: {len(df)}")
print("\nRisk distribution:")
print(df["inundation_risk"].value_counts())

print("\nFirst 5 rows:")
print(df.head())