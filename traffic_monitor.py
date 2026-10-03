import os
import requests

from dotenv import load_dotenv

from database import (
    create_database,
    insert_traffic_data
)


# =============================================================
# LOAD ENVIRONMENT
# =============================================================

load_dotenv()

API_KEY = os.getenv(
    "TOMTOM_API_KEY"
)


# =============================================================
# TOMTOM TRAFFIC FLOW API
# =============================================================

TOMTOM_URL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/absolute/10/json"
)


# =============================================================
# ANDHRA PRADESH MONITORING LOCATIONS
# =============================================================

LOCATIONS = {

    "Visakhapatnam": {

        "Point 1": {
            "name": "NAD Junction",
            "point": "17.74476,83.23341"
        },

        "Point 2": {
            "name": "Siripuram Junction",
            "point": "17.72366,83.31785"
        },

        "Point 3": {
            "name": "Jagadamba Junction",
            "point": "17.71238,83.30300"
        },

        "Point 4": {
            "name": "RTC Complex",
            "point": "17.72173,83.30762"
        },

        "Point 5": {
            "name": "MVP Colony",
            "point": "17.74070,83.33670"
        }
    },

    "Vizianagaram": {

        "Point 1": {
            "name": "APSRTC Bus Complex",
            "point": "18.10847,83.39918"
        },

        "Point 2": {
            "name": "Phool Bagh",
            "point": "18.12683,83.42309"
        },

        "Point 3": {
            "name": "Vizianagaram Railway Station",
            "point": "18.11154,83.39718"
        }
    },

    "Srikakulam": {

        "Point 1": {
            "name": "Seven Road Junction",
            "point": "18.29476,83.89381"
        },

        "Point 2": {
            "name": "Srikakulam RTC Complex",
            "point": "18.29685,83.89714"
        },

        "Point 3": {
            "name": "Day & Night Junction",
            "point": "18.30250,83.89970"
        }
    },

    "Vijayawada": {

        "Point 1": {
            "name": "Benz Circle",
            "point": "16.48969,80.66763"
        },

        "Point 2": {
            "name": "PNBS",
            "point": "16.51765,80.61968"
        },

        "Point 3": {
            "name": "Ramavarappadu Junction",
            "point": "16.52635,80.67885"
        }
    },

    "Guntur": {

        "Point 1": {
            "name": "NTR Bus Station",
            "point": "16.30665,80.43654"
        },

        "Point 2": {
            "name": "Lakshmipuram",
            "point": "16.30080,80.43670"
        },

        "Point 3": {
            "name": "Arundelpet",
            "point": "16.30040,80.44230"
        }
    },

    "Tirupati": {

        "Point 1": {
            "name": "Tirupati Bus Station",
            "point": "13.62880,79.41920"
        },

        "Point 2": {
            "name": "Alipiri Junction",
            "point": "13.63160,79.40350"
        },

        "Point 3": {
            "name": "Leela Mahal Circle",
            "point": "13.63590,79.41750"
        }
    },

    "Nellore": {

        "Point 1": {
            "name": "Nellore RTC Bus Stand",
            "point": "14.44260,79.98650"
        },

        "Point 2": {
            "name": "Magunta Layout",
            "point": "14.44040,79.99330"
        },

        "Point 3": {
            "name": "Atmakur Bus Stand",
            "point": "14.45150,79.98760"
        }
    },

    "Kakinada": {

        "Point 1": {
            "name": "Kakinada RTC Complex",
            "point": "16.98910,82.24750"
        },

        "Point 2": {
            "name": "Jagannaickpur Junction",
            "point": "16.98650,82.26180"
        },

        "Point 3": {
            "name": "Bhanugudi Junction",
            "point": "16.97480,82.23870"
        }
    },

    "Rajahmundry": {

        "Point 1": {
            "name": "Kotipalli Bus Stand",
            "point": "16.98810,81.77980"
        },

        "Point 2": {
            "name": "Morampudi Junction",
            "point": "17.00540,81.78570"
        },

        "Point 3": {
            "name": "RTC Complex",
            "point": "17.00120,81.77890"
        }
    },

    "Anantapur": {

        "Point 1": {
            "name": "RTC Bus Stand",
            "point": "14.68190,77.60060"
        },

        "Point 2": {
            "name": "Sapthagiri Circle",
            "point": "14.67690,77.59640"
        },

        "Point 3": {
            "name": "Railway Station Road",
            "point": "14.67540,77.59380"
        }
    }
}


