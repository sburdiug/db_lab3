import argparse
from pathlib import Path

from sqlalchemy import inspect

from db import engine
from import_weather_raw import import_csv
from run_changes import run_liquibase_update


def table_exists(table_name: str) -> bool:
    with engine.connect() as conn:
        inspector = inspect(conn)
        return inspector.has_table(table_name, schema="public")


def run_pipeline(csv_path: Path, batch_size: int) -> None:
    weather_record_exists = table_exists("weather_record")
    astronomy_info_exists = table_exists("astronomy_info")
    if weather_record_exists and astronomy_info_exists:
        print("Stage 2 tables already exist. Skipping import and migration.")
        return

    if not table_exists("weather_raw"):
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        print("weather_raw not found. Importing CSV into weather_raw...")
        inserted = import_csv(csv_path, batch_size)
        print(f"Import finished. Inserted {inserted} rows into weather_raw.")
    else:
        print("weather_raw already exists. Skipping CSV import.")

    print("Running stage 2 migration (weather_record + astronomy_info)...")
    run_liquibase_update()

    weather_record_exists = table_exists("weather_record")
    astronomy_info_exists = table_exists("astronomy_info")
    if not weather_record_exists or not astronomy_info_exists:
        raise RuntimeError(
            "Migration did not create expected tables: weather_record and astronomy_info."
        )

    print("Stage 2 migration is complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run pipeline: ensure weather_raw exists, then run stage 2 migration."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("GlobalWeatherRepository.csv"),
        help="Path to source CSV for weather_raw import.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for CSV import into weather_raw.",
    )
    args = parser.parse_args()

    run_pipeline(csv_path=args.csv, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
