import json
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ============================================================
# OPEN-METEO CONFIGURATION
# ============================================================

OPEN_METEO_BASE_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

# Keep recent successful responses in memory so repeated
# dashboard requests do not repeatedly hit Open-Meteo.
FORECAST_CACHE_TTL_SECONDS = 15 * 60
CURRENT_WEATHER_CACHE_TTL_SECONDS = 5 * 60

# Short retry schedule for temporary HTTP 429 responses.
# This avoids immediately failing on a transient rate limit.
MAX_429_RETRIES = 3
RETRY_DELAYS_SECONDS = [2, 4, 8]

# Thread-safe cache because FastAPI may serve concurrent requests.
_CACHE_LOCK = threading.Lock()

# Cache key -> {"timestamp": float, "data": dict}
_OPEN_METEO_CACHE = {}


# ============================================================
# CACHE HELPERS
# ============================================================

def _cache_key(latitude: float, longitude: float):
    """Create a stable cache key for a geographic point."""

    return (
        round(float(latitude), 4),
        round(float(longitude), 4)
    )


def _get_cached_open_meteo(
    latitude: float,
    longitude: float,
    ttl_seconds: int
):
    """Return a recent cached Open-Meteo response, if available."""

    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        cached = _OPEN_METEO_CACHE.get(key)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age > ttl_seconds:
            return None

        return cached["data"]


def _store_cached_open_meteo(
    latitude: float,
    longitude: float,
    data: dict
):
    """Store the latest successful Open-Meteo response."""

    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        _OPEN_METEO_CACHE[key] = {
            "timestamp": time.time(),
            "data": data
        }


def _get_stale_cached_open_meteo(
    latitude: float,
    longitude: float
):
    """Return the last successful response even when its TTL expired."""

    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        cached = _OPEN_METEO_CACHE.get(key)

        if not cached:
            return None

        return cached["data"]


# ============================================================
# OPEN-METEO REQUEST
# ============================================================

