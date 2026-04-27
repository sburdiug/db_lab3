import argparse
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from migrate_stage3_to_mysql import build_mysql_url, migrate_stage3_to_mysql
from models import AstronomyInfo, WeatherRecord


def create_mysql_session_factory():
    load_dotenv()
    mysql_engine = create_engine(build_mysql_url(), future=True)
    return sessionmaker(bind=mysql_engine, autoflush=False, autocommit=False, expire_on_commit=False)


def run_query_by_country_and_date(*, session_factory, country: str, selected_date: date, limit: int) -> None:
    with session_factory() as session:
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


def run_query_by_date_good_weather(*, session_factory, selected_date: date, limit: int) -> None:
    with session_factory() as session:
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


def menu_query_by_country_and_date(*, session_factory) -> None:
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
    run_query_by_country_and_date(
        session_factory=session_factory,
        country=country,
        selected_date=selected_date,
        limit=limit,
    )


def menu_query_by_date_good_weather(*, session_factory) -> None:
    date_raw = input("Date (YYYY-MM-DD): ").strip()
    if not date_raw:
        print("Date is required.")
        return
    selected_date = date.fromisoformat(date_raw)

    limit = prompt_int("Limit", 50)
    run_query_by_date_good_weather(
        session_factory=session_factory,
        selected_date=selected_date,
        limit=limit,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Final stage: migrate PostgreSQL stage3 to MySQL and open menu.")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for migration copy.")
    args = parser.parse_args()

    migrate_stage3_to_mysql(batch_size=args.batch_size)
    session_factory = create_mysql_session_factory()

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
                menu_query_by_country_and_date(session_factory=session_factory)
            elif choice == "2":
                menu_query_by_date_good_weather(session_factory=session_factory)
            elif choice == "3":
                print("Bye.")
                return
            else:
                print("Unknown option. Use 1, 2 or 3.")
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
