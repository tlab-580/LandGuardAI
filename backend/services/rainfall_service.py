
import json
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError


def generate_meteorological_forecast(
    latitude: float,
    longitude: float,
    days: int = 15
):
    """
    Fetches real numerical weather prediction data.

    Data source:
    Open-Meteo ECMWF IFS forecast

    This is real meteorological forecast data from an NWP model,
    not a synthetic rainfall scenario.

    ECMWF IFS forecast availability is limited to approximately
    15 days through the selected API.
    """

    if days < 1 or days > 15:
        raise ValueError(
            "Real meteorological forecast supports 1 to 15 days."
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "rain_sum,"
            "precipitation_sum,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_hours"
        ),
        "timezone": "auto",
        "forecast_days": days,
        "models": "ecmwf_ifs025",
    }

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(params)
    )

    try:
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        raise RuntimeError(
            f"Meteorological API returned HTTP {error.code}"
        )

    except URLError as error:
        raise RuntimeError(
            f"Unable to connect to meteorological API: {error.reason}"
        )

    daily = data.get("daily")

    if not daily:
        raise RuntimeError(
            "Meteorological API returned no daily forecast data."
        )

    dates = daily.get("time", [])
    rain = daily.get("rain_sum", [])
    precipitation = daily.get("precipitation_sum", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precipitation_hours = daily.get(
        "precipitation_hours", []
    )

    forecast = []

    for i, date in enumerate(dates):

        forecast.append({
            "day": i + 1,
            "date": date,

            "rainfall": round(
                float(rain[i] or 0), 2
            ),

            "precipitation": round(
                float(precipitation[i] or 0), 2
            ),

            "temperature_max": round(
                float(temp_max[i]), 1
            ) if temp_max[i] is not None else None,

            "temperature_min": round(
                float(temp_min[i]), 1
            ) if temp_min[i] is not None else None,

            "precipitation_hours": round(
                float(precipitation_hours[i] or 0), 1
            ),

            "source": "ECMWF IFS",
            "provider": "Open-Meteo",
            "data_type": "Numerical Weather Prediction"
        })

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "model": "ECMWF IFS",
        "provider": "Open-Meteo",
        "forecast_days": days,
        "data_type": "Numerical Weather Prediction",
        "forecast": forecast
    }


# ---------------------------------------------------------
# EXISTING SCENARIO GENERATOR
# ---------------------------------------------------------

def generate_rainfall_scenario(
    base_rainfall: float,
    days: int = 7
):
    """
    Synthetic rainfall scenario generator.

    IMPORTANT:
    This is NOT a meteorological forecast.

    It is retained for:
    - scenario simulation
    - stress testing
    - 30-day preparedness scenarios
    """

    rainfall_pattern = [
        1.00,
        1.15,
        1.30,
        1.10,
        0.90,
        0.75,
        0.60
    ]

    from datetime import datetime, timedelta

    today = datetime.now()

    forecast = []

    for i in range(days):

        multiplier = rainfall_pattern[
            i % len(rainfall_pattern)
        ]

        rainfall = round(
            base_rainfall * multiplier,
            2
        )

        forecast.append({
            "day": i + 1,
            "date": (
                today + timedelta(days=i + 1)
            ).strftime("%Y-%m-%d"),
            "rainfall": rainfall,
            "source": "AI Scenario"
        })

    return forecast

def generate_current_weather(
    latitude: float,
    longitude: float
):
    """
    Retrieves current weather conditions for the selected location.

    IMPORTANT:
    These values are current meteorological data from Open-Meteo.
    They should not be described as direct ground-station observations.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "soil_moisture_0_to_1cm"
        ),
        "timezone": "auto",
    }

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(params)
    )

    try:
        with urlopen(url, timeout=15) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as error:
        raise RuntimeError(
            f"Current weather API returned HTTP {error.code}"
        )

    except URLError as error:
        raise RuntimeError(
            f"Unable to connect to current weather API: {error.reason}"
        )

    current = data.get("current")

    if not current:
        raise RuntimeError(
            "Current weather API returned no current data."
        )

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "time": current.get("time"),

        "temperature": current.get(
            "temperature_2m"
        ),

        "relative_humidity": current.get(
            "relative_humidity_2m"
        ),

        "precipitation": current.get(
            "precipitation"
        ),

        "rainfall": current.get(
            "rain"
        ),

        "weather_code": current.get(
            "weather_code"
        ),

        "wind_speed": current.get(
            "wind_speed_10m"
        ),

        "soil_moisture": current.get(
            "soil_moisture_0_to_1cm"
        ),

        "provider": "Open-Meteo",

        "data_type": (
            "Current meteorological data"
        )
    }