# =============================================================
# OLD TRAFFIC LEVEL
# =============================================================

def calculate_traffic_level(
    speed_reduction,
    road_closure
):

    if road_closure:

        return "HIGH"

    if speed_reduction < 20:

        return "LOW"

    elif speed_reduction < 50:

        return "MEDIUM"

    else:

        return "HIGH"


# =============================================================
# STEP 1 - TRAFFIC INTELLIGENCE SCORE
# =============================================================

def calculate_traffic_score(
    speed_reduction,
    current_travel_time,
    free_flow_travel_time,
    road_closure
):
    """
    Calculate a 0-100 Traffic Intelligence Score.

    Components:

    Speed reduction:
        60%

    Travel-time delay:
        40%

    Road closure:
        Critical condition -> 100
    """

    # ---------------------------------------------------------
    # ROAD CLOSURE
    # ---------------------------------------------------------

    if road_closure:

        return 100.0

    # ---------------------------------------------------------
    # SPEED REDUCTION
    # ---------------------------------------------------------

    if speed_reduction is None:

        speed_reduction = 0

    speed_reduction = max(
        0,
        float(speed_reduction)
    )

    # Cap at 100%
    speed_component = min(
        speed_reduction,
        100
    )

    # ---------------------------------------------------------
    # TRAVEL TIME DELAY
    # ---------------------------------------------------------

    delay_percentage = 0

    if (
        free_flow_travel_time
        and free_flow_travel_time > 0
        and current_travel_time is not None
    ):

        delay_percentage = (
            (
                current_travel_time
                - free_flow_travel_time
            )
            / free_flow_travel_time
        ) * 100

    delay_percentage = max(
        0,
        delay_percentage
    )

    delay_component = min(
        delay_percentage,
        100
    )

    # ---------------------------------------------------------
    # WEIGHTED SCORE
    # ---------------------------------------------------------

    score = (
        (speed_component * 0.60)
        +
        (delay_component * 0.40)
    )

    # ---------------------------------------------------------
    # SAFETY LIMIT
    # ---------------------------------------------------------

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return round(
        score,
        2
    )


# =============================================================
# STEP 1 - TRAFFIC STATUS
# =============================================================

def calculate_traffic_status(
    traffic_score
):

    if traffic_score < 25:

        return "NORMAL"

    elif traffic_score < 50:

        return "MODERATE"

    elif traffic_score < 75:

        return "HEAVY"

    else:

        return "CRITICAL"


# =============================================================
# STEP 1 - DELAY IN MINUTES
# =============================================================

def calculate_delay_minutes(
    current_travel_time,
    free_flow_travel_time
):

    if (
        current_travel_time is None
        or free_flow_travel_time is None
    ):

        return 0.0

    delay = (
        current_travel_time
        - free_flow_travel_time
    )

    return round(
        max(0, delay),
        2
    )


# =============================================================
# GET TRAFFIC DATA FROM TOMTOM
# =============================================================

