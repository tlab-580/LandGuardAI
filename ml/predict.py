import joblib
import pandas as pd


# Load trained model
model = joblib.load("ml/models/landslide_risk_model.pkl")


# Example current environmental conditions
data = pd.DataFrame([{
    "rainfall_24h": 120,
    "rainfall_7d": 450,
    "soil_moisture": 82,
    "slope_angle": 42,
    "elevation": 1200,
    "ndvi": 0.35
}])


# Predict risk
prediction = model.predict(data)[0]

probabilities = model.predict_proba(data)[0]

classes = model.classes_

confidence = probabilities[list(classes).index(prediction)]


print("\n====================================")
print("LANDGUARD AI PREDICTION")
print("====================================")

print(f"Risk Level : {prediction}")
print(f"Confidence : {confidence * 100:.2f}%")