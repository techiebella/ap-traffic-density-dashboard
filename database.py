import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATABASE_NAME = str(
    BASE_DIR / "traffic_data.db"
)


def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_data (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            state TEXT DEFAULT 'Andhra Pradesh',

            location_name TEXT NOT NULL,

            city TEXT,
            point_id TEXT,
            area TEXT,

            latitude REAL NOT NULL,
            longitude REAL NOT NULL,

            current_speed REAL,
            free_flow_speed REAL,

            speed_reduction REAL,

            current_travel_time REAL,
            free_flow_travel_time REAL,

            confidence REAL,

            road_closure INTEGER DEFAULT 0,

            traffic_level TEXT,

            traffic_score REAL DEFAULT 0,

            traffic_status TEXT DEFAULT 'NORMAL',

            delay_minutes REAL DEFAULT 0,

            timestamp TEXT
        )
    """)

    connection.commit()

    cursor.execute("""
        PRAGMA table_info(traffic_data)
    """)

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]

    required_columns = {

        "state":
            "TEXT DEFAULT 'Andhra Pradesh'",

        "city":
            "TEXT",

        "point_id":
            "TEXT",

        "area":
            "TEXT",

        "traffic_score":
            "REAL DEFAULT 0",

        "traffic_status":
            "TEXT DEFAULT 'NORMAL'",

        "delay_minutes":
            "REAL DEFAULT 0"
    }

    for column_name, column_definition in required_columns.items():

        if column_name not in columns:

            cursor.execute(
                f"""
                ALTER TABLE traffic_data
                ADD COLUMN {column_name} {column_definition}
                """
            )

    connection.commit()

    cursor.execute("""
        PRAGMA table_info(traffic_data)
    """)

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT
            id,
            location_name,
            city,
            point_id,
            area
        FROM traffic_data
    """)

    records = cursor.fetchall()

    for record in records:

        record_id = record["id"]

        location_name = record["location_name"]

        city = record["city"]

        point_id = record["point_id"]

        area = record["area"]

        new_city = city
        new_point_id = point_id
        new_area = area

        if location_name:

            if " | " in location_name:

                parts = location_name.split(
                    " | ",
                    1
                )

                if not new_city:

                    new_city = parts[0].strip()

                remaining = parts[1].strip()

                if " — " in remaining:

                    point_part, area_part = (
                        remaining.split(
                            " — ",
                            1
                        )
                    )

                    if not new_point_id:

                        new_point_id = (
                            point_part.strip()
                        )

                    if not new_area:

                        new_area = (
                            area_part.strip()
                        )

                elif not new_area:

                    new_area = remaining

            elif " - " in location_name:

                parts = location_name.split(
                    " - ",
                    1
                )

                if not new_city:

                    new_city = parts[0].strip()

                remaining = parts[1].strip()

                if (
                    not new_point_id
                    and remaining.lower().startswith("point")
                ):

                    new_point_id = remaining

                if not new_area:

                    new_area = remaining

            else:

                if not new_area:

                    new_area = location_name.strip()

        new_city = new_city or "Unknown"

        new_point_id = (
            new_point_id or "Unknown"
        )

        new_area = new_area or "Unknown"

        cursor.execute("""
            UPDATE traffic_data

            SET
                state = 'Andhra Pradesh',
                city = ?,
                point_id = ?,
                area = ?

            WHERE id = ?
        """, (
            new_city,
            new_point_id,
            new_area,
            record_id
        ))

    connection.commit()

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_city
        ON traffic_data(city)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_point
        ON traffic_data(city, point_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_point_area
        ON traffic_data(city, point_id, area)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_timestamp
        ON traffic_data(timestamp)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_level
        ON traffic_data(traffic_level)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_status
        ON traffic_data(traffic_status)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_score
        ON traffic_data(traffic_score)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_traffic_location
        ON traffic_data(latitude, longitude)
    """)

    connection.commit()

    connection.close()

    print()
    print("=" * 60)
    print("DATABASE CREATED / UPGRADED SUCCESSFULLY")
    print("=" * 60)
    print(f"Database path   : {DATABASE_NAME}")
    print("State structure : Andhra Pradesh")
    print("Database table  : traffic_data")
    print("Intelligence    : ENABLED")
    print("Traffic score   : ENABLED")
    print("Traffic status  : ENABLED")
    print("Delay minutes   : ENABLED")
    print("Indexes         : ENABLED")
    print("=" * 60)


# =============================================================
# INSERT TRAFFIC DATA
# =============================================================

def insert_traffic_data(
    location_name,
    latitude,
    longitude,
    current_speed,
    free_flow_speed,
    speed_reduction,
    current_travel_time,
    free_flow_travel_time,
    confidence,
    road_closure,
    traffic_level,
    city=None,
    area=None,
    point_id=None,
    state="Andhra Pradesh",
    traffic_score=0,
    traffic_status="NORMAL",
    delay_minutes=0
):

    connection = get_connection()

    cursor = connection.cursor()

    if city is None:

        city = "Unknown"

    if point_id is None:

        point_id = "Unknown"

    if area is None:

        area = "Unknown"

    if location_name:

        if (
            city == "Unknown"
            and " | " in location_name
        ):

            city_part, remaining = (
                location_name.split(
                    " | ",
                    1
                )
            )

            city = city_part.strip()

            if " — " in remaining:

                point_part, area_part = (
                    remaining.split(
                        " — ",
                        1
                    )
                )

                if point_id == "Unknown":

                    point_id = point_part.strip()

                if area == "Unknown":

                    area = area_part.strip()

        elif (
            city == "Unknown"
            and " - " in location_name
        ):

            city_part, remaining = (
                location_name.split(
                    " - ",
                    1
                )
            )

            city = city_part.strip()

            if (
                point_id == "Unknown"
                and remaining.lower().startswith("point")
            ):

                point_id = remaining.strip()

            if area == "Unknown":

                area = remaining.strip()

    if traffic_score is None:

        traffic_score = 0

    traffic_score = max(
        0,
        min(
            100,
            float(traffic_score)
        )
    )

    if delay_minutes is None:

        delay_minutes = 0

    delay_minutes = max(
        0,
        float(delay_minutes)
    )

    if traffic_status is None:

        traffic_status = "NORMAL"

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO traffic_data (

            state,

            location_name,

            city,
            point_id,
            area,

            latitude,
            longitude,

            current_speed,
            free_flow_speed,

            speed_reduction,

            current_travel_time,
            free_flow_travel_time,

            confidence,

            road_closure,

            traffic_level,

            traffic_score,

            traffic_status,

            delay_minutes,

            timestamp

        )

        VALUES (

            ?, ?, ?, ?, ?,
            ?, ?,
            ?, ?,
            ?,
            ?, ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?

        )
    """, (

        state,

        location_name,

        city,
        point_id,
        area,

        latitude,
        longitude,

        current_speed,
        free_flow_speed,

        speed_reduction,

        current_travel_time,
        free_flow_travel_time,

        confidence,

        int(bool(road_closure)),

        traffic_level,

        traffic_score,

        traffic_status,

        delay_minutes,

        timestamp
    ))

    connection.commit()

    connection.close()

    print(
        f"Data saved: "
        f"{state} | "
        f"{city} | "
        f"{point_id} | "
        f"{area} | "
        f"Score: {traffic_score:.1f} | "
        f"Status: {traffic_status}"
    )


