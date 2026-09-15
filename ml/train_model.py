import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
df = pd.read_csv("data/landslide_training_data.csv")

# Features used by the model
features = [
    "rainfall_24h",
    "rainfall_7d",
    "soil_moisture",
    "slope_angle",
    "elevation",
    "ndvi"
]

X = df[features]
y = df["risk_level"]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# Create model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    max_depth=12
)


# Train
model.fit(X_train, y_train)


# Test
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n====================================")
print("LANDGUARD AI MODEL TRAINING")
print("====================================")

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, predictions))


# Save model
joblib.dump(
    model,
    "ml/models/landslide_risk_model.pkl"
)

print("\nModel saved successfully!")
print("Location: ml/models/landslide_risk_model.pkl")