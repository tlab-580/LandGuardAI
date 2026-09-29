
import os
import base64
import json
import math

from io import BytesIO
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from PIL import Image

from backend.services.satellite_service import (
    get_cdse_access_token,
    search_sentinel1,
)


# ============================================================
# COPERNICUS SENTINEL-1 PROCESS API
# ============================================================

PROCESS_URL = (
    "https://sh.dataspace.copernicus.eu/process/v1"
)


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_BBOX = [
    91.68,
    26.10,
    91.78,
    26.20,
]

DEFAULT_CHANGE_THRESHOLD_DB = -3.0

DEFAULT_RESOLUTION_METERS = 20


# ============================================================
# DATETIME PARSER
# ============================================================

def _parse_datetime(value):
    """
    Convert Sentinel-1 catalog datetime into
    a timezone-aware UTC datetime.
    """

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(timezone.utc)


# ============================================================
# PUBLIC ACQUISITION FORMATTER
# ============================================================

def _public_acquisition(item):
    """
    Remove internal Python datetime objects before
    returning data through FastAPI.
    """

    return {
        key: value
        for key, value in item.items()
        if key != "parsed_datetime"
    }


# ============================================================
# SENTINEL-1 ACQUISITION PAIR SELECTION
# ============================================================

def _select_acquisition_pair(
    bbox,
    days_back=30,
    min_gap_days=5,
):
    """
    Search real Sentinel-1 acquisitions and select:

    POST:
        Latest available Sentinel-1 acquisition.

    PRE:
        Previous acquisition that is at least
        min_gap_days before the latest acquisition.
    """

    search_result = search_sentinel1(
        bbox=bbox,
        days_back=days_back,
        limit=20,
    )

    acquisitions = search_result.get(
        "acquisitions",
        [],
    )

    valid = []

    for item in acquisitions:

        acquisition_datetime = item.get(
            "datetime"
        )

        if not acquisition_datetime:
            continue

        try:
            parsed_datetime = _parse_datetime(
                acquisition_datetime
            )

        except Exception:
            continue

        copied = dict(item)

        copied["parsed_datetime"] = (
            parsed_datetime
        )

        valid.append(copied)

    valid.sort(
        key=lambda item: item["parsed_datetime"],
        reverse=True,
    )

    if len(valid) < 2:

        raise ValueError(
            "Not enough Sentinel-1 acquisitions were "
            "found for pixel-level change detection."
        )

    # --------------------------------------------------------
    # LATEST = POST EVENT
    # --------------------------------------------------------

    post = valid[0]

    post_time = post[
        "parsed_datetime"
    ]

    # --------------------------------------------------------
    # FIND PRE-EVENT ACQUISITION
    # --------------------------------------------------------

    pre = None

    for candidate in valid[1:]:

        candidate_time = candidate[
            "parsed_datetime"
        ]

        gap_days = (
            post_time - candidate_time
        ).total_seconds() / 86400.0

        if gap_days >= min_gap_days:

            pre = candidate

            break

    if pre is None:

        raise ValueError(
            "No Sentinel-1 acquisition pair with a "
            f"gap of at least {min_gap_days} days "
            "was found."
        )

    # --------------------------------------------------------
    # ACTUAL TEMPORAL GAP
    # --------------------------------------------------------

    actual_gap_days = (
        post_time - pre["parsed_datetime"]
    ).total_seconds() / 86400.0

    return (
        pre,
        post,
        actual_gap_days,
    )


# ============================================================
# SENTINEL-1 MULTI-TEMPORAL EVALSCRIPT
# ============================================================

