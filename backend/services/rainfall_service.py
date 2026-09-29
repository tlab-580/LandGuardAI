import os
import json
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ============================================================
# OPEN-METEO / NWP CONFIGURATION
# ============================================================

# Free endpoints are retained as a local-development fallback.
FREE_ECMWF_API_URL = "https://api.open-meteo.com/v1/ecmwf"
FREE_GFS_API_URL = "https://api.open-meteo.com/v1/gfs"

# Customer API provides a dedicated quota and accepts the same
# request syntax, with the addition of the API key.
CUSTOMER_ECMWF_API_URL = (
    "https://customer-api.open-meteo.com/v1/ecmwf"
)
CUSTOMER_GFS_API_URL = (
    "https://customer-api.open-meteo.com/v1/gfs"
)

OPEN_METEO_API_KEY = os.getenv(
    "OPEN_METEO_API_KEY",
    ""
).strip()

# Cache successful provider responses in memory so repeated
# dashboard requests do not repeatedly hit the external API.
FORECAST_CACHE_TTL_SECONDS = 15 * 60
CURRENT_WEATHER_CACHE_TTL_SECONDS = 5 * 60

# Short retry schedule for transient HTTP 429 responses.
MAX_429_RETRIES = 2
RETRY_DELAYS_SECONDS = [2, 4]

_CACHE_LOCK = threading.Lock()

# Cache key -> {
#   "timestamp": float,
#   "data": dict,
#   "model": str,
#   "provider": str,
#   "source_url": str,
# }
_OPEN_METEO_CACHE = {}


# ============================================================
# CACHE HELPERS
# ============================================================

def _cache_key(latitude: float, longitude: float):
    return (
        round(float(latitude), 4),
        round(float(longitude), 4)
    )


def _get_cached_weather(
    latitude: float,
    longitude: float,
    ttl_seconds: int
):
    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        cached = _OPEN_METEO_CACHE.get(key)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age > ttl_seconds:
            return None

        return cached


def _get_stale_cached_weather(
    latitude: float,
    longitude: float
):
    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        return _OPEN_METEO_CACHE.get(key)


def _store_cached_weather(
    latitude: float,
    longitude: float,
    data: dict,
    model: str,
    source_url: str
):
    key = _cache_key(latitude, longitude)

    with _CACHE_LOCK:
        _OPEN_METEO_CACHE[key] = {
            "timestamp": time.time(),
            "data": data,
            "model": model,
            "provider": "Open-Meteo",
            "source_url": source_url,
        }


# ============================================================
# REQUEST BUILDERS
# ============================================================

def _build_hourly_params(
    latitude: float,
    longitude: float,
    days: int
):
    return {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "soil_moisture_0_to_10cm"
        ),
        "timezone": "auto",
        "forecast_days": days,
    }


# ============================================================
# NWP REQUEST
# ============================================================

