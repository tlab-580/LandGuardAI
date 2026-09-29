"""
LandGuard AI 2.0
Integrated Hazard Fusion Service

Combines:
1. Current AI inundation high-risk probability
2. Peak 7-day forecast high-risk probability
3. Sentinel-1 SAR candidate coverage

Important:
The output is an INTEGRATED HAZARD INDEX, not a calibrated
probability of flooding.

Fusion weights are prototype weights and should be calibrated
against historical/event-based validation data before operational use.
"""

AI_CURRENT_WEIGHT = 0.50
FORECAST_WEIGHT = 0.30
SAR_WEIGHT = 0.20


def _clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, float(value)))


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def classify_hazard(index):
    if index >= 75:
        return "VERY HIGH"
    if index >= 50:
        return "HIGH"
    if index >= 25:
        return "MODERATE"
    return "LOW"


def calculate_integrated_hazard(
    ai_current_high_probability,
    forecast_high_probability,
    satellite_candidate_percent,
):
    """
    Calculate an explainable Integrated Hazard Index.

    The result is an evidence-fusion index, not a calibrated flood
    probability.
    """

    ai_score = _clamp(_safe_float(ai_current_high_probability))
    forecast_score = _clamp(_safe_float(forecast_high_probability))
    sar_score = _clamp(_safe_float(satellite_candidate_percent))

    integrated_index = (
        ai_score * AI_CURRENT_WEIGHT
        + forecast_score * FORECAST_WEIGHT
        + sar_score * SAR_WEIGHT
    )

    integrated_index = round(integrated_index, 2)
    hazard_level = classify_hazard(integrated_index)

    evidence = []

    if ai_score >= 50:
        evidence.append(
            "Current AI model indicates elevated inundation risk."
        )
    elif ai_score >= 25:
        evidence.append(
            "Current AI model indicates moderate inundation risk."
        )
    else:
        evidence.append(
            "Current AI model indicates relatively low inundation risk."
        )

    if forecast_score >= 50:
        evidence.append(
            "The 7-day forecast contains a high-risk forecast signal."
        )
    elif forecast_score >= 25:
        evidence.append(
            "The 7-day forecast contains a moderate-risk signal."
        )
    else:
        evidence.append(
            "The 7-day forecast currently shows a lower high-risk signal."
        )

    if sar_score >= 20:
        evidence.append(
            "Sentinel-1 shows substantial candidate SAR-change coverage."
        )
    elif sar_score > 0:
        evidence.append(
            "Sentinel-1 shows some potential SAR-change candidate coverage."
        )
    else:
        evidence.append(
            "Sentinel-1 did not identify candidate SAR-change coverage."
        )

    return {
        "index": integrated_index,
        "level": hazard_level,
        "interpretation": (
            "Integrated evidence index combining current AI risk, "
            "forecast risk, and Sentinel-1 SAR candidate coverage."
        ),
        "components": {
            "current_ai": {
                "value": round(ai_score, 2),
                "weight": AI_CURRENT_WEIGHT,
                "weighted_contribution": round(
                    ai_score * AI_CURRENT_WEIGHT, 2
                ),
            },
            "forecast": {
                "value": round(forecast_score, 2),
                "weight": FORECAST_WEIGHT,
                "weighted_contribution": round(
                    forecast_score * FORECAST_WEIGHT, 2
                ),
            },
            "sentinel1_sar": {
                "value": round(sar_score, 2),
                "weight": SAR_WEIGHT,
                "weighted_contribution": round(
                    sar_score * SAR_WEIGHT, 2
                ),
                "meaning": (
                    "Candidate SAR-change coverage, not flood probability."
                ),
            },
        },
        "evidence": evidence,
        "validation_note": (
            "Fusion weights and hazard bands are prototype values. "
            "Historical and event-based validation is required before "
            "operational deployment."
        ),
    }
