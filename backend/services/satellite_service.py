
import os
import json
import math

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import dotenv_values


# ============================================================
# LOAD CREDENTIALS FROM backend/.env
# ============================================================

BACKEND_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_FILE = os.path.join(
    BACKEND_DIR,
    ".env"
)

env_values = dotenv_values(ENV_FILE)

CDSE_CLIENT_ID = env_values.get(
    "CDSE_CLIENT_ID"
)

CDSE_CLIENT_SECRET = env_values.get(
    "CDSE_CLIENT_SECRET"
)


# ============================================================
# COPERNICUS TOKEN URL
# ============================================================

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/"
    "realms/CDSE/protocol/openid-connect/token"
)


# ============================================================
# COPERNICUS AUTHENTICATION
# ============================================================

def get_cdse_access_token():
    """
    Authenticate with Copernicus Data Space Ecosystem
    using OAuth2 Client Credentials.

    Credentials are loaded from:
        backend/.env
    """

    if not CDSE_CLIENT_ID:
        raise RuntimeError(
            "CDSE_CLIENT_ID is not configured in backend/.env"
        )

    if not CDSE_CLIENT_SECRET:
        raise RuntimeError(
            "CDSE_CLIENT_SECRET is not configured in backend/.env"
        )

    payload = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": CDSE_CLIENT_ID,
            "client_secret": CDSE_CLIENT_SECRET,
        }
    ).encode("utf-8")

    request = Request(
        TOKEN_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded"
        },
    )

    try:
        with urlopen(
            request,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

    except HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            "Copernicus authentication failed "
            f"(HTTP {error.code}): {error_body}"
        )

    except URLError as error:

        raise RuntimeError(
            "Unable to connect to Copernicus authentication "
            "service: "
            f"{error.reason}"
        )

    access_token = data.get(
        "access_token"
    )

    if not access_token:
        raise RuntimeError(
            "Copernicus authentication succeeded "
            "but no access token was returned."
        )

    return access_token


# ============================================================
# TEST COPERNICUS AUTHENTICATION
# ============================================================

def test_cdse_authentication():
    """
    Test Copernicus authentication.
    """

    token = get_cdse_access_token()

    return {
        "authenticated": True,
        "provider":
            "Copernicus Data Space Ecosystem",
        "token_received":
            bool(token),
    }


# ============================================================
# SENTINEL-1 CATALOG SEARCH
# ============================================================

def search_sentinel1(
    bbox=None,
    days_back=30,
    limit=5
):
    """
    Search Sentinel-1 GRD acquisitions over the
    LandGuard study area.

    Returns acquisition metadata only.
    """

    if bbox is None:
        bbox = [
            91.55,
            25.95,
            92.05,
            26.35
        ]

    if days_back < 1:
        raise ValueError(
            "days_back must be at least 1."
        )

    if limit < 1 or limit > 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    access_token = get_cdse_access_token()

    now = datetime.now(
        timezone.utc
    )

    start = (
        now -
        timedelta(days=days_back)
    )

    datetime_range = (
        start.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        + "/"
        +
        now.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    request_body = {
        "bbox": bbox,
        "datetime": datetime_range,
        "collections": [
            "sentinel-1-grd"
        ],
        "limit": limit
    }

    url = (
        "https://sh.dataspace.copernicus.eu/"
        "catalog/v1/search"
    )

    request = Request(
        url,
        data=json.dumps(
            request_body
        ).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type":
                "application/json",

            "Accept":
                "application/geo+json",

            "Authorization":
                f"Bearer {access_token}"
        }
    )

    try:

        with urlopen(
            request,
            timeout=30
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            "Sentinel-1 Catalog API failed "
            f"(HTTP {error.code}): "
            f"{error_body}"
        )

    except URLError as error:

        raise RuntimeError(
            "Unable to connect to Sentinel-1 "
            "Catalog API: "
            f"{error.reason}"
        )

    features = data.get(
        "features",
        []
    )

    acquisitions = []

    for item in features:

        properties = item.get(
            "properties",
            {}
        )

        acquisitions.append(
            {
                "id":
                    item.get("id"),

                "datetime":
                    properties.get(
                        "datetime"
                    ),

                "bbox":
                    item.get("bbox"),

                "collection":
                    "sentinel-1-grd",

                "instrument_mode":
                    properties.get(
                        "sar:instrument_mode"
                    ),

                "orbit_state":
                    properties.get(
                        "sat:orbit_state"
                    ),

                "polarization":
                    properties.get(
                        "s1:polarization"
                    ),

                "resolution":
                    properties.get(
                        "s1:resolution"
                    )
            }
        )

    return {
        "provider":
            "Copernicus Data Space Ecosystem",

        "satellite":
            "Sentinel-1",

        "collection":
            "sentinel-1-grd",

        "study_area": {
            "bbox":
                bbox
        },

        "search_period": {
            "from":
                datetime_range.split("/")[0],

            "to":
                datetime_range.split("/")[1]
        },

        "count":
            len(acquisitions),

        "acquisitions":
            acquisitions
    }


