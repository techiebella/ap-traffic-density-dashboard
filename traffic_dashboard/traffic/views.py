import os
import sqlite3
import subprocess
import sys

from django.http import JsonResponse
from django.shortcuts import render


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"D:\Traffic_Density_Project"

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "traffic_data.db"
)

MONITOR_SCRIPT = os.path.join(
    BASE_DIR,
    "traffic_monitor.py"
)


# ============================================================
# DATABASE
# ============================================================

def get_database_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def row_to_dict(row):

    return dict(row)


# ============================================================
# LATEST TRAFFIC RECORDS
# ============================================================

def get_latest_records(
    city=None,
    area=None,
    point_id=None
):

    connection = get_database_connection()

    cursor = connection.cursor()

    conditions = []

    parameters = []

    conditions.append(
        "state = ?"
    )

    parameters.append(
        "Andhra Pradesh"
    )

    if city:

        conditions.append(
            "city = ?"
        )

        parameters.append(
            city
        )

    if area:

        conditions.append(
            "area = ?"
        )

        parameters.append(
            area
        )

    if point_id:

        conditions.append(
            "point_id = ?"
        )

        parameters.append(
            point_id
        )

    where_clause = " AND ".join(
        conditions
    )

    query = f"""
        SELECT *
        FROM (
            SELECT
                traffic_data.*,

                ROW_NUMBER() OVER (
                    PARTITION BY
                        city,
                        point_id,
                        area

                    ORDER BY
                        timestamp DESC,
                        id DESC
                ) AS row_number

            FROM traffic_data

            WHERE {where_clause}
        )

        WHERE row_number = 1

        ORDER BY
            city,
            point_id,
            area
    """

    cursor.execute(
        query,
        parameters
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row_to_dict(row)
        for row in rows
    ]


# ============================================================
# TRAFFIC HISTORY
# ============================================================

def get_history(
    city=None,
    area=None,
    point_id=None,
    limit=100
):

    connection = get_database_connection()

    cursor = connection.cursor()

    conditions = [
        "state = ?"
    ]

    parameters = [
        "Andhra Pradesh"
    ]

    if city:

        conditions.append(
            "city = ?"
        )

        parameters.append(
            city
        )

    if area:

        conditions.append(
            "area = ?"
        )

        parameters.append(
            area
        )

    if point_id:

        conditions.append(
            "point_id = ?"
        )

        parameters.append(
            point_id
        )

    where_clause = " AND ".join(
        conditions
    )

    query = f"""
        SELECT *
        FROM traffic_data

        WHERE {where_clause}

        ORDER BY
            timestamp DESC,
            id DESC

        LIMIT ?
    """

    parameters.append(
        int(limit)
    )

    cursor.execute(
        query,
        parameters
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row_to_dict(row)
        for row in rows
    ]


# ============================================================
# CITIES
# ============================================================

