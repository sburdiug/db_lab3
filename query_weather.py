import argparse
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import SessionLocal
from models import AstronomyInfo, WeatherRecord


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show full weather information by country and date."
    )
    parser.add_argument("--country", required=True, help="Country name (case-insensitive).")
    parser.add_argument(
        "--date",
        required=True,
        type=lambda value: date.fromisoformat(value),
        help="Date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--location",
        default=None,
        help="Optional exact location_name filter (case-insensitive).",
    )
    parser.add_argument(
        "--only-good-weather",
        action="store_true",
        help="Show only rows where should_go_outside = true.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum rows to print (default: 50).",
    )
    return parser.parse_args()


def print_record(row: tuple[WeatherRecord, AstronomyInfo]) -> None:
    weather, astro = row
    print("-" * 80)
    print(f"id: {weather.id}")
    print(f"country: {weather.country}")
    print(f"location_name: {weather.location_name}")
    print(f"last_updated: {weather.last_updated}")
    print(f"temperature_celsius: {weather.temperature_celsius}")
    print(f"wind_degree: {weather.wind_degree}")
    print(f"wind_kph: {weather.wind_kph}")
    print(f"wind_direction: {weather.wind_direction.value}")
    print(f"should_go_outside: {weather.should_go_outside}")
    print(f"sunrise: {astro.sunrise}")
    print(f"sunset: {astro.sunset}")
    print(f"moonrise: {astro.moonrise}")
    print(f"moonset: {astro.moonset}")
    print(f"moon_phase: {astro.moon_phase}")
    print(f"moon_illumination: {astro.moon_illumination}")


def query_weather_data(
    session: Session,
    *,
    country: str,
    selected_date: date,
    location: str | None,
    only_good_weather: bool,
    limit: int,
) -> list[tuple[WeatherRecord, AstronomyInfo]]:
    query = (
        select(WeatherRecord, AstronomyInfo)
        .join(AstronomyInfo, AstronomyInfo.weather_record_id == WeatherRecord.id)
        .where(func.lower(WeatherRecord.country) == country.lower())
        .where(func.date(WeatherRecord.last_updated) == selected_date)
        .order_by(WeatherRecord.last_updated.asc(), WeatherRecord.location_name.asc())
        .limit(limit)
    )

    if location:
        query = query.where(func.lower(WeatherRecord.location_name) == location.lower())
    if only_good_weather:
        query = query.where(WeatherRecord.should_go_outside.is_(True))

    return list(session.execute(query).all())


def main() -> None:
    args = parse_args()

    with SessionLocal() as session:
        rows = query_weather_data(
            session,
            country=args.country,
            selected_date=args.date,
            location=args.location,
            only_good_weather=args.only_good_weather,
            limit=args.limit,
        )

    if not rows:
        print("No weather records found for provided filters.")
        return

    print(f"Found {len(rows)} row(s).")
    for row in rows:
        print_record(row)


if __name__ == "__main__":
    main()