def _build_evalscript(
    pre_date,
    post_date,
    threshold_db,
):
    """
    Build a multi-temporal Sentinel-1 VV change
    detection evalscript.

    IMPORTANT:

    The output uses four channels:

        R:
            255 for potential inundation/change.

        G:
            255 for valid non-candidate pixels.

        B:
            0.

        A:
            180 for candidate pixels.
            100 for valid non-candidate pixels.
            0 for invalid pixels.

    This allows Python to distinguish:

        1. invalid pixels
        2. valid non-candidate pixels
        3. potential inundation pixels

    Previously, transparent non-candidate pixels were
    excluded from valid_pixels, which could make the
    candidate percentage incorrectly appear as 100%.
    """

    return f"""
//VERSION=3

var PRE_DATE = "{pre_date}";
var POST_DATE = "{post_date}";
var THRESHOLD_DB = {threshold_db};


function setup() {{

    return {{

        input: [
            {{
                bands: [
                    "VV",
                    "VH",
                    "dataMask"
                ]
            }}
        ],

        mosaicking: Mosaicking.ORBIT,

        output: {{

            id: "default",

            bands: 4,

            sampleType: SampleType.UINT8
        }}
    }};
}}


function preProcessScenes(collections) {{

    /*
     * Keep only the two requested acquisition dates.
     */

    collections.scenes.orbits =
        collections.scenes.orbits.filter(
            function(orbit) {{

                var orbitDate =
                    orbit.dateFrom.split("T")[0];

                return (
                    orbitDate === PRE_DATE ||
                    orbitDate === POST_DATE
                );
            }}
        );

    return collections;
}}


function findSample(
    samples,
    scenes,
    targetDate
) {{

    /*
     * Find the sample corresponding to the
     * requested acquisition date.
     */

    for (
        var i = 0;
        i < samples.length;
        i++
    ) {{

        if (
            !scenes.orbits[i]
        ) {{
            continue;
        }}

        var sceneDate =
            scenes.orbits[i]
                .dateFrom
                .split("T")[0];

        if (
            sceneDate === targetDate
        ) {{

            return samples[i];
        }}
    }}

    return null;
}}


function evaluatePixel(
    samples,
    scenes
) {{

    /*
     * Retrieve the two temporal observations.
     */

    var pre =
        findSample(
            samples,
            scenes,
            PRE_DATE
        );

    var post =
        findSample(
            samples,
            scenes,
            POST_DATE
        );


    /*
     * Invalid if one of the required
     * acquisitions is unavailable.
     */

    if (
        pre === null ||
        post === null
    ) {{

        return [
            0,
            0,
            0,
            0
        ];
    }}


    /*
     * Require valid observations from
     * both acquisitions.
     */

    if (
        pre.dataMask === 0 ||
        post.dataMask === 0
    ) {{

        return [
            0,
            0,
            0,
            0
        ];
    }}


    /*
     * Ignore zero / invalid backscatter.
     */

    if (
        pre.VV <= 0 ||
        post.VV <= 0
    ) {{

        return [
            0,
            0,
            0,
            0
        ];
    }}


    /*
     * Sentinel-1 VV is handled as linear
     * backscatter power.
     *
     * Convert the post/pre ratio into dB.
     */

    var vvChangeDb =
        10 * Math.log10(
            post.VV / pre.VV
        );


    /*
     * Strong negative VV change.
     *
     * This is a POTENTIAL inundation/change
     * candidate, not a confirmed flood pixel.
     */

    if (
        vvChangeDb <= THRESHOLD_DB
    ) {{

        return [
            255,
            50,
            50,
            180
        ];
    }}


    /*
     * Valid pixel but not a candidate.
     *
     * GREEN is used so Python can count this
     * pixel as valid.
     */

    return [
        0,
        255,
        0,
        100
    ];
}}
"""
    

# ============================================================
# COPERNICUS PROCESS API REQUEST
# ============================================================