def get_cities():

    connection = get_database_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT city

        FROM traffic_data

        WHERE state = 'Andhra Pradesh'

          AND city IS NOT NULL

          AND city != 'Unknown'

        ORDER BY city
    """)

    cities = [
        row["city"]
        for row in cursor.fetchall()
    ]

    connection.close()

    return cities


# ============================================================
# AREAS
# ============================================================

def get_areas(city=None):

    connection = get_database_connection()

    cursor = connection.cursor()

    if city:

        cursor.execute("""
            SELECT DISTINCT area

            FROM traffic_data

            WHERE state = 'Andhra Pradesh'

              AND city = ?

              AND area IS NOT NULL

              AND area != 'Unknown'

            ORDER BY area
        """, (city,))

    else:

        cursor.execute("""
            SELECT DISTINCT area

            FROM traffic_data

            WHERE state = 'Andhra Pradesh'

              AND area IS NOT NULL

              AND area != 'Unknown'

            ORDER BY area
        """)

    areas = [
        row["area"]
        for row in cursor.fetchall()
    ]

    connection.close()

    return areas


# ============================================================
# MONITORING POINTS
# ============================================================

def get_points(city=None):

    connection = get_database_connection()

    cursor = connection.cursor()

    if city:

        cursor.execute("""
            SELECT DISTINCT
                point_id,
                area

            FROM traffic_data

            WHERE state = 'Andhra Pradesh'

              AND city = ?

              AND point_id IS NOT NULL

              AND point_id != 'Unknown'

            ORDER BY point_id
        """, (city,))

    else:

        cursor.execute("""
            SELECT DISTINCT
                city,
                point_id,
                area

            FROM traffic_data

            WHERE state = 'Andhra Pradesh'

              AND point_id IS NOT NULL

              AND point_id != 'Unknown'

            ORDER BY
                city,
                point_id
        """)

    points = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return points


# ============================================================
# SUMMARY
# ============================================================

def calculate_summary(records):

    low_count = 0

    medium_count = 0

    high_count = 0

    road_closures = 0

    total_speed = 0

    speed_count = 0

    total_reduction = 0

    reduction_count = 0

    total_confidence = 0

    confidence_count = 0

    total_score = 0

    score_count = 0

    total_delay = 0

    delay_count = 0

    for record in records:

        level = str(
            record.get(
                "traffic_level"
            ) or ""
        ).upper()

        if level == "LOW":

            low_count += 1

        elif level == "MEDIUM":

            medium_count += 1

        elif level == "HIGH":

            high_count += 1

        if record.get(
            "road_closure"
        ):

            road_closures += 1

        if record.get(
            "current_speed"
        ) is not None:

            total_speed += float(
                record["current_speed"]
            )

            speed_count += 1

        if record.get(
            "speed_reduction"
        ) is not None:

            total_reduction += float(
                record["speed_reduction"]
            )

            reduction_count += 1

        if record.get(
            "confidence"
        ) is not None:

            total_confidence += float(
                record["confidence"]
            )

            confidence_count += 1

        if record.get(
            "traffic_score"
        ) is not None:

            total_score += float(
                record["traffic_score"]
            )

            score_count += 1

        if record.get(
            "delay_minutes"
        ) is not None:

            total_delay += float(
                record["delay_minutes"]
            )

            delay_count += 1

    average_speed = (

        total_speed / speed_count

        if speed_count

        else 0
    )

    average_reduction = (

        total_reduction / reduction_count

        if reduction_count

        else 0
    )

    average_confidence = (

        total_confidence / confidence_count

        if confidence_count

        else 0
    )

    average_score = (

        total_score / score_count

        if score_count

        else 0
    )

    average_delay = (

        total_delay / delay_count

        if delay_count

        else 0
    )

    return {

        "monitored_locations":
            len(records),

        "low":
            low_count,

        "medium":
            medium_count,

        "high":
            high_count,

        "road_closures":
            road_closures,

        "average_speed":
            round(
                average_speed,
                2
            ),

        "average_reduction":
            round(
                average_reduction,
                2
            ),

        "average_confidence":
            round(
                average_confidence,
                2
            ),

        "average_score":
            round(
                average_score,
                2
            ),

        "average_delay":
            round(
                average_delay,
                2
            )
    }


# ============================================================
# LATEST TIMESTAMP
# ============================================================

def get_latest_timestamp(records):

    timestamps = [

        record.get(
            "timestamp"
        )

        for record in records

        if record.get(
            "timestamp"
        )
    ]

    if not timestamps:

        return None

    return max(
        timestamps
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard(request):

    latest_records = (
        get_latest_records()
    )

    history = get_history(
        limit=100
    )

    cities = get_cities()

    areas = get_areas()

    points = get_points()

    summary = calculate_summary(
        latest_records
    )

    latest_timestamp = (
        get_latest_timestamp(
            latest_records
        )
    )

    context = {

        "state":
            "Andhra Pradesh",

        "latest_records":
            latest_records,

        "history":
            history,

        "cities":
            cities,

        "areas":
            areas,

        "points":
            points,

        "summary":
            summary,

        "latest_timestamp":
            latest_timestamp
    }

    return render(
        request,
        "traffic/dashboard.html",
        context
    )


# ============================================================
# RUN TRAFFIC MONITOR
# ============================================================

def run_traffic_monitor():

    try:

        if not os.path.exists(
            MONITOR_SCRIPT
        ):

            return {

                "success":
                    False,

                "message":
                    (
                        "traffic_monitor.py "
                        "not found."
                    )
            }

        result = subprocess.run(

            [
                sys.executable,
                MONITOR_SCRIPT
            ],

            cwd=BASE_DIR,

            capture_output=True,

            text=True,

            timeout=180
        )

        if result.returncode == 0:

            return {

                "success":
                    True,

                "message":
                    (
                        "Andhra Pradesh "
                        "traffic data updated "
                        "successfully."
                    ),

                "output":
                    result.stdout
            }

        return {

            "success":
                False,

            "message":
                (
                    "Traffic monitor "
                    "failed."
                ),

            "output":
                result.stderr
        }

    except subprocess.TimeoutExpired:

        return {

            "success":
                False,

            "message":
                (
                    "Traffic monitoring "
                    "timed out."
                )
        }

    except Exception as error:

        return {

            "success":
                False,

            "message":
                str(error)
        }


# ============================================================
# REFRESH TRAFFIC
# ============================================================

def refresh_traffic(request):

    if request.method != "GET":

        return JsonResponse(

            {
                "success":
                    False,

                "message":
                    (
                        "Only GET requests "
                        "are allowed."
                    )
            },

            status=405
        )

    result = run_traffic_monitor()

    if result["success"]:

        latest_records = (
            get_latest_records()
        )

        return JsonResponse(

            {
                "success":
                    True,

                "message":
                    result["message"],

                "state":
                    "Andhra Pradesh",

                "cities_monitored":
                    len(
                        get_cities()
                    ),

                "traffic_points":
                    len(
                        latest_records
                    ),

                "updated_locations":
                    len(
                        latest_records
                    ),

                "timestamp":
                    get_latest_timestamp(
                        latest_records
                    ),

                "output":
                    result.get(
                        "output",
                        ""
                    )
            }
        )

    return JsonResponse(

        {
            "success":
                False,

            "message":
                result["message"],

            "output":
                result.get(
                    "output",
                    ""
                )
        },

        status=500
    )


# ============================================================
# LATEST TRAFFIC API
# ============================================================

def latest_traffic(request):

    city = request.GET.get(
        "city"
    )

    area = request.GET.get(
        "area"
    )

    point_id = request.GET.get(
        "point_id"
    )

    if city == "all":

        city = None

    if area == "all":

        area = None

    if point_id == "all":

        point_id = None

    latest_records = (
        get_latest_records(

            city=city,

            area=area,

            point_id=point_id
        )
    )

    history = get_history(

        city=city,

        area=area,

        point_id=point_id,

        limit=100
    )

    cities = get_cities()

    areas = get_areas(
        city
    )

    points = get_points(
        city
    )

    summary = calculate_summary(
        latest_records
    )

    latest_timestamp = (
        get_latest_timestamp(
            latest_records
        )
    )

    return JsonResponse(

        {

            "success":
                True,

            "state":
                "Andhra Pradesh",

            "filters": {

                "city":
                    city,

                "area":
                    area,

                "point_id":
                    point_id
            },

            "latest":
                latest_records,

            "history":
                history,

            "cities":
                cities,

            "areas":
                areas,

            "points":
                points,

            "timestamp":
                latest_timestamp,

            "summary":
                summary
        }
    )


# ============================================================
# ANALYTICS API
# ============================================================

def traffic_analytics(request):

    city = request.GET.get(
        "city"
    )

    area = request.GET.get(
        "area"
    )

    point_id = request.GET.get(
        "point_id"
    )

    if city == "all":

        city = None

    if area == "all":

        area = None

    if point_id == "all":

        point_id = None

    latest_records = (
        get_latest_records(

            city=city,

            area=area,

            point_id=point_id
        )
    )

    history = get_history(

        city=city,

        area=area,

        point_id=point_id,

        limit=200
    )

    summary = calculate_summary(
        latest_records
    )

    # --------------------------------------------------------
    # Traffic Distribution
    # --------------------------------------------------------

    distribution = {

        "LOW":
            0,

        "MEDIUM":
            0,

        "HIGH":
            0
    }

    for record in latest_records:

        level = str(

            record.get(
                "traffic_level"
            ) or ""

        ).upper()

        if level in distribution:

            distribution[level] += 1

    # --------------------------------------------------------
    # Highest Speed Reduction
    # --------------------------------------------------------

    highest_reduction_location = None

    highest_reduction_value = 0

    for record in latest_records:

        reduction = record.get(
            "speed_reduction"
        )

        if reduction is None:

            continue

        reduction = float(
            reduction
        )

        if reduction > highest_reduction_value:

            highest_reduction_value = (
                reduction
            )

            highest_reduction_location = (

                f"{record.get('city', 'Unknown')} | "

                f"{record.get('point_id', 'Unknown')} | "

                f"{record.get('area', 'Unknown')}"
            )

    # --------------------------------------------------------
    # City Analytics
    # --------------------------------------------------------

    city_data = {}

    for record in latest_records:

        city_name = (

            record.get(
                "city"
            )

            or "Unknown"
        )

        if city_name not in city_data:

            city_data[city_name] = {

                "locations":
                    0,

                "speed_total":
                    0,

                "speed_count":
                    0,

                "reduction_total":
                    0,

                "reduction_count":
                    0,

                "confidence_total":
                    0,

                "confidence_count":
                    0,

                "high":
                    0,

                "medium":
                    0,

                "low":
                    0,

                "closures":
                    0
            }

        item = city_data[
            city_name
        ]

        item["locations"] += 1

        if record.get(
            "current_speed"
        ) is not None:

            item["speed_total"] += float(

                record[
                    "current_speed"
                ]
            )

            item["speed_count"] += 1

        if record.get(
            "speed_reduction"
        ) is not None:

            item["reduction_total"] += float(

                record[
                    "speed_reduction"
                ]
            )

            item["reduction_count"] += 1

        if record.get(
            "confidence"
        ) is not None:

            item["confidence_total"] += float(

                record[
                    "confidence"
                ]
            )

            item["confidence_count"] += 1

        level = str(

            record.get(
                "traffic_level"
            ) or ""

        ).upper()

        if level == "HIGH":

            item["high"] += 1

        elif level == "MEDIUM":

            item["medium"] += 1

        elif level == "LOW":

            item["low"] += 1

        if record.get(
            "road_closure"
        ):

            item["closures"] += 1

    city_result = []

    for city_name, item in city_data.items():

        city_result.append(

            {

                "city":
                    city_name,

                "locations":
                    item[
                        "locations"
                    ],

                "average_speed":
                    round(

                        item[
                            "speed_total"
                        ]
                        /
                        item[
                            "speed_count"
                        ],

                        2

                    )
                    if item[
                        "speed_count"
                    ]

                    else 0,

                "average_reduction":
                    round(

                        item[
                            "reduction_total"
                        ]
                        /
                        item[
                            "reduction_count"
                        ],

                        2

                    )
                    if item[
                        "reduction_count"
                    ]

                    else 0,

                "average_confidence":
                    round(

                        item[
                            "confidence_total"
                        ]
                        /
                        item[
                            "confidence_count"
                        ],

                        2

                    )
                    if item[
                        "confidence_count"
                    ]

                    else 0,

                "high":
                    item["high"],

                "medium":
                    item["medium"],

                "low":
                    item["low"],

                "road_closures":
                    item["closures"]
            }
        )

    city_result.sort(
        key=lambda item:
            item["city"]
    )

    # --------------------------------------------------------
    # Area Analytics
    # --------------------------------------------------------

    area_result = []

    for record in latest_records:

        area_result.append(

            {

                "state":
                    record.get(
                        "state"
                    ),

                "city":
                    record.get(
                        "city"
                    ),

                "point_id":
                    record.get(
                        "point_id"
                    ),

                "area":
                    record.get(
                        "area"
                    ),

                "latitude":
                    record.get(
                        "latitude"
                    ),

                "longitude":
                    record.get(
                        "longitude"
                    ),

                "current_speed":
                    record.get(
                        "current_speed"
                    ),

                "free_flow_speed":
                    record.get(
                        "free_flow_speed"
                    ),

                "speed_reduction":
                    record.get(
                        "speed_reduction"
                    ),

                "current_travel_time":
                    record.get(
                        "current_travel_time"
                    ),

                "free_flow_travel_time":
                    record.get(
                        "free_flow_travel_time"
                    ),

                "confidence":
                    record.get(
                        "confidence"
                    ),

                "traffic_level":
                    record.get(
                        "traffic_level"
                    ),

                "traffic_score":
                    record.get(
                        "traffic_score"
                    ),

                "traffic_status":
                    record.get(
                        "traffic_status"
                    ),

                "delay_minutes":
                    record.get(
                        "delay_minutes"
                    ),

                "road_closure":
                    bool(
                        record.get(
                            "road_closure"
                        )
                    ),

                "timestamp":
                    record.get(
                        "timestamp"
                    )
            }
        )

    # --------------------------------------------------------
    # Trend Data
    # --------------------------------------------------------

    trend = []

    for record in reversed(
        history
    ):

        trend.append(

            {

                "timestamp":
                    record.get(
                        "timestamp"
                    ),

                "city":
                    record.get(
                        "city"
                    ),

                "point_id":
                    record.get(
                        "point_id"
                    ),

                "area":
                    record.get(
                        "area"
                    ),

                "current_speed":
                    record.get(
                        "current_speed"
                    ),

                "free_flow_speed":
                    record.get(
                        "free_flow_speed"
                    ),

                "speed_reduction":
                    record.get(
                        "speed_reduction"
                    ),

                "traffic_level":
                    record.get(
                        "traffic_level"
                    ),

                "traffic_score":
                    record.get(
                        "traffic_score"
                    ),

                "traffic_status":
                    record.get(
                        "traffic_status"
                    ),

                "delay_minutes":
                    record.get(
                        "delay_minutes"
                    )
            }
        )

    return JsonResponse(

        {

            "success":
                True,

            "state":
                "Andhra Pradesh",

            "filters": {

                "city":
                    city,

                "area":
                    area,

                "point_id":
                    point_id
            },

            "overview": {

                "monitored_locations":
                    summary[
                        "monitored_locations"
                    ],

                "average_speed":
                    summary[
                        "average_speed"
                    ],

                "average_reduction":
                    summary[
                        "average_reduction"
                    ],

                "average_confidence":
                    summary[
                        "average_confidence"
                    ],

                "average_score":
                    summary[
                        "average_score"
                    ],

                "average_delay":
                    summary[
                        "average_delay"
                    ],

                "highest_reduction":
                    round(
                        highest_reduction_value,
                        2
                    ),

                "highest_reduction_location":
                    highest_reduction_location
            },

            "traffic_distribution":
                distribution,

            "city_analytics":
                city_result,

            "area_analytics":
                area_result,

            "trend":
                trend
        }
    )


# ============================================================
# AUTOMATIC TRAFFIC HOTSPOTS
# ============================================================

def get_traffic_hotspots(
    limit=5
):

    connection = (
        get_database_connection()
    )

    cursor = connection.cursor()

    query = """

        SELECT *

        FROM (

            SELECT

                traffic_data.*,

                ROW_NUMBER() OVER (

                    PARTITION BY
                        city,
                        point_id,
                        area

                    ORDER BY
                        timestamp DESC,
                        id DESC

                ) AS row_number

            FROM traffic_data

            WHERE state = ?

        )

        WHERE row_number = 1

        ORDER BY

            traffic_score DESC,

            speed_reduction DESC

        LIMIT ?

    """

    cursor.execute(

        query,

        (
            "Andhra Pradesh",
            int(limit)
        )
    )

    rows = cursor.fetchall()

    connection.close()

    hotspots = []

    for row in rows:

        record = row_to_dict(
            row
        )

        hotspots.append(

            {

                "state":
                    record.get(
                        "state"
                    ),

                "city":
                    record.get(
                        "city"
                    ),

                "point_id":
                    record.get(
                        "point_id"
                    ),

                "area":
                    record.get(
                        "area"
                    ),

                "latitude":
                    record.get(
                        "latitude"
                    ),

                "longitude":
                    record.get(
                        "longitude"
                    ),

                "traffic_score":
                    round(

                        float(
                            record.get(
                                "traffic_score"
                            ) or 0
                        ),

                        2
                    ),

                "traffic_status":
                    (
                        record.get(
                            "traffic_status"
                        )

                        or "NORMAL"
                    ),

                "delay_minutes":
                    round(

                        float(
                            record.get(
                                "delay_minutes"
                            ) or 0
                        ),

                        2
                    ),

                "current_speed":
                    record.get(
                        "current_speed"
                    ),

                "free_flow_speed":
                    record.get(
                        "free_flow_speed"
                    ),

                "speed_reduction":
                    record.get(
                        "speed_reduction"
                    ),

                "road_closure":
                    bool(
                        record.get(
                            "road_closure"
                        )
                    ),

                "timestamp":
                    record.get(
                        "timestamp"
                    )
            }
        )

    return hotspots


def traffic_hotspots(request):

    try:

        limit = int(

            request.GET.get(
                "limit",
                5
            )
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 5

    limit = max(
        1,
        min(
            limit,
            20
        )
    )

    hotspots = (
        get_traffic_hotspots(
            limit=limit
        )
    )

    return JsonResponse(

        {

            "success":
                True,

            "state":
                "Andhra Pradesh",

            "count":
                len(hotspots),

            "hotspots":
                hotspots
        }
    )


# ============================================================
# INCIDENT INTELLIGENCE
# ============================================================

def get_traffic_incidents():

    """
    Automatically detects active traffic incidents
    using only the latest reading from each
    monitoring point in Andhra Pradesh.
    """

    connection = (
        get_database_connection()
    )

    cursor = connection.cursor()

    query = """

        SELECT *

        FROM (

            SELECT

                traffic_data.*,

                ROW_NUMBER() OVER (

                    PARTITION BY
                        city,
                        point_id,
                        area

                    ORDER BY
                        timestamp DESC,
                        id DESC

                ) AS row_number

            FROM traffic_data

            WHERE state = ?

        )

        WHERE row_number = 1

    """

    cursor.execute(

        query,

        (
            "Andhra Pradesh",
        )
    )

    rows = cursor.fetchall()

    connection.close()

    incidents = []

    for row in rows:

        record = row_to_dict(
            row
        )

        city = (

            record.get(
                "city"
            )

            or "Unknown City"
        )

        area = (

            record.get(
                "area"
            )

            or record.get(
                "point_id"
            )

            or "Unknown Location"
        )

        point_id = (

            record.get(
                "point_id"
            )

            or "Unknown Point"
        )

        score = float(

            record.get(
                "traffic_score"
            ) or 0
        )

        delay = float(

            record.get(
                "delay_minutes"
            ) or 0
        )

        speed_reduction = float(

            record.get(
                "speed_reduction"
            ) or 0
        )

        traffic_status = (

            record.get(
                "traffic_status"
            )

            or "NORMAL"
        ).upper()

        road_closure = bool(

            record.get(
                "road_closure"
            )
        )

        detected_incidents = []

        # ----------------------------------------------------
        # ROAD CLOSURE
        # ----------------------------------------------------

        if road_closure:

            detected_incidents.append(

                {

                    "incident_type":
                        "ROAD CLOSURE",

                    "severity":
                        "CRITICAL",

                    "message":
                        (
                            f"Road closure "
                            f"detected at {area}"
                        )
                }
            )

        # ----------------------------------------------------
        # CRITICAL TRAFFIC
        # ----------------------------------------------------

        elif score >= 75:

            detected_incidents.append(

                {

                    "incident_type":
                        "CRITICAL TRAFFIC",

                    "severity":
                        "CRITICAL",

                    "message":
                        (
                            f"Critical traffic "
                            f"detected at {area}"
                        )
                }
            )

        # ----------------------------------------------------
        # HEAVY TRAFFIC
        # ----------------------------------------------------

        elif score >= 50:

            detected_incidents.append(

                {

                    "incident_type":
                        "HEAVY TRAFFIC",

                    "severity":
                        "HIGH",

                    "message":
                        (
                            f"Heavy traffic "
                            f"detected at {area}"
                        )
                }
            )

        # ----------------------------------------------------
        # SEVERE SPEED REDUCTION
        # ----------------------------------------------------

        if speed_reduction >= 50:

            detected_incidents.append(

                {

                    "incident_type":
                        "SEVERE SPEED REDUCTION",

                    "severity":
                        "HIGH",

                    "message":
                        (
                            f"Speed reduced by "
                            f"{speed_reduction:.1f}% "
                            f"at {area}"
                        )
                }
            )

        # ----------------------------------------------------
        # HIGH DELAY
        # ----------------------------------------------------

        if delay >= 10:

            detected_incidents.append(

                {

                    "incident_type":
                        "HIGH DELAY",

                    "severity":
                        "HIGH",

                    "message":
                        (
                            f"Traffic delay of "
                            f"{delay:.1f} minutes "
                            f"detected at {area}"
                        )
                }
            )

        # ----------------------------------------------------
        # COMMON INCIDENT INFORMATION
        # ----------------------------------------------------

        for incident in detected_incidents:

            incident["state"] = (

                record.get(
                    "state"
                )

                or "Andhra Pradesh"
            )

            incident["city"] = city

            incident["point_id"] = point_id

            incident["area"] = area

            incident["latitude"] = (
                record.get(
                    "latitude"
                )
            )

            incident["longitude"] = (
                record.get(
                    "longitude"
                )
            )

            incident["traffic_score"] = round(
                score,
                2
            )

            incident["traffic_status"] = (
                traffic_status
            )

            incident["delay_minutes"] = round(
                delay,
                2
            )

            incident["current_speed"] = (
                record.get(
                    "current_speed"
                )
            )

            incident["free_flow_speed"] = (
                record.get(
                    "free_flow_speed"
                )
            )

            incident["speed_reduction"] = round(
                speed_reduction,
                2
            )

            incident["road_closure"] = (
                road_closure
            )

            incident["timestamp"] = (
                record.get(
                    "timestamp"
                )
            )

            incidents.append(
                incident
            )

    # --------------------------------------------------------
    # INCIDENT SEVERITY ORDER
    # --------------------------------------------------------

    severity_order = {

        "CRITICAL":
            1,

        "HIGH":
            2,

        "MEDIUM":
            3,

        "LOW":
            4
    }

    incidents.sort(

        key=lambda item: (

            severity_order.get(

                item.get(
                    "severity"
                ),

                99
            ),

            -float(

                item.get(
                    "traffic_score"
                ) or 0
            ),

            -float(

                item.get(
                    "delay_minutes"
                ) or 0
            )
        )
    )

    return incidents


# ============================================================
# INCIDENT API
# ============================================================

def traffic_incidents(request):

    incidents = (
        get_traffic_incidents()
    )

    return JsonResponse(

        {

            "success":
                True,

            "state":
                "Andhra Pradesh",

            "count":
                len(incidents),

            "incidents":
                incidents
        }
    )