def _fetch_open_meteo_data(
    latitude: float,
    longitude: float,
    days: int = 15
):
    """
    Fetch one combined Open-Meteo response containing:

    - ECMWF IFS daily forecast fields
    - current meteorological conditions

    The combined response is cached and reused by both public
    weather functions so the dashboard does not create duplicate
    external requests.
    """

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
        "forecast_days": days,
        "models": "ecmwf_ifs025",
    }

    url = (
        OPEN_METEO_BASE_URL
        + "?"
        + urlencode(params)
    )

    request = Request(
        url,
        headers={
            "User-Agent": "LANDGUARD-AI/2.0"
        }
    )

    last_error = None

    for attempt in range(MAX_429_RETRIES + 1):

        try:

            with urlopen(
                request,
                timeout=20
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            _store_cached_open_meteo(
                latitude=latitude,
                longitude=longitude,
                data=data
            )

            return data

        except HTTPError as error:

            last_error = error

            # Rate limiting: retry briefly before falling back to
            # the last successful cached response.
            if error.code == 429 and attempt < MAX_429_RETRIES:

                retry_after = error.headers.get(
                    "Retry-After"
                )

                try:
                    delay = float(retry_after)
                except (
                    TypeError,
                    ValueError
                ):
                    delay = RETRY_DELAYS_SECONDS[
                        min(
                            attempt,
                            len(RETRY_DELAYS_SECONDS) - 1
                        )
                    ]

                # Prevent an unexpectedly large server-provided
                # Retry-After value from blocking the API for too long.
                delay = max(1, min(delay, 10))

                time.sleep(delay)
                continue

            raise RuntimeError(
                f"Meteorological API returned HTTP {error.code}"
            )

        except URLError as error:

            last_error = error

            raise RuntimeError(
                "Unable to connect to meteorological API: "
                f"{error.reason}"
            )

        except (
            TimeoutError,
            json.JSONDecodeError
        ) as error:

            last_error = error

            raise RuntimeError(
                "Meteorological API returned an invalid or "
                "timed-out response."
            )

    # Defensive fallback; the loop normally raises before this point.
    raise RuntimeError(
        f"Meteorological API request failed: {last_error}"
    )


def _get_weather_data(
    latitude: float,
    longitude: float,
    days: int,
    ttl_seconds: int
):
    """
    Get weather data from the recent cache when possible.

    When the external API is temporarily unavailable, the last
    successful cached response is returned so the dashboard remains
    usable instead of failing completely.
    """

    cached = _get_cached_open_meteo(
        latitude=latitude,
        longitude=longitude,
        ttl_seconds=ttl_seconds
    )

    if cached is not None:
        return cached, False

    try:
        fresh_data = _fetch_open_meteo_data(
            latitude=latitude,
            longitude=longitude,
            days=days
        )

        return fresh_data, False

    except RuntimeError as error:

        stale = _get_stale_cached_open_meteo(
            latitude=latitude,
            longitude=longitude
        )

        if stale is not None:
            print(
                "Open-Meteo temporarily unavailable; "
                "using last successful cached response: "
                f"{error}"
            )
            return stale, True

        raise


# ============================================================
# REAL METEOROLOGICAL FORECAST
# ============================================================

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

    Production safeguards:
    - in-memory caching
    - short retry for HTTP 429
    - stale-cache fallback during temporary API failures
    """

    if days < 1 or days > 15:
        raise ValueError(
            "Real meteorological forecast supports 1 to 15 days."
        )

    data, used_stale_cache = _get_weather_data(
        latitude=latitude,
        longitude=longitude,
        days=days,
        ttl_seconds=FORECAST_CACHE_TTL_SECONDS
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

        # Protect against partially populated API arrays.
        rain_value = (
            rain[i]
            if i < len(rain)
            else 0
        )

        precipitation_value = (
            precipitation[i]
            if i < len(precipitation)
            else 0
        )

        temp_max_value = (
            temp_max[i]
            if i < len(temp_max)
            else None
        )

        temp_min_value = (
            temp_min[i]
            if i < len(temp_min)
            else None
        )

        precipitation_hours_value = (
            precipitation_hours[i]
            if i < len(precipitation_hours)
            else 0
        )

        forecast.append({
            "day": i + 1,
            "date": date,

            "rainfall": round(
                float(rain_value or 0), 2
            ),

            "precipitation": round(
                float(precipitation_value or 0), 2
            ),

            "temperature_max": round(
                float(temp_max_value), 1
            ) if temp_max_value is not None else None,

            "temperature_min": round(
                float(temp_min_value), 1
            ) if temp_min_value is not None else None,

            "precipitation_hours": round(
                float(precipitation_hours_value or 0), 1
            ),

            "source": "ECMWF IFS",
            "provider": "Open-Meteo",
            "data_type": "Numerical Weather Prediction"
        })

    result = {
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

    if used_stale_cache:
        result["cache_status"] = (
            "stale_cache_used_due_to_temporary_api_unavailability"
        )
        result["live"] = False
    else:
        result["cache_status"] = "fresh_or_recent_cached_data"
        result["live"] = True

    return result


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

    Production safeguards:
    - shared cache with the forecast endpoint
    - short retry for HTTP 429
    - stale-cache fallback during temporary API failures
    """

    data, used_stale_cache = _get_weather_data(
        latitude=latitude,
        longitude=longitude,
        days=15,
        ttl_seconds=CURRENT_WEATHER_CACHE_TTL_SECONDS
    )

    current = data.get("current")

    if not current:
        raise RuntimeError(
            "Current weather API returned no current data."
        )

    result = {
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

    if used_stale_cache:
        result["cache_status"] = (
            "stale_cache_used_due_to_temporary_api_unavailability"
        )
        result["live"] = False
    else:
        result["cache_status"] = "fresh_or_recent_cached_data"
        result["live"] = True

    return result