def get_traffic(point):

    if not API_KEY:

        raise Exception(
            "TOMTOM_API_KEY not found in .env file."
        )

    params = {
        "key": API_KEY,
        "point": point
    }

    response = requests.get(
        TOMTOM_URL,
        params=params,
        timeout=15
    )

    if response.status_code != 200:

        raise Exception(
            f"TomTom API Error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    return response.json()


# =============================================================
# PROCESS ONE TRAFFIC POINT
# =============================================================

def process_location(
    city,
    point_id,
    location_info
):

    area_name = location_info["name"]

    point = location_info["point"]

    latitude = float(
        point.split(",")[0]
    )

    longitude = float(
        point.split(",")[1]
    )

    print()
    print("-" * 70)

    print(
        "State        : Andhra Pradesh"
    )

    print(
        f"City         : {city}"
    )

    print(
        f"Traffic Point: {point_id}"
    )

    print(
        f"Location     : {area_name}"
    )

    print(
        f"Coordinates  : {point}"
    )

    print("-" * 70)

    try:

        # -----------------------------------------------------
        # GET TOMTOM DATA
        # -----------------------------------------------------

        data = get_traffic(point)

        flow_data = data.get(
            "flowSegmentData",
            {}
        )

        current_speed = flow_data.get(
            "currentSpeed"
        )

        free_flow_speed = flow_data.get(
            "freeFlowSpeed"
        )

        current_travel_time = flow_data.get(
            "currentTravelTime"
        )

        free_flow_travel_time = flow_data.get(
            "freeFlowTravelTime"
        )

        confidence = flow_data.get(
            "confidence"
        )

        road_closure = flow_data.get(
            "roadClosure",
            False
        )

        # -----------------------------------------------------
        # VALIDATE SPEED DATA
        # -----------------------------------------------------

        if (
            current_speed is None
            or free_flow_speed is None
        ):

            print(
                "Traffic speed data unavailable."
            )

            return False

        # -----------------------------------------------------
        # SPEED REDUCTION
        # -----------------------------------------------------

        if free_flow_speed > 0:

            speed_reduction = (

                (
                    free_flow_speed
                    - current_speed
                )
                /
                free_flow_speed

            ) * 100

        else:

            speed_reduction = 0

        speed_reduction = max(
            0,
            speed_reduction
        )

        # -----------------------------------------------------
        # TRAVEL TIME
        # -----------------------------------------------------

        if current_travel_time is not None:

            current_travel_time_minutes = (
                current_travel_time / 60
            )

        else:

            current_travel_time_minutes = 0

        if free_flow_travel_time is not None:

            free_flow_travel_time_minutes = (
                free_flow_travel_time / 60
            )

        else:

            free_flow_travel_time_minutes = 0

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        if confidence is not None:

            confidence_percentage = (
                confidence * 100
            )

        else:

            confidence_percentage = 0

        # -----------------------------------------------------
        # EXISTING TRAFFIC LEVEL
        # -----------------------------------------------------

        traffic_level = calculate_traffic_level(
            speed_reduction,
            road_closure
        )

        # -----------------------------------------------------
        # STEP 1 - DELAY
        # -----------------------------------------------------

        delay_minutes = calculate_delay_minutes(
            current_travel_time_minutes,
            free_flow_travel_time_minutes
        )

        # -----------------------------------------------------
        # STEP 1 - INTELLIGENCE SCORE
        # -----------------------------------------------------

        traffic_score = calculate_traffic_score(
            speed_reduction,
            current_travel_time_minutes,
            free_flow_travel_time_minutes,
            road_closure
        )

        # -----------------------------------------------------
        # STEP 1 - INTELLIGENCE STATUS
        # -----------------------------------------------------

        traffic_status = calculate_traffic_status(
            traffic_score
        )

        # -----------------------------------------------------
        # DISPLAY
        # -----------------------------------------------------

        print(
            f"Current Speed       : "
            f"{current_speed:.2f} km/h"
        )

        print(
            f"Free Flow Speed     : "
            f"{free_flow_speed:.2f} km/h"
        )

        print(
            f"Speed Reduction     : "
            f"{speed_reduction:.2f}%"
        )

        print(
            f"Current Travel Time : "
            f"{current_travel_time_minutes:.2f} min"
        )

        print(
            f"Free Flow Time      : "
            f"{free_flow_travel_time_minutes:.2f} min"
        )

        print(
            f"Delay               : "
            f"{delay_minutes:.2f} min"
        )

        print(
            f"Confidence          : "
            f"{confidence_percentage:.2f}%"
        )

        print(
            f"Road Closure        : "
            f"{'YES' if road_closure else 'NO'}"
        )

        print(
            f"Traffic Level       : "
            f"{traffic_level}"
        )

        print(
            f"Intelligence Score  : "
            f"{traffic_score:.2f}/100"
        )

        print(
            f"Intelligence Status : "
            f"{traffic_status}"
        )

        # -----------------------------------------------------
        # LOCATION NAME
        # -----------------------------------------------------

        location_name = (
            f"{city} | "
            f"{point_id} — "
            f"{area_name}"
        )

        # -----------------------------------------------------
        # SAVE
        # -----------------------------------------------------

        insert_traffic_data(

            location_name=location_name,

            latitude=latitude,

            longitude=longitude,

            current_speed=current_speed,

            free_flow_speed=free_flow_speed,

            speed_reduction=speed_reduction,

            current_travel_time=(
                current_travel_time_minutes
            ),

            free_flow_travel_time=(
                free_flow_travel_time_minutes
            ),

            confidence=confidence_percentage,

            road_closure=road_closure,

            traffic_level=traffic_level,

            city=city,

            area=area_name,

            point_id=point_id,

            traffic_score=traffic_score,

            traffic_status=traffic_status,

            delay_minutes=delay_minutes
        )

        print(
            "Status              : "
            "SAVED SUCCESSFULLY"
        )

        return True

    except Exception as error:

        print(
            f"Error while collecting "
            f"{city} | "
            f"{point_id} — "
            f"{area_name}"
        )

        print(
            f"Reason              : {error}"
        )

        return False


# =============================================================
# COLLECT ALL TRAFFIC
# =============================================================

def collect_all_traffic():

    print()
    print("=" * 70)

    print(
        "ANDHRA PRADESH TRAFFIC INTELLIGENCE"
    )

    print(
        "REAL-TIME MONITORING SYSTEM"
    )

    print("=" * 70)

    total_cities = len(
        LOCATIONS
    )

    total_points = sum(
        len(points)
        for points in LOCATIONS.values()
    )

    print(
        "Region             : "
        "Andhra Pradesh, India"
    )

    print(
        f"Cities monitored   : "
        f"{total_cities}"
    )

    print(
        f"Traffic points     : "
        f"{total_points}"
    )

    print("=" * 70)

    successful = 0

    failed = 0

    for city, points in LOCATIONS.items():

        print()
        print(
            f">>> {city.upper()}"
        )

        for point_id, location_info in points.items():

            result = process_location(
                city,
                point_id,
                location_info
            )

            if result:

                successful += 1

            else:

                failed += 1

    print()
    print("=" * 70)

    print(
        "COLLECTION SUMMARY"
    )

    print("=" * 70)

    print(
        "State              : "
        "Andhra Pradesh"
    )

    print(
        f"Cities monitored   : "
        f"{total_cities}"
    )

    print(
        f"Traffic points     : "
        f"{total_points}"
    )

    print(
        f"Successful         : "
        f"{successful}"
    )

    print(
        f"Failed             : "
        f"{failed}"
    )

    if total_points > 0:

        success_rate = (
            successful
            / total_points
        ) * 100

        print(
            f"Success rate       : "
            f"{success_rate:.2f}%"
        )

    print("=" * 70)

    print(
        "Traffic data "
        "collection completed."
    )

    print("=" * 70)


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    print()

    print(
        "Initializing database..."
    )

    create_database()

    print(
        "Database initialized successfully."
    )

    collect_all_traffic()