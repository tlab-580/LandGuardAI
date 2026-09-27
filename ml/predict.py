import joblib
import pandas as pd


MODEL_PATH = "ml/models/inundation_risk_model.pkl"


# --------------------------------------------------
# Load trained model
# --------------------------------------------------

model = joblib.load(MODEL_PATH)


# --------------------------------------------------
# Example heavy-rainfall scenario
# --------------------------------------------------

scenario = pd.DataFrame([{
    "rainfall_1h": 80,
    "rainfall_6h": 150,
    "rainfall_24h": 250,
    "rainfall_3d": 400,
    "rainfall_7d": 600,
    "forecast_rainfall_6h": 100,
    "forecast_rainfall_24h": 200,
    "forecast_rainfall_7d": 400,
    "soil_moisture": 85,
    "elevation": 100,
    "slope": 5,
    "distance_to_river": 0.3,
    "drainage_density": 0.25
}])


# --------------------------------------------------
# Prediction
# --------------------------------------------------

prediction = model.predict(scenario)[0]

probabilities = model.predict_proba(scenario)[0]

class_probabilities = dict(
    zip(model.classes_, probabilities)
)


# --------------------------------------------------
# Confidence
# --------------------------------------------------

confidence = max(probabilities) * 100


# --------------------------------------------------
# Feature importance
# --------------------------------------------------

feature_importance = dict(
    zip(
        scenario.columns,
        model.feature_importances_
    )
)

top_features = sorted(
    feature_importance.items(),
    key=lambda x: x[1],
    reverse=True
)[:5]


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("========================================")
print("LANDGUARD AI 2.0 PREDICTION")
print("========================================")

print(f"\nPredicted Inundation Risk: {prediction}")

print(f"Model Confidence: {confidence:.2f}%")

print("\nRisk Probabilities:")

for risk_class, probability in class_probabilities.items():
    print(
        f"{risk_class}: "
        f"{probability * 100:.2f}%"
    )


print("\nTop Contributing Features:")

for feature, importance in top_features:
    print(
        f"{feature}: "
        f"{importance * 100:.2f}%"
    )


print("\n========================================")