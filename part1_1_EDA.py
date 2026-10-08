# Exploratory data analysis for the Porto taxi dataset.

import argparse
import ast
import csv
import json
from collections import Counter
from pathlib import Path

DEFAULT_CSV = Path(__file__).with_name("porto") / "porto.csv"

def get_points(polyline):
    # Convert a POLYLINE value from CSV text to a list of GPS points.
    points = ast.literal_eval(polyline)
    if not isinstance(points, list):
        raise ValueError("POLYLINE is not a list")

    for point in points:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError("invalid GPS point")
        longitude, latitude = point
        if not -180 <= float(longitude) <= 180 or not -90 <= float(latitude) <= 90:
            raise ValueError("invalid GPS coordinates")
    return points

def analyze(csv_path):
    summary = {
        "rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "invalid_trips": 0,
        "duplicate_trip_keys": set(),
        "duplicate_rows": 0,
        "taxis": set(),
        "total_gps_points": 0,
        "missing_data_rows": 0,
        "empty_trajectory_rows": 0,
        "call_types": Counter(),
        "day_types": Counter(),
        "point_counts": Counter(),
    }

    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows_by_trip_id = {}

        for row in reader:
            summary["rows"] += 1
            try:
                trip_id = int(row["TRIP_ID"])
            except (KeyError, TypeError, ValueError):
                trip_id = None

            if trip_id is not None:
                # Count repeated keys, then check whether repeated rows are identical.
                complete_row = tuple(row.values())
                previous_rows = rows_by_trip_id.setdefault(trip_id, set())
                if previous_rows:
                    summary["duplicate_trip_keys"].add(trip_id)
                    if complete_row in previous_rows:
                        summary["duplicate_rows"] += 1
                previous_rows.add(complete_row)

            try:
                points = get_points(row["POLYLINE"])
                if row["CALL_TYPE"] not in {"A", "B", "C"}:
                    raise ValueError("invalid call type")
                if row["DAY_TYPE"] not in {"A", "B", "C"}:
                    raise ValueError("invalid day type")
                taxi_id = int(row["TAXI_ID"])
                missing_data = row["MISSING_DATA"].lower() == "true"
            except (KeyError, TypeError, ValueError, SyntaxError):
                summary["invalid_rows"] += 1
                continue

            summary["valid_rows"] += 1
            summary["taxis"].add(taxi_id)
            summary["total_gps_points"] += len(points)
            summary["missing_data_rows"] += missing_data
            summary["empty_trajectory_rows"] += not points
            summary["invalid_trips"] += len(points) < 3
            summary["call_types"][row["CALL_TYPE"]] += 1
            summary["day_types"][row["DAY_TYPE"]] += 1
            summary["point_counts"][len(points)] += 1

    summary["taxis"] = len(summary["taxis"])
    summary["duplicate_trip_keys"] = len(summary["duplicate_trip_keys"])
    summary["call_types"] = dict(sorted(summary["call_types"].items()))
    summary["day_types"] = dict(sorted(summary["day_types"].items()))
    summary["point_count_min"] = min(summary["point_counts"], default=None)
    summary["point_count_max"] = max(summary["point_counts"], default=None)
    del summary["point_counts"]
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = parser.parse_args()
    if not args.csv.is_file():
        parser.error(f"CSV file does not exist: {args.csv}")
    print(json.dumps(analyze(args.csv), indent=2))

if __name__ == "__main__":
    main()