def _request_model(
    base_url: str,
    model_name: str,
    latitude: float,
    longitude: float,
    days: int
):
    params = _build_hourly_params(
        latitude,
        longitude,
        days
    )

    if base_url.startswith("https://customer-api.open-meteo.com"):
        if not OPEN_METEO_API_KEY:
            raise RuntimeError(
                "OPEN_METEO_API_KEY is not configured for the "
                "Open-Meteo customer API."
            )

        params["apikey"] = OPEN_METEO_API_KEY

    url = (
        base_url
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

            if not data.get("hourly"):
                raise RuntimeError(
                    f"{model_name} returned no hourly forecast data."
                )

            _store_cached_weather(
                latitude=latitude,
                longitude=longitude,
                data=data,
                model=model_name,
                source_url=url
            )

            return data, model_name, False

        except HTTPError as error:

            last_error = error

            if (
                error.code == 429
                and attempt < MAX_429_RETRIES
            ):
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

                # Do not allow an unexpectedly large server value
                # to block the FastAPI request for a long time.
                delay = max(1, min(delay, 8))
                time.sleep(delay)
                continue

            raise RuntimeError(
                f"{model_name} API returned HTTP {error.code}"
            )

        except URLError as error:

            last_error = error
            raise RuntimeError(
                f"Unable to connect to {model_name} API: "
                f"{error.reason}"
            )

        except (
            TimeoutError,
            json.JSONDecodeError
        ) as error:

            last_error = error
            raise RuntimeError(
                f"{model_name} API returned an invalid or "
                f"timed-out response: {error}"
            )

    raise RuntimeError(
        f"{model_name} API request failed: {last_error}"
    )


def _get_weather_data(
    latitude: float,
    longitude: float,
    days: int,
    ttl_seconds: int
):
    """
    Provider order:

    1. Recent successful cache
    2. ECMWF IFS
    3. NOAA GFS through Open-Meteo
    4. Stale successful cache

    The result records which NWP model actually supplied the data.
    """

    cached = _get_cached_weather(
        latitude=latitude,
        longitude=longitude,
        ttl_seconds=ttl_seconds
    )

    if cached is not None:
        return cached, False

    errors = []

    if OPEN_METEO_API_KEY:
        providers = [
            (
                CUSTOMER_ECMWF_API_URL,
                "ECMWF IFS"
            ),
            (
                CUSTOMER_GFS_API_URL,
                "NOAA GFS"
            ),
        ]
    else:
        # Local development can still use the free endpoints.
        # Render/production should set OPEN_METEO_API_KEY so the
        # customer endpoint with dedicated capacity is used.
        providers = [
            (
                FREE_ECMWF_API_URL,
                "ECMWF IFS"
            ),
            (
                FREE_GFS_API_URL,
                "NOAA GFS"
            ),
        ]

    for base_url, model_name in providers:

        try:

            data, resolved_model, _ = _request_model(
                base_url=base_url,
                model_name=model_name,
                latitude=latitude,
                longitude=longitude,
                days=days
            )

            cached_result = _get_stale_cached_weather(
                latitude,
                longitude
            )

            return cached_result, False

        except RuntimeError as error:

            errors.append(
                f"{model_name}: {error}"
            )

    stale = _get_stale_cached_weather(
        latitude,
        longitude
    )

    if stale is not None:
        print(
            "NWP providers temporarily unavailable; "
            "using last successful cached response. "
            + " | ".join(errors)
        )
        return stale, True

    raise RuntimeError(
        "All configured NWP providers are currently unavailable. "
        + " | ".join(errors)
    )


# ============================================================
# HOURLY -> DAILY AGGREGATION
# ============================================================

def _aggregate_daily_forecast(data: dict):
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    temperature = hourly.get(
        "temperature_2m", []
    )
    precipitation = hourly.get(
        "precipitation", []
    )
    rain = hourly.get(
        "rain", []
    )

    daily = {}

    for i, timestamp in enumerate(times):

        date = str(timestamp).split("T")[0]

        entry = daily.setdefault(
            date,
            {
                "rainfall": 0.0,
                "precipitation": 0.0,
                "temperatures": [],
                "precipitation_hours": 0.0,
            }
        )

        rain_value = (
            rain[i]
            if i < len(rain)
            else None
        )

        precipitation_value = (
            precipitation[i]
            if i < len(precipitation)
            else None
        )

        temperature_value = (
            temperature[i]
            if i < len(temperature)
            else None
        )

        if rain_value is not None:
            try:
                rain_number = float(rain_value)
                entry["rainfall"] += max(
                    0.0,
                    rain_number
                )
            except (TypeError, ValueError):
                pass

        if precipitation_value is not None:
            try:
                precipitation_number = float(
                    precipitation_value
                )
                entry["precipitation"] += max(
                    0.0,
                    precipitation_number
                )

                if precipitation_number > 0:
                    # Open-Meteo hourly series can become coarser
                    # farther into the forecast. We preserve a
                    # conservative sample-hour count here.
                    entry["precipitation_hours"] += 1.0

            except (TypeError, ValueError):
                pass

        if temperature_value is not None:
            try:
                entry["temperatures"].append(
                    float(temperature_value)
                )
            except (TypeError, ValueError):
                pass

    forecast = []

    for day_number, (date, values) in enumerate(
        daily.items(),
        start=1
    ):

        temperatures = values["temperatures"]

        forecast.append({
            "day": day_number,
            "date": date,
            "rainfall": round(
                values["rainfall"],
                2
            ),
            "precipitation": round(
                values["precipitation"],
                2
            ),
            "temperature_max": (
                round(
                    max(temperatures),
                    1
                )
                if temperatures
                else None
            ),
            "temperature_min": (
                round(
                    min(temperatures),
                    1
                )
                if temperatures
                else None
            ),
            "precipitation_hours": round(
                values["precipitation_hours"],
                1
            ),
        })

    return forecast


# ============================================================
# CURRENT HOURLY CONDITIONS
# ============================================================

def _extract_current_conditions(data: dict):
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        raise RuntimeError(
            "NWP response returned no hourly time values."
        )

    timezone_name = data.get(
        "timezone",
        "UTC"
    )

    try:
        local_now = datetime.now(
            ZoneInfo(timezone_name)
        )
    except Exception:
        local_now = datetime.now()

    target_date = local_now.strftime(
        "%Y-%m-%d"
    )
    target_hour = local_now.strftime(
        "%Y-%m-%dT%H:00"
    )

    best_index = None

    for i, timestamp in enumerate(times):
        if str(timestamp).startswith(target_hour):
            best_index = i
            break

    if best_index is None:
        # Fall back to the latest forecast timestamp that is not
        # later than the current local hour.
        try:
            parsed_times = [
                datetime.fromisoformat(
                    str(timestamp).replace("Z", "")
                )
                for timestamp in times
            ]
            naive_now = local_now.replace(tzinfo=None)

            candidates = [
                (i, item_time)
                for i, item_time in enumerate(parsed_times)
                if item_time <= naive_now
            ]

            if candidates:
                best_index = max(
                    candidates,
                    key=lambda item: item[1]
                )[0]
            else:
                best_index = 0

        except (TypeError, ValueError):
            best_index = 0

    def value(name, default=None):
        values = hourly.get(name, [])
        if best_index >= len(values):
            return default
        return values[best_index]

    return {
        "time": times[best_index],
        "temperature": value("temperature_2m"),
        "relative_humidity": value(
            "relative_humidity_2m"
        ),
        "precipitation": value(
            "precipitation"
        ),
        "rainfall": value("rain"),
        "weather_code": value("weather_code"),
        "wind_speed": value("wind_speed_10m"),
        "soil_moisture": value(
            "soil_moisture_0_to_10cm"
        ),
    }


# ============================================================
# REAL METEOROLOGICAL FORECAST
# ============================================================

def generate_meteorological_forecast(
    latitude: float,
    longitude: float,
    days: int = 15
):
    """
    Returns real NWP rainfall/weather forecast data.

    Primary model:
        ECMWF IFS

    Fallback model:
        NOAA GFS through Open-Meteo

    The returned payload explicitly identifies the model that
    supplied the data. No synthetic rainfall values are created.
    """

    if days < 1 or days > 15:
        raise ValueError(
            "Real meteorological forecast supports 1 to 15 days."
        )

    cached, used_stale_cache = _get_weather_data(
        latitude=latitude,
        longitude=longitude,
        days=days,
        ttl_seconds=FORECAST_CACHE_TTL_SECONDS
    )

    data = cached["data"]
    model = cached["model"]
    provider = cached["provider"]

    forecast = _aggregate_daily_forecast(
        data
    )[:days]

    result = {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "model": model,
        "provider": provider,
        "forecast_days": len(forecast),
        "data_type": "Numerical Weather Prediction",
        "forecast": [],
    }

    for item in forecast:
        result["forecast"].append({
            **item,
            "source": model,
            "provider": provider,
            "data_type": "Numerical Weather Prediction"
        })

    if used_stale_cache:
        result["live"] = False
        result["cache_status"] = (
            "stale_cache_used_due_to_temporary_api_unavailability"
        )
    else:
        result["live"] = True
        result["cache_status"] = "fresh_or_recent_cached_data"

    result["api_access"] = (
        "Open-Meteo customer API"
        if OPEN_METEO_API_KEY
        else "Open-Meteo free API"
    )

    return result


# ============================================================
# EXISTING SCENARIO GENERATOR
# ============================================================

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


# ============================================================
# CURRENT METEOROLOGICAL DATA
# ============================================================

def generate_current_weather(
    latitude: float,
    longitude: float
):
    """
    Returns current meteorological conditions from the same NWP
    data pipeline used by the forecast endpoint.

    Provider/model are reported explicitly, and the stale-cache
    state is exposed when upstream services are temporarily down.
    """

    cached, used_stale_cache = _get_weather_data(
        latitude=latitude,
        longitude=longitude,
        days=15,
        ttl_seconds=CURRENT_WEATHER_CACHE_TTL_SECONDS
    )

    data = cached["data"]
    model = cached["model"]
    provider = cached["provider"]

    current = _extract_current_conditions(
        data
    )

    result = {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "time": current["time"],
        "temperature": current["temperature"],
        "relative_humidity": current[
            "relative_humidity"
        ],
        "precipitation": current[
            "precipitation"
        ],
        "rainfall": current["rainfall"],
        "weather_code": current["weather_code"],
        "wind_speed": current["wind_speed"],
        "soil_moisture": current["soil_moisture"],
        "provider": provider,
        "model": model,
        "data_type": "Current meteorological data"
    }

    if used_stale_cache:
        result["live"] = False
        result["cache_status"] = (
            "stale_cache_used_due_to_temporary_api_unavailability"
        )
    else:
        result["live"] = True
        result["cache_status"] = "fresh_or_recent_cached_data"

    result["api_access"] = (
        "Open-Meteo customer API"
        if OPEN_METEO_API_KEY
        else "Open-Meteo free API"
    )

    return result