# ============================================================
# SENTINEL-1 EVALSCRIPT
# ============================================================

SENTINEL1_EVALSCRIPT = """
//VERSION=3

function setup() {
    return {
        input: [{
            bands: [
                "VV",
                "VH",
                "dataMask"
            ]
        }],

        output: [
            {
                id: "output_VV",
                bands: 1,
                sampleType: "FLOAT32"
            },

            {
                id: "output_VH",
                bands: 1,
                sampleType: "FLOAT32"
            },

            {
                id: "dataMask",
                bands: 1
            }
        ]
    };
}

function evaluatePixel(samples) {
    return {
        output_VV: [
            samples.VV
        ],

        output_VH: [
            samples.VH
        ],

        dataMask: [
            samples.dataMask
        ]
    };
}
"""


# ============================================================
# INTERNAL SENTINEL-1 STATISTICS REQUEST
# ============================================================

def _request_sentinel1_statistics(
    access_token,
    bbox,
    from_date,
    to_date,
    aggregation_interval="P5D"
):
    """
    Request Sentinel-1 VV/VH statistics for a
    specific observation window.

    P5D is used for the pre/post comparison because
    Sentinel-1 acquisitions over the study area are
    not necessarily available inside a single 24-hour
    interval.
    """

    request_body = {

        "input": {

            "bounds": {

                "bbox":
                    bbox,

                "properties": {

                    "crs":
                        (
                            "http://www.opengis.net/"
                            "def/crs/EPSG/0/4326"
                        )
                }
            },

            "data": [

                {
                    "type":
                        "sentinel-1-grd",

                    "dataFilter": {

                        "polarization":
                            "DV"
                    }
                }
            ]
        },

        "aggregation": {

            "timeRange": {

                "from":
                    from_date,

                "to":
                    to_date
            },

            "aggregationInterval": {

                "of":
                    aggregation_interval
            },

            "evalscript":
                SENTINEL1_EVALSCRIPT,

            "width":
                256,

            "height":
                256
        }
    }

    url = (
        "https://sh.dataspace.copernicus.eu/"
        "statistics/v1"
    )

    request = Request(
        url,
        data=json.dumps(
            request_body
        ).encode("utf-8"),
        method="POST",
        headers={

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",

            "Authorization":
                f"Bearer {access_token}"
        }
    )

    try:

        with urlopen(
            request,
            timeout=60
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            "Sentinel-1 Statistical API failed "
            f"(HTTP {error.code}): {error_body}"
        )

    except URLError as error:

        raise RuntimeError(
            "Unable to connect to Sentinel-1 "
            "Statistical API: "
            f"{error.reason}"
        )

    if data.get("status") != "OK":

        raise RuntimeError(
            "Sentinel-1 Statistical API returned "
            f"an unexpected response: {data}"
        )

    return data


# ============================================================
# SENTINEL-1 STATISTIC EXTRACTION
# ============================================================

