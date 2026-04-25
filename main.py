import argparse
from datetime import date
from pathlib import Path

from sqlalchemy import func, inspect, select

from db import SessionLocal, engine
from import_weather_raw import import_csv
from models import AstronomyInfo, WeatherRecord
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


def run_query_by_country_and_date(*, country: str, selected_date: date, limit: int) -> None:
    with SessionLocal() as session:
        rows = list(
            session.execute(
                select(WeatherRecord, AstronomyInfo)
                .join(AstronomyInfo, AstronomyInfo.weather_record_id == WeatherRecord.id)
                .where(func.lower(WeatherRecord.country) == country.lower())
                .where(func.date(WeatherRecord.last_updated) == selected_date)
                .order_by(WeatherRecord.last_updated.desc(), WeatherRecord.location_name.asc())
                .limit(limit)
            ).all()
        )

    if not rows:
        print("No weather records found for this country and date.")
        return

    print(f"Found {len(rows)} row(s).")
    for row in rows:
        print_short_record(row)


def run_query_by_date_good_weather(*, selected_date: date, limit: int) -> None:
    with SessionLocal() as session:
        rows = list(
            session.execute(
                select(WeatherRecord, AstronomyInfo)
                .join(AstronomyInfo, AstronomyInfo.weather_record_id == WeatherRecord.id)
                .where(func.date(WeatherRecord.last_updated) == selected_date)
                .where(WeatherRecord.should_go_outside.is_(True))
                .order_by(WeatherRecord.country.asc(), WeatherRecord.location_name.asc())
                .limit(limit)
            ).all()
        )

    if not rows:
        print("No good-weather records found for this date.")
        return

    print(f"Found {len(rows)} row(s).")
    for row in rows:
        print_short_record(row)


def print_short_record(row: tuple[WeatherRecord, AstronomyInfo]) -> None:
    weather, _ = row
    go_outside = "yes" if weather.should_go_outside else "no"
    print(
        f"{weather.country} | {weather.location_name} | "
        f"{weather.last_updated.date()} | should_go_outside: {go_outside}"
    )


def prompt_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    return int(raw)


def menu_query_by_country_and_date() -> None:
    country = input("Country: ").strip()
    if not country:
        print("Country is required.")
        return

    date_raw = input("Date (YYYY-MM-DD): ").strip()
    if not date_raw:
        print("Date is required.")
        return
    selected_date = date.fromisoformat(date_raw)

    limit = prompt_int("Limit", 50)
    run_query_by_country_and_date(country=country, selected_date=selected_date, limit=limit)


def menu_query_by_date_good_weather() -> None:
    date_raw = input("Date (YYYY-MM-DD): ").strip()
    if not date_raw:
        print("Date is required.")
        return
    selected_date = date.fromisoformat(date_raw)

    limit = prompt_int("Limit", 50)
    run_query_by_date_good_weather(selected_date=selected_date, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Weather app entry point.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("GlobalWeatherRepository.csv"),
        help="CSV path for default pipeline mode.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for default pipeline mode.",
    )
    args = parser.parse_args()

    run_pipeline(csv_path=args.csv, batch_size=args.batch_size)

    while True:
        print("\n=== Weather Menu ===")
        print("1. Query by country + date")
        print("2. Query by date where should_go_outside = TRUE")
        print("3. Exit")
        try:
            choice = input("Choose action: ").strip()
        except EOFError:
            print("\nInput stream closed. Bye.")
            return

        try:
            if choice == "1":
                menu_query_by_country_and_date()
            elif choice == "2":
                menu_query_by_date_good_weather()
            elif choice == "3":
                print("Bye.")
                return
            else:
                print("Unknown option. Use 1, 2 or 3.")
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
