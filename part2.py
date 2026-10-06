# Run the Part 2 queries and print their results.

import argparse
import re
from pathlib import Path

from tabulate import tabulate

from DbConnector import DbConnector

QUERY_FILE = Path(__file__).with_name("queries.sql")
QUERY_NAMES = [
    "1. Number of taxis, trips, and GPS points",
    "2. Average number of trips per taxi",
    "3. Top 20 taxis by number of trips",
    "4a. Most used call type per taxi",
    "4b. Averages and time-band shares by call type",
    "5. Total hours and distance by taxi",
    "6. Trips within 100 metres of Porto City Hall",
    "7. Number of invalid trips",
    "8. Trips crossing midnight",
    "9. Circular trips",
    "10. Top 20 taxis by average idle time",
]

def read_queries():
    # Read SQL statements.
    text = QUERY_FILE.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = "\n".join(
        line for line in text.splitlines()
        if not line.lstrip().startswith("--")
    )
    return [
        query.strip()
        for query in text.split(";")
        if query.strip()
    ]

def run_queries():
    queries = read_queries()
    if len(queries) != len(QUERY_NAMES):
        raise ValueError(
            f"Expected {len(QUERY_NAMES)} queries, found {len(queries)}"
        )

    connection = DbConnector()
    try:
        for name, query in zip(QUERY_NAMES, queries):
            connection.cursor.execute(query)
            rows = connection.cursor.fetchall()
            print(f"\n{name}")
            print(tabulate(
                rows,
                headers=connection.cursor.column_names,
                tablefmt="grid",
            ))
    finally:
        connection.close_connection()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_queries()


if __name__ == "__main__":
    main()