def _extract_s1_mean_statistics(
    statistics_response
):
    """
    Extract valid average VV and VH values.

    NaN and infinite values are ignored.
    """

    records = statistics_response.get(
        "data",
        []
    )

    vv_values = []
    vh_values = []

    pixel_count = 0

    for record in records:

        outputs = record.get(
            "outputs",
            {}
        )

        vv_stats = (
            outputs
            .get("output_VV", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )

        vh_stats = (
            outputs
            .get("output_VH", {})
            .get("bands", {})
            .get("B0", {})
            .get("stats", {})
        )

        vv_mean = vv_stats.get(
            "mean"
        )

        vh_mean = vh_stats.get(
            "mean"
        )

        # ----------------------------------------------------
        # VV
        # ----------------------------------------------------

        if vv_mean is not None:

            try:

                vv_number = float(
                    vv_mean
                )

                if math.isfinite(
                    vv_number
                ):

                    vv_values.append(
                        vv_number
                    )

            except (
                TypeError,
                ValueError
            ):

                pass

        # ----------------------------------------------------
        # VH
        # ----------------------------------------------------

        if vh_mean is not None:

            try:

                vh_number = float(
                    vh_mean
                )

                if math.isfinite(
                    vh_number
                ):

                    vh_values.append(
                        vh_number
                    )

            except (
                TypeError,
                ValueError
            ):

                pass

        # ----------------------------------------------------
        # SAMPLE COUNT
        # ----------------------------------------------------

        sample_count = vv_stats.get(
            "sampleCount",
            0
        )

        try:

            pixel_count += int(
                sample_count or 0
            )

        except (
            TypeError,
            ValueError
        ):

            pass

    return {

        "vv_mean":
            (
                sum(vv_values)
                / len(vv_values)
                if vv_values
                else None
            ),

        "vh_mean":
            (
                sum(vh_values)
                / len(vh_values)
                if vh_values
                else None
            ),

        "interval_count":
            max(
                len(vv_values),
                len(vh_values)
            ),

        "pixels_analyzed":
            pixel_count,

        "raw_intervals":
            records
    }


# ============================================================
# SENTINEL-1 STATISTICAL API
# ============================================================

def get_sentinel1_statistics(
    bbox=None,
    days_back=10
):
    """
    Retrieve Sentinel-1 VV/VH backscatter statistics.

    These are satellite observations/statistics.
    They are NOT a final flood/inundation mask.
    """

    if bbox is None:

        bbox = [
            91.68,
            26.10,
            91.78,
            26.20
        ]

    if days_back < 1:

        raise ValueError(
            "days_back must be at least 1."
        )

    access_token = get_cdse_access_token()

    now = datetime.now(
        timezone.utc
    )

    start = (
        now -
        timedelta(
            days=days_back
        )
    )

    from_date = start.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    to_date = now.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    data = _request_sentinel1_statistics(
        access_token=access_token,
        bbox=bbox,
        from_date=from_date,
        to_date=to_date
    )

    return {

        "provider":
            "Copernicus Data Space Ecosystem",

        "satellite":
            "Sentinel-1",

        "collection":
            "sentinel-1-grd",

        "study_area": {

            "bbox":
                bbox
        },

        "time_range": {

            "from":
                from_date,

            "to":
                to_date
        },

        "observation_type":
            "Sentinel-1 SAR backscatter statistics",

        "statistics":
            data
    }


# ============================================================
# SAR RELATIVE CHANGE
# ============================================================

def _calculate_relative_change(
    pre_value,
    post_value
):
    """
    Calculate percentage change:

        ((post - pre) / pre) * 100

    Negative result = decrease.
    """

    if pre_value is None:
        return None

    if post_value is None:
        return None

    try:

        pre_number = float(
            pre_value
        )

        post_number = float(
            post_value
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    if not math.isfinite(
        pre_number
    ):

        return None

    if not math.isfinite(
        post_number
    ):

        return None

    if pre_number == 0:

        return None

    return (
        (
            post_number -
            pre_number
        )
        /
        pre_number
    ) * 100.0


# ============================================================
# SAR DECREASE
# ============================================================

def _calculate_decrease_percent(
    pre_value,
    post_value
):
    """
    Calculate percentage decrease from pre
    to post.

    Positive value = reduction.
    """

    change = _calculate_relative_change(
        pre_value,
        post_value
    )

    if change is None:

        return None

    return max(
        0.0,
        -change
    )


# ============================================================
# SENTINEL-1 PRE/POST CHANGE DETECTION
# ============================================================

def get_sentinel1_change_detection(
    bbox=None,
    days_back=30,
    min_gap_days=3
):
    """
    Compare two actual Sentinel-1 observations.

    The function searches for real Sentinel-1 GRD
    acquisitions and selects:

        latest acquisition
        previous sufficiently separated acquisition

    IMPORTANT:

    This produces an aggregated SAR change signal.

    It is NOT a pixel-level inundation mask.
    """

    # --------------------------------------------------------
    # DEFAULT STUDY AREA
    # --------------------------------------------------------

    if bbox is None:

        bbox = [
            91.68,
            26.10,
            91.78,
            26.20
        ]

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if days_back < 5:

        raise ValueError(
            "days_back must be at least 5."
        )

    if min_gap_days < 1:

        raise ValueError(
            "min_gap_days must be at least 1."
        )

    if min_gap_days >= days_back:

        raise ValueError(
            "min_gap_days must be smaller than days_back."
        )

    # --------------------------------------------------------
    # SEARCH ACTUAL SENTINEL-1 ACQUISITIONS
    # --------------------------------------------------------

    catalog = search_sentinel1(
        bbox=bbox,
        days_back=days_back,
        limit=20
    )

    acquisitions = catalog.get(
        "acquisitions",
        []
    )

    valid_acquisitions = []

    # --------------------------------------------------------
    # PARSE ACQUISITION TIMES
    # --------------------------------------------------------

    for item in acquisitions:

        timestamp = item.get(
            "datetime"
        )

        if not timestamp:
            continue

        try:

            acquisition_time = (
                datetime.fromisoformat(
                    timestamp.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            valid_acquisitions.append(
                {
                    **item,

                    "parsed_datetime":
                        acquisition_time
                }
            )

        except (
            ValueError,
            TypeError
        ):

            continue

    # --------------------------------------------------------
    # NEWEST FIRST
    # --------------------------------------------------------

    valid_acquisitions.sort(
        key=lambda item:
            item["parsed_datetime"],
        reverse=True
    )

    # --------------------------------------------------------
    # NEED TWO ACQUISITIONS
    # --------------------------------------------------------

    if len(valid_acquisitions) < 2:

        return {

            "status":
                "insufficient_data",

            "provider":
                "Copernicus Data Space Ecosystem",

            "satellite":
                "Sentinel-1",

            "collection":
                "sentinel-1-grd",

            "study_area": {

                "bbox":
                    bbox
            },

            "observation_type":
                "Sentinel-1 SAR pre/post change detection",

            "message":
                (
                    "Fewer than two valid Sentinel-1 "
                    "acquisitions were found in the "
                    "selected period."
                ),

            "acquisition_count":
                len(valid_acquisitions),

            "acquisitions":
                valid_acquisitions
        }

    # --------------------------------------------------------
    # LATEST ACQUISITION
    # --------------------------------------------------------

    post_acquisition = (
        valid_acquisitions[0]
    )

    post_time = (
        post_acquisition[
            "parsed_datetime"
        ]
    )

    # --------------------------------------------------------
    # PREVIOUS SUFFICIENTLY SEPARATED ACQUISITION
    # --------------------------------------------------------

    pre_acquisition = None

    for candidate in (
        valid_acquisitions[1:]
    ):

        candidate_time = (
            candidate[
                "parsed_datetime"
            ]
        )

        gap_days = (
            post_time -
            candidate_time
        ).total_seconds() / 86400.0

        if gap_days >= min_gap_days:

            pre_acquisition = candidate

            break

    # --------------------------------------------------------
    # NO SUITABLE PREVIOUS ACQUISITION
    # --------------------------------------------------------

    if pre_acquisition is None:

        return {

            "status":
                "insufficient_data",

            "provider":
                "Copernicus Data Space Ecosystem",

            "satellite":
                "Sentinel-1",

            "collection":
                "sentinel-1-grd",

            "study_area": {

                "bbox":
                    bbox
            },

            "observation_type":
                "Sentinel-1 SAR pre/post change detection",

            "message":
                (
                    "Multiple Sentinel-1 acquisitions "
                    "were found, but no earlier acquisition "
                    "with the required time separation "
                    "was available."
                ),

            "acquisition_count":
                len(valid_acquisitions),

            "acquisitions":
                valid_acquisitions
        }

    # --------------------------------------------------------
    # ACTUAL ACQUISITION TIMES
    # --------------------------------------------------------

    pre_time = (
        pre_acquisition[
            "parsed_datetime"
        ]
    )

    actual_gap_days = (
        post_time -
        pre_time
    ).total_seconds() / 86400.0

    # ========================================================
    # FIVE-DAY WINDOWS AROUND ACTUAL ACQUISITIONS
    #
    # 60 hours before + 60 hours after = 5 days.
    #
    # IMPORTANT:
    # This entire section MUST remain INSIDE the function.
    # ========================================================

    WINDOW_HALF = timedelta(
        hours=60
    )

    pre_from_time = (
        pre_time -
        WINDOW_HALF
    )

    pre_to_time = (
        pre_time +
        WINDOW_HALF
    )

    post_from_time = (
        post_time -
        WINDOW_HALF
    )

    post_to_time = (
        post_time +
        WINDOW_HALF
    )

    pre_from = (
        pre_from_time.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    pre_to = (
        pre_to_time.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    post_from = (
        post_from_time.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    post_to = (
        post_to_time.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    access_token = get_cdse_access_token()

    # --------------------------------------------------------
    # PRE-EVENT / EARLIER OBSERVATION
    # --------------------------------------------------------

    pre_statistics = (
        _request_sentinel1_statistics(
            access_token=access_token,
            bbox=bbox,
            from_date=pre_from,
            to_date=pre_to
        )
    )

    # --------------------------------------------------------
    # POST-EVENT / LATEST OBSERVATION
    # --------------------------------------------------------

    post_statistics = (
        _request_sentinel1_statistics(
            access_token=access_token,
            bbox=bbox,
            from_date=post_from,
            to_date=post_to
        )
    )

    # --------------------------------------------------------
    # EXTRACT VALID VV/VH
    # --------------------------------------------------------

    pre = (
        _extract_s1_mean_statistics(
            pre_statistics
        )
    )

    post = (
        _extract_s1_mean_statistics(
            post_statistics
        )
    )

    # --------------------------------------------------------
    # CALCULATE VV CHANGE
    # --------------------------------------------------------

    vv_change = (
        _calculate_relative_change(
            pre["vv_mean"],
            post["vv_mean"]
        )
    )

    # --------------------------------------------------------
    # CALCULATE VH CHANGE
    # --------------------------------------------------------

    vh_change = (
        _calculate_relative_change(
            pre["vh_mean"],
            post["vh_mean"]
        )
    )

    # --------------------------------------------------------
    # CALCULATE DECREASE
    # --------------------------------------------------------

    vv_decrease = (
        _calculate_decrease_percent(
            pre["vv_mean"],
            post["vv_mean"]
        )
    )

    vh_decrease = (
        _calculate_decrease_percent(
            pre["vh_mean"],
            post["vh_mean"]
        )
    )

    # --------------------------------------------------------
    # CHANGE SIGNAL
    # --------------------------------------------------------

    decrease_values = [
        value

        for value in [
            vv_decrease,
            vh_decrease
        ]

        if value is not None
    ]

    if decrease_values:

        change_signal = (
            sum(decrease_values)
            /
            len(decrease_values)
        )

    else:

        change_signal = None

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    if change_signal is None:

        change_level = (
            "INSUFFICIENT SAR DATA"
        )

    elif change_signal >= 30:

        change_level = (
            "HIGH CHANGE SIGNAL"
        )

    elif change_signal >= 15:

        change_level = (
            "MODERATE CHANGE SIGNAL"
        )

    elif change_signal >= 5:

        change_level = (
            "WEAK CHANGE SIGNAL"
        )

    else:

        change_level = (
            "STABLE / LOW CHANGE SIGNAL"
        )

    # --------------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------------

    if change_signal is None:

        interpretation = (
            "The selected Sentinel-1 acquisitions "
            "did not provide finite VV/VH statistics "
            "for both observations. No SAR change "
            "signal was calculated."
        )

    elif change_signal >= 15:

        interpretation = (
            "A noticeable decrease in aggregated "
            "Sentinel-1 backscatter was detected "
            "between the selected acquisitions. "
            "This can be consistent with surface-water "
            "or inundation change, but spatial processing "
            "and event-based validation are required "
            "before calling it confirmed inundation."
        )

    elif change_signal >= 5:

        interpretation = (
            "A weak aggregated SAR backscatter change "
            "was detected between the selected "
            "acquisitions. Continued monitoring and "
            "spatial pre/post analysis are recommended."
        )

    else:

        interpretation = (
            "No strong aggregated SAR backscatter "
            "decrease was detected between the selected "
            "Sentinel-1 acquisitions."
        )

    # --------------------------------------------------------
    # RETURN LANDGUARD RESULT
    # --------------------------------------------------------

    return {

        "status":
            "success",

        "provider":
            "Copernicus Data Space Ecosystem",

        "satellite":
            "Sentinel-1",

        "collection":
            "sentinel-1-grd",

        "study_area": {

            "bbox":
                bbox
        },

        "observation_type":
            (
                "Sentinel-1 SAR "
                "acquisition-to-acquisition "
                "change detection"
            ),

        "pre_event": {

            "acquisition_id":
                pre_acquisition.get(
                    "id"
                ),

            "acquisition_datetime":
                pre_acquisition.get(
                    "datetime"
                ),

            "orbit_state":
                pre_acquisition.get(
                    "orbit_state"
                ),

            "from":
                pre_from,

            "to":
                pre_to,

            "gap_from_latest_days":
                round(
                    actual_gap_days,
                    2
                ),

            "vv_mean":
                pre["vv_mean"],

            "vh_mean":
                pre["vh_mean"],

            "pixels_analyzed":
                pre["pixels_analyzed"]
        },

        "post_event": {

            "acquisition_id":
                post_acquisition.get(
                    "id"
                ),

            "acquisition_datetime":
                post_acquisition.get(
                    "datetime"
                ),

            "orbit_state":
                post_acquisition.get(
                    "orbit_state"
                ),

            "from":
                post_from,

            "to":
                post_to,

            "vv_mean":
                post["vv_mean"],

            "vh_mean":
                post["vh_mean"],

            "pixels_analyzed":
                post["pixels_analyzed"]
        },

        "change_detection": {

            "vv_change_percent":
                (
                    round(
                        vv_change,
                        2
                    )
                    if vv_change is not None
                    else None
                ),

            "vh_change_percent":
                (
                    round(
                        vh_change,
                        2
                    )
                    if vh_change is not None
                    else None
                ),

            "vv_decrease_percent":
                (
                    round(
                        vv_decrease,
                        2
                    )
                    if vv_decrease is not None
                    else None
                ),

            "vh_decrease_percent":
                (
                    round(
                        vh_decrease,
                        2
                    )
                    if vh_decrease is not None
                    else None
                ),

            "change_signal_percent":
                (
                    round(
                        change_signal,
                        2
                    )
                    if change_signal is not None
                    else None
                ),

            "change_level":
                change_level,

            "interpretation":
                interpretation
        },

        "validation_status":
            "AGGREGATED SAR CHANGE SIGNAL",

        "limitations": [

            "This is not a pixel-level inundation mask.",

            "Aggregated SAR change can be caused by factors other than flooding.",

            "Spatial pre/post classification is required for confirmed inundation extent.",

            "Acquisition geometry, land-cover changes, and other SAR effects should be considered during validation.",

            "Event-based validation should compare the resulting inundation map against independent observations."
        ]
    }
