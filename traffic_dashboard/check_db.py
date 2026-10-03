import sqlite3

connection = sqlite3.connect(
    r"D:\Traffic_Density_Project\traffic_data.db"
)

cursor = connection.cursor()

rows = cursor.execute(
    """
    SELECT
        city,
        point_id,
        area,
        COUNT(*) AS records
    FROM traffic_data
    GROUP BY
        city,
        point_id,
        area
    ORDER BY
        city,
        point_id,
        area
    """
).fetchall()

print()
print("=" * 80)
print("DATABASE MONITORING POINTS")
print("=" * 80)

current_city = None

for city, point_id, area, records in rows:

    if city != current_city:
        print()
        print(f">>> {city}")
        current_city = city

    print(
        f"  {point_id} | "
        f"{area} | "
        f"{records} records"
    )

print()
print("=" * 80)
print(f"TOTAL UNIQUE POINTS: {len(rows)}")
print("=" * 80)

connection.close()