def _request_inundation_map(
    access_token,
    bbox,
    pre_datetime,
    post_datetime,
    threshold_db,
):
    """
    Request a pixel-level Sentinel-1 change image
    from the Copernicus Data Space Processing API.
    """

    pre_date = (
        pre_datetime.strftime(
            "%Y-%m-%d"
        )
    )

    post_date = (
        post_datetime.strftime(
            "%Y-%m-%d"
        )
    )


    # --------------------------------------------------------
    # REQUEST TIME WINDOW
    # --------------------------------------------------------

    start_time = (
        pre_datetime - timedelta(days=1)
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    end_time = (
        post_datetime + timedelta(days=1)
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


    # --------------------------------------------------------
    # EVALSCRIPT
    # --------------------------------------------------------

    evalscript = _build_evalscript(
        pre_date=pre_date,
        post_date=post_date,
        threshold_db=threshold_db,
    )


    # --------------------------------------------------------
    # COPERNICUS REQUEST BODY
    # --------------------------------------------------------

    request_body = {

        "input": {

            "bounds": {

                "bbox": bbox,

                "properties": {

                    "crs": (
                        "http://www.opengis.net/def/"
                        "crs/OGC/1.3/CRS84"
                    )
                },
            },

            "data": [

                {

                    "type":
                        "sentinel-1-grd",

                    "dataFilter": {

                        "timeRange": {

                            "from":
                                start_time,

                            "to":
                                end_time,
                        }
                    },

                    "processing": {

                        "orthorectify":
                            "true",

                        "demInstance":
                            "COPERNICUS_30",

                        "backCoeff":
                            "GAMMA0_TERRAIN",
                    },
                }
            ],
        },


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        "output": {

            "width":
                512,

            "height":
                512,

            "responses": [

                {

                    "identifier":
                        "default",

                    "format": {

                        "type":
                            "image/png"
                    },
                }
            ],
        },


        "evalscript":
            evalscript,
    }


    # --------------------------------------------------------
    # HTTP REQUEST
    # --------------------------------------------------------

    request = Request(

        PROCESS_URL,

        data=json.dumps(
            request_body
        ).encode("utf-8"),

        method="POST",

        headers={

            "Authorization":
                f"Bearer {access_token}",

            "Content-Type":
                "application/json",

            "Accept":
                "image/png",
        },
    )


    # --------------------------------------------------------
    # SEND REQUEST
    # --------------------------------------------------------

    try:

        with urlopen(
            request,
            timeout=180
        ) as response:

            image_bytes = (
                response.read()
            )


    except HTTPError as exc:

        error_body = (
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise RuntimeError(
            "Copernicus Process API returned "
            f"HTTP {exc.code}: {error_body}"
        ) from exc


    except URLError as exc:

        raise RuntimeError(
            "Unable to connect to Copernicus "
            f"Process API: {exc}"
        ) from exc


    # --------------------------------------------------------
    # VALIDATE RESPONSE
    # --------------------------------------------------------

    if not image_bytes:

        raise RuntimeError(
            "Copernicus returned an empty "
            "inundation image."
        )


    return image_bytes


# ============================================================
# MASK ANALYSIS
# ============================================================

def _analyze_mask(
    image_bytes,
    bbox,
):
    """
    Analyze the returned RGBA PNG.

    Pixel encoding:

        Candidate:
            R >= 200
            G <= 100
            B <= 100
            A > 0

        Valid non-candidate:
            G >= 150
            A > 0

        Invalid:
            A == 0

    This ensures valid_pixels means:

        candidate + valid non-candidate

    rather than only candidate pixels.
    """

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGBA")


    width, height = image.size

    pixels = image.load()


    valid_pixels = 0

    potential_pixels = 0


    # --------------------------------------------------------
    # PIXEL COUNTING
    # --------------------------------------------------------

    for y in range(height):

        for x in range(width):

            red, green, blue, alpha = (
                pixels[x, y]
            )


            # ------------------------------------------------
            # INVALID
            # ------------------------------------------------

            if alpha == 0:

                continue


            # ------------------------------------------------
            # VALID PIXEL
            # ------------------------------------------------

            valid_pixels += 1


            # ------------------------------------------------
            # POTENTIAL INUNDATION
            # ------------------------------------------------

            if (
                red >= 200
                and green <= 100
                and blue <= 100
            ):

                potential_pixels += 1


    # --------------------------------------------------------
    # PERCENTAGE
    # --------------------------------------------------------

    if valid_pixels > 0:

        potential_percent = (
            potential_pixels
            / valid_pixels
            * 100.0
        )

    else:

        potential_percent = 0.0


    return {

        "width":
            width,

        "height":
            height,

        "total_pixels":
            width * height,

        "valid_pixels":
            valid_pixels,

        "potential_inundation_pixels":
            potential_pixels,

        "potential_inundation_percent":
            round(
                potential_percent,
                2,
            ),
    }


# ============================================================
# BBOX AREA ESTIMATION
# ============================================================

def _estimate_bbox_area_km2(
    bbox,
):
    """
    Approximate the geographic area of the
    rectangular study-area bounding box.

    This is an approximate area calculation and
    should not be interpreted as the exact area
    of an inundated polygon.
    """

    west, south, east, north = bbox

    earth_radius_km = 6371.0088


    # --------------------------------------------------------
    # LATITUDE
    # --------------------------------------------------------

    lat1 = (
        south
        * math.pi
        / 180.0
    )

    lat2 = (
        north
        * math.pi
        / 180.0
    )


    # --------------------------------------------------------
    # LONGITUDE
    # --------------------------------------------------------

    lon_distance = (
        (east - west)
        * math.pi
        / 180.0
    )


    # --------------------------------------------------------
    # LATITUDE DISTANCE
    # --------------------------------------------------------

    lat_distance = (
        (north - south)
        * math.pi
        / 180.0
    )


    mean_lat = (
        lat1 + lat2
    ) / 2.0


    # --------------------------------------------------------
    # WIDTH
    # --------------------------------------------------------

    width_km = (
        earth_radius_km
        * lon_distance
        * math.cos(mean_lat)
    )


    # --------------------------------------------------------
    # HEIGHT
    # --------------------------------------------------------

    height_km = (
        earth_radius_km
        * lat_distance
    )


    return abs(
        width_km * height_km
    )


# ============================================================
# MAIN SENTINEL-1 INUNDATION MAP FUNCTION
# ============================================================

def get_sentinel1_inundation_map(
    bbox=None,
    days_back=30,
    min_gap_days=5,
    threshold_db=DEFAULT_CHANGE_THRESHOLD_DB,
):
    """
    Generate a pixel-level Sentinel-1
    potential inundation/change mask.

    IMPORTANT:

    This produces a SAR change candidate mask.

    It is NOT a confirmed flood map.
    """

    # --------------------------------------------------------
    # DEFAULT BBOX
    # --------------------------------------------------------

    if bbox is None:

        bbox = DEFAULT_BBOX


    # --------------------------------------------------------
    # VALIDATE BBOX
    # --------------------------------------------------------

    if len(bbox) != 4:

        raise ValueError(
            "bbox must contain "
            "[west, south, east, north]."
        )


    west, south, east, north = bbox


    if west >= east:

        raise ValueError(
            "bbox west must be smaller than east."
        )


    if south >= north:

        raise ValueError(
            "bbox south must be smaller than north."
        )


    # --------------------------------------------------------
    # VALIDATE DAYS
    # --------------------------------------------------------

    if days_back < 5:

        raise ValueError(
            "days_back must be at least 5."
        )


    if min_gap_days < 1:

        raise ValueError(
            "min_gap_days must be at least 1."
        )


    # --------------------------------------------------------
    # SELECT PRE/POST ACQUISITIONS
    # --------------------------------------------------------

    (
        pre,
        post,
        actual_gap_days,
    ) = _select_acquisition_pair(

        bbox=bbox,

        days_back=days_back,

        min_gap_days=min_gap_days,
    )


    pre_datetime = (
        pre["parsed_datetime"]
    )

    post_datetime = (
        post["parsed_datetime"]
    )


    # --------------------------------------------------------
    # COPERNICUS AUTHENTICATION
    # --------------------------------------------------------

    access_token = (
        get_cdse_access_token()
    )


    # --------------------------------------------------------
    # REQUEST PIXEL-LEVEL MAP
    # --------------------------------------------------------

    image_bytes = (
        _request_inundation_map(

            access_token=access_token,

            bbox=bbox,

            pre_datetime=pre_datetime,

            post_datetime=post_datetime,

            threshold_db=threshold_db,
        )
    )


    # --------------------------------------------------------
    # ANALYZE MASK
    # --------------------------------------------------------

    mask_stats = _analyze_mask(

        image_bytes,

        bbox,
    )


    valid_pixels = (
        mask_stats[
            "valid_pixels"
        ]
    )

    potential_pixels = (
        mask_stats[
            "potential_inundation_pixels"
        ]
    )

    potential_percent = (
        mask_stats[
            "potential_inundation_percent"
        ]
    )


    # --------------------------------------------------------
    # STUDY AREA
    # --------------------------------------------------------

    bbox_area_km2 = (
        _estimate_bbox_area_km2(
            bbox
        )
    )


    # --------------------------------------------------------
    # ESTIMATED CANDIDATE AREA
    # --------------------------------------------------------

    if valid_pixels > 0:

        estimated_area_km2 = (
            bbox_area_km2
            * potential_pixels
            / valid_pixels
        )

    else:

        estimated_area_km2 = 0.0


    # --------------------------------------------------------
    # SANITY CLASSIFICATION
    # --------------------------------------------------------

    if valid_pixels == 0:

        classification = (
            "INSUFFICIENT VALID SAR PIXELS"
        )

        interpretation = (
            "No valid pre/post Sentinel-1 "
            "pixels were available for comparison."
        )

    elif potential_percent >= 95:

        classification = (
            "SUSPICIOUSLY HIGH SAR CHANGE"
        )

        interpretation = (
            "More than 95% of valid pixels were "
            "classified as strong VV decrease. "
            "This should be treated as a SAR-change "
            "anomaly requiring validation rather "
            "than as confirmed inundation."
        )

    elif potential_percent >= 30:

        classification = (
            "HIGH POTENTIAL SAR CHANGE"
        )

        interpretation = (
            "A substantial portion of valid pixels "
            "shows strong VV decrease. The result "
            "may contain inundation candidates, "
            "but independent spatial validation "
            "is required."
        )

    elif potential_percent >= 10:

        classification = (
            "MODERATE POTENTIAL SAR CHANGE"
        )

        interpretation = (
            "A moderate portion of valid pixels "
            "shows strong VV decrease. Further "
            "spatial and event-based validation "
            "is recommended."
        )

    elif potential_percent > 0:

        classification = (
            "LOW POTENTIAL SAR CHANGE"
        )

        interpretation = (
            "Some valid pixels show strong VV "
            "decrease. Continued monitoring and "
            "spatial validation are recommended."
        )

    else:

        classification = (
            "NO STRONG SAR DECREASE"
        )

        interpretation = (
            "No valid pixels exceeded the configured "
            "VV decrease threshold."
        )


    # --------------------------------------------------------
    # BASE64 IMAGE
    # --------------------------------------------------------

    image_base64 = (
        base64.b64encode(
            image_bytes
        ).decode("ascii")
    )


    # --------------------------------------------------------
    # RETURN RESULT
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
                bbox,

            "area_km2":
                round(
                    bbox_area_km2,
                    4,
                ),
        },


        "observation_type": (
            "Sentinel-1 pixel-level "
            "pre/post VV change mask"
        ),


        # ====================================================
        # PRE-EVENT
        # ====================================================

        "pre_event": {

            **_public_acquisition(
                pre
            ),

            "acquisition_datetime":
                pre_datetime.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
        },


        # ====================================================
        # POST-EVENT
        # ====================================================

        "post_event": {

            **_public_acquisition(
                post
            ),

            "acquisition_datetime":
                post_datetime.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
        },


        # ====================================================
        # CHANGE DETECTION
        # ====================================================

        "change_detection": {

            "threshold_db":
                threshold_db,

            "actual_gap_days":
                round(
                    actual_gap_days,
                    2,
                ),

            "classification":
                classification,

            "interpretation":
                interpretation,
        },


        # ====================================================
        # MASK STATISTICS
        # ====================================================

        "mask": {

            "width":
                mask_stats[
                    "width"
                ],

            "height":
                mask_stats[
                    "height"
                ],

            "total_pixels":
                mask_stats[
                    "total_pixels"
                ],

            "valid_pixels":
                valid_pixels,

            "potential_inundation_pixels":
                potential_pixels,

            "potential_inundation_percent":
                round(
                    potential_percent,
                    2,
                ),

            "estimated_candidate_area_km2":
                round(
                    estimated_area_km2,
                    4,
                ),
        },


        # ====================================================
        # IMAGE
        # ====================================================

        "image": {

            "format":
                "image/png",

            "encoding":
                "base64",

            "data":
                image_base64,
        },


        # ====================================================
        # VALIDATION STATUS
        # ====================================================

        "validation_status":
            "PIXEL-LEVEL SAR CHANGE MASK",


        # ====================================================
        # LIMITATIONS
        # ====================================================

        "limitations": [

            (
                "This is a potential inundation "
                "candidate mask, not a confirmed "
                "flood map."
            ),

            (
                "A strong VV decrease can be "
                "caused by factors other than "
                "flooding."
            ),

            (
                "The threshold is configurable "
                "and requires event-based "
                "calibration."
            ),

            (
                "The estimated candidate area "
                "is derived from the selected "
                "bounding box and valid pixels."
            ),

            (
                "The current area estimate "
                "represents candidate pixels "
                "within the study area, not a "
                "validated inundation polygon."
            ),

            (
                "Independent observations are "
                "needed for validation."
            ),

            (
                "Very large candidate percentages "
                "should be treated as potential "
                "SAR-processing or scene-change "
                "anomalies until independently "
                "validated."
            ),
        ],
    }
