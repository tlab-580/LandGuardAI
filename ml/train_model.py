import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# --------------------------------------------------
# 1. Load dataset
# --------------------------------------------------

DATA_PATH = "data/rainfall_inundation_training_data.csv"
MODEL_PATH = "ml/models/inundation_risk_model.pkl"

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully.")
print(f"Total samples: {len(df)}")

# --------------------------------------------------
# 2. Define features and target
# --------------------------------------------------

features = [
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "rainfall_3d",
    "rainfall_7d",
    "forecast_rainfall_6h",
    "forecast_rainfall_24h",
    "forecast_rainfall_7d",
    "soil_moisture",
    "elevation",
    "slope",
    "distance_to_river",
    "drainage_density"
]

target = "inundation_risk"

X = df[features]
y = df[target]

# --------------------------------------------------
# 3. Split dataset
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")

# --------------------------------------------------
# 4. Create Random Forest model
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight="balanced"
)

# --------------------------------------------------
# 5. Train model
# --------------------------------------------------

print("\nTraining inundation risk model...")

model.fit(X_train, y_train)

print("Training completed.")

# --------------------------------------------------
# 6. Make predictions
# --------------------------------------------------

y_pred = model.predict(X_test)

# --------------------------------------------------
# 7. Evaluate model
# --------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)

print("\n========================================")
print("LANDGUARD AI 2.0 MODEL RESULTS")
print("========================================")

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# --------------------------------------------------
# 8. Feature importance
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    by="importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# --------------------------------------------------
# 9. Save trained model
# --------------------------------------------------

joblib.dump(model, MODEL_PATH)

print("\n========================================")
print("Model saved successfully:")
print(MODEL_PATH)
print("========================================")