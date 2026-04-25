import argparse
import csv
from datetime import datetime, time
from pathlib import Path
from typing import Iterator

from sqlalchemy import insert

from db import engine
from models import Base, WeatherRaw, WindDirection


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")


def parse_clock(value: str) -> time | None:
    normalized = value.strip()
    if (
        not normalized
        or normalized.lower().startswith("no ")
        or normalized in {"****", "...."}
    ):
        return None
    if normalized == "24:00":
        return time(0, 0)
    for time_format in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(normalized, time_format).time()
        except ValueError:
            continue
    raise ValueError(f"Unsupported time value: {value!r}")


def map_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "country": row["country"].strip(),
        "location_name": row["location_name"].strip(),
        "last_updated": parse_datetime(row["last_updated"]),
        "wind_degree": int(row["wind_degree"]),
        "wind_kph": float(row["wind_kph"]),
        "wind_direction": WindDirection(row["wind_direction"].strip()),
        "temperature_celsius": float(row["temperature_celsius"]),
        "sunrise": parse_clock(row["sunrise"]),
        "sunset": parse_clock(row["sunset"]),
        "moonrise": parse_clock(row["moonrise"]),
        "moonset": parse_clock(row["moonset"]),
        "moon_phase": row["moon_phase"].strip(),
        "moon_illumination": int(row["moon_illumination"]),
    }


def iter_csv_rows(csv_path: Path) -> Iterator[dict[str, object]]:
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield map_row(row)


def chunks(iterator: Iterator[dict[str, object]], chunk_size: int) -> Iterator[list[dict[str, object]]]:
    bucket: list[dict[str, object]] = []
    for item in iterator:
        bucket.append(item)
        if len(bucket) >= chunk_size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket


def import_csv(csv_path: Path, batch_size: int) -> int:
    total = 0
    Base.metadata.create_all(bind=engine, tables=[WeatherRaw.__table__])
    with engine.begin() as conn:
        for batch in chunks(iter_csv_rows(csv_path), batch_size):
            conn.execute(insert(WeatherRaw), batch)
            total += len(batch)
            print(f"Inserted {total} rows...", flush=True)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Import weather CSV into weather_raw table.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("GlobalWeatherRepository.csv"),
        help="Path to input CSV file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Number of rows per INSERT batch.",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv}")

    inserted = import_csv(args.csv, args.batch_size)
    print(f"Done. Inserted {inserted} rows into weather_raw.")


if __name__ == "__main__":
    main()
