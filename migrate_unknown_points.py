import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


DB_PATH = Path(r"D:\Traffic_Density_Project\traffic_data.db")


POINT_MAPPING = {
    "Anantapur": {
        "RTC Bus Stand": "Point 1",
        "Sapthagiri Circle": "Point 2",
        "Railway Station Road": "Point 3",
    },
    "Guntur": {
        "NTR Bus Station": "Point 1",
        "Lakshmipuram": "Point 2",
        "Arundelpet": "Point 3",
    },
    "Kakinada": {
        "Kakinada RTC Complex": "Point 1",
        "Jagannaickpur Junction": "Point 2",
        "Bhanugudi Junction": "Point 3",
    },
    "Nellore": {
        "Nellore RTC Bus Stand": "Point 1",
        "Magunta Layout": "Point 2",
        "Atmakur Bus Stand": "Point 3",
    },
    "Rajahmundry": {
        "Kotipalli Bus Stand": "Point 1",
        "Morampudi Junction": "Point 2",
        "RTC Complex": "Point 3",
    },
    "Srikakulam": {
        "Seven Road Junction": "Point 1",
        "Srikakulam RTC Complex": "Point 2",
        "Day & Night Junction": "Point 3",
    },
    "Tirupati": {
        "Tirupati Bus Station": "Point 1",
        "Alipiri Junction": "Point 2",
        "Leela Mahal Circle": "Point 3",
    },
    "Vijayawada": {
        "Benz Circle": "Point 1",
        "PNBS": "Point 2",
        "Ramavarappadu Junction": "Point 3",
    },
    "Visakhapatnam": {
        "NAD Junction": "Point 1",
        "Siripuram Junction": "Point 2",
        "Jagadamba Junction": "Point 3",
        "RTC Complex": "Point 4",
        "MVP Colony": "Point 5",
    },
    "Vizianagaram": {
        "APSRTC Bus Complex": "Point 1",
        "Phool Bagh": "Point 2",
        "Vizianagaram Railway Station": "Point 3",
    },
}


def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = DB_PATH.with_name(
        f"traffic_data_backup_before_migration_{timestamp}.db"
    )

    shutil.copy2(DB_PATH, backup_path)

    print()
    print("=" * 80)
    print("DATABASE BACKUP CREATED")
    print("=" * 80)
    print(f"Original : {DB_PATH}")
    print(f"Backup   : {backup_path}")
    print("=" * 80)

    return backup_path


def migrate_unknown_points():
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        unknown_before = cursor.execute(
            """
            SELECT COUNT(*)
            FROM traffic_data
            WHERE point_id = 'Unknown'
            """
        ).fetchone()[0]

        print()
        print(f"Unknown records before migration: {unknown_before}")

        total_updated = 0

        for city, areas in POINT_MAPPING.items():

            for area, point_id in areas.items():

                cursor.execute(
                    """
                    UPDATE traffic_data
                    SET point_id = ?
                    WHERE city = ?
                      AND area = ?
                      AND point_id = 'Unknown'
                    """,
                    (
                        point_id,
                        city,
                        area,
                    ),
                )

                updated = cursor.rowcount
                total_updated += updated

                if updated > 0:
                    print(
                        f"{city:15} | "
                        f"{point_id:8} | "
                        f"{area:30} | "
                        f"{updated:2} records"
                    )

        connection.commit()

        unknown_after = cursor.execute(
            """
            SELECT COUNT(*)
            FROM traffic_data
            WHERE point_id = 'Unknown'
            """
        ).fetchone()[0]

        total_rows = cursor.execute(
            """
            SELECT COUNT(*)
            FROM traffic_data
            """
        ).fetchone()[0]

        unique_points = cursor.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT city, point_id, area
                FROM traffic_data
            )
            """
        ).fetchone()[0]

        print()
        print("=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"Records updated       : {total_updated}")
        print(f"Unknown before        : {unknown_before}")
        print(f"Unknown after         : {unknown_after}")
        print(f"Total database rows   : {total_rows}")
        print(f"Unique city/point/area: {unique_points}")
        print("=" * 80)

        if unknown_after == 0 and total_updated == unknown_before:
            print()
            print("SUCCESS: All Unknown records were mapped.")
        else:
            print()
            print("WARNING: Some Unknown records remain.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        raise SystemExit(1)

    create_backup()
    migrate_unknown_points()