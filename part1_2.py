# Create the database tables and load cleaned Porto data.

import argparse
import ast
import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from DbConnector import DbConnector
from tabulate import tabulate # Test

DEFAULT_CSV = Path(__file__).with_name("porto") / "porto_mini.csv"
SCHEMA_FILE = Path(__file__).with_name("schema.sql")
BATCH_SIZE = 2000

TRIP_INSERT = """
INSERT INTO trips (
    trip_id, taxi_id, call_type, origin_call, origin_stand, day_type,
    missing_data, start_time, end_time, duration, point_count, distance,
    start_longitude, start_latitude, end_longitude, end_latitude
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    taxi_id = VALUES(taxi_id), call_type = VALUES(call_type),
    origin_call = VALUES(origin_call), origin_stand = VALUES(origin_stand),
    day_type = VALUES(day_type), missing_data = VALUES(missing_data),
    start_time = VALUES(start_time), end_time = VALUES(end_time),
    duration = VALUES(duration), point_count = VALUES(point_count),
    distance = VALUES(distance), start_longitude = VALUES(start_longitude),
    start_latitude = VALUES(start_latitude), end_longitude = VALUES(end_longitude),
    end_latitude = VALUES(end_latitude)
"""

POINT_INSERT = """
INSERT IGNORE INTO trajectory_points (trip_id, point_index, longitude, latitude)
VALUES (%s, %s, %s, %s)
"""

def get_points(polyline):
    # POLYLINE is stored as text, so turn it into a list of coordinates.
    points = ast.literal_eval(polyline)
    if not isinstance(points, list):
        raise ValueError("POLYLINE is not a list")
    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError("invalid GPS point")
        longitude, latitude = point
        if not -180 <= float(longitude) <= 180 or not -90 <= float(latitude) <= 90:
            raise ValueError("invalid GPS coordinates")
    return [(float(longitude), float(latitude)) for longitude, latitude in points]

def distance_in_km(first, second):
    # Calculate the distance between two longitude, latitude coordinates.
    lon1, lat1 = map(math.radians, first)
    lon2, lat2 = map(math.radians, second)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    value = math.sin(dlat / 2) ** 2
    value += math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(value))

def clean_row(row):
    points = get_points(row["POLYLINE"])
    start_time = datetime.fromtimestamp(
        int(row["TIMESTAMP"]), timezone.utc
    ).replace(tzinfo=None)
    duration = 15 * (len(points) - 1) if points else None
    end_time = start_time + timedelta(seconds=duration) if duration is not None else None
    distance = sum(
        distance_in_km(points[index - 1], points[index])
        for index in range(1, len(points))
    ) if points else None

    return {
        "trip_id": int(row["TRIP_ID"]),
        "taxi_id": int(row["TAXI_ID"]),
        "call_type": row["CALL_TYPE"],
        "origin_call": int(row["ORIGIN_CALL"]) if row["ORIGIN_CALL"] else None,
        "origin_stand": int(row["ORIGIN_STAND"]) if row["ORIGIN_STAND"] else None,
        "day_type": row["DAY_TYPE"],
        "missing_data": row["MISSING_DATA"].lower() == "true",
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "points": points,
        "distance": distance,
    }

def create_tables(cursor, connection):
    # The statements are kept in schema.sql.
    for statement in SCHEMA_FILE.read_text(encoding="utf-8").split(";"):
        if statement.strip():
            cursor.execute(statement)
    connection.commit()

def empty_tables(cursor, connection):
    # Drop tables from child to parent because of the foreign keys.
    cursor.execute("DROP TABLE IF EXISTS trajectory_points")
    cursor.execute("DROP TABLE IF EXISTS trips")
    cursor.execute("DROP TABLE IF EXISTS taxis")
    connection.commit()

def insert_batch(cursor, connection, trips):
    # Batches make the import faster and prevent one huge transaction.
    cursor.executemany(
        "INSERT IGNORE INTO taxis (taxi_id) VALUES (%s)",
        [(trip["taxi_id"],) for trip in trips],
    )

    cursor.executemany(TRIP_INSERT, [
        (
            trip["trip_id"], trip["taxi_id"], trip["call_type"],
            trip["origin_call"], trip["origin_stand"], trip["day_type"],
            trip["missing_data"], trip["start_time"], trip["end_time"],
            trip["duration"], len(trip["points"]), trip["distance"],
            trip["points"][0][0] if trip["points"] else None,
            trip["points"][0][1] if trip["points"] else None,
            trip["points"][-1][0] if trip["points"] else None,
            trip["points"][-1][1] if trip["points"] else None,
        )
        for trip in trips
    ])

    points = [
        (trip["trip_id"], index, longitude, latitude)
        for trip in trips
        for index, (longitude, latitude) in enumerate(trip["points"])
    ]
    if points:
        cursor.executemany(POINT_INSERT, points)
    connection.commit()

# Test
def print_tables(cursor):
    for table in ("taxis", "trips", "trajectory_points"):
        cursor.execute(f"SELECT * FROM {table} LIMIT 5")
        print(f"\n{table}:")
        print(tabulate(cursor.fetchall(), headers=cursor.column_names, tablefmt="grid"))

def load_data(csv_path, reset):
    connection = DbConnector()
    valid_rows = 0
    invalid_rows = 0
    batch = []

    try:
        if reset:
            empty_tables(connection.cursor, connection.db_connection)
        create_tables(connection.cursor, connection.db_connection)

        with csv_path.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                try:
                    trip = clean_row(row)
                except (KeyError, TypeError, ValueError, SyntaxError, OverflowError):
                    invalid_rows += 1
                    continue

                batch.append(trip)
                valid_rows += 1
                if len(batch) == BATCH_SIZE:
                    insert_batch(connection.cursor, connection.db_connection, batch)
                    batch.clear()

        insert_batch(connection.cursor, connection.db_connection, batch)
        print_tables(connection.cursor) # Test
    finally:
        connection.close_connection()

    print(f"Inserted {valid_rows} trips.")
    print(f"Skipped {invalid_rows} invalid rows.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if not args.csv.is_file():
        parser.error(f"CSV file does not exist: {args.csv}")
    load_data(args.csv, args.reset)

if __name__ == "__main__":
    main()