# =============================================================
# GET LATEST TRAFFIC
# =============================================================

def get_latest_traffic():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM traffic_data
        ORDER BY timestamp DESC, id DESC
    """)

    records = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return records


# =============================================================
# GET CITY TRAFFIC
# =============================================================

def get_city_traffic(city):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM traffic_data
        WHERE city = ?
        ORDER BY timestamp DESC, id DESC
    """, (city,))

    records = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return records


# =============================================================
# GET AVAILABLE CITIES
# =============================================================

def get_available_cities():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT city
        FROM traffic_data

        WHERE city IS NOT NULL
        AND city != 'Unknown'

        ORDER BY city
    """)

    cities = [
        row["city"]
        for row in cursor.fetchall()
    ]

    connection.close()

    return cities


# =============================================================
# GET TRAFFIC SUMMARY
# =============================================================

def get_traffic_summary():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            COUNT(*) AS total_records,

            COUNT(DISTINCT city)
                AS total_cities,

            COUNT(
                DISTINCT city || '|' ||
                point_id || '|' ||
                area
            )
                AS total_points,

            AVG(current_speed)
                AS average_speed,

            AVG(speed_reduction)
                AS average_speed_reduction,

            AVG(traffic_score)
                AS average_traffic_score,

            AVG(delay_minutes)
                AS average_delay_minutes

        FROM traffic_data

        WHERE state = 'Andhra Pradesh'
    """)

    result = dict(
        cursor.fetchone()
    )

    connection.close()

    return result


# =============================================================
# GET TRAFFIC HOTSPOTS
# =============================================================

def get_traffic_hotspots(limit=5):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
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

            WHERE state = 'Andhra Pradesh'

        )

        WHERE row_number = 1

        ORDER BY
            traffic_score DESC,
            speed_reduction DESC,
            delay_minutes DESC

        LIMIT ?
    """, (
        int(limit),
    ))

    hotspots = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return hotspots


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    create_database()