import argparse
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, insert, text

from models import AstronomyInfo, Base, WeatherRecord


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ValueError(f"Environment variable {name} is required")
    return value


def build_postgres_url() -> str:
    host = os.getenv("PG_HOST", os.getenv("DB_HOST", "localhost"))
    port = os.getenv("PG_PORT", os.getenv("DB_PORT", "5432"))
    name = os.getenv("PG_NAME", os.getenv("DB_NAME"))
    user = os.getenv("PG_USER", os.getenv("DB_USER"))
    password = os.getenv("PG_PASSWORD", os.getenv("DB_PASSWORD", ""))

    if not name or not user:
        raise ValueError("Set PG_* or DB_* variables for source PostgreSQL connection")

    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


def build_mysql_url() -> str:
    host = get_env("MYSQL_HOST", "localhost")
    port = get_env("MYSQL_PORT", "3306")
    name = get_env("MYSQL_DB_NAME")
    user = get_env("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD", "")

    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


def ensure_mysql_schema(mysql_engine) -> None:
    Base.metadata.create_all(bind=mysql_engine, tables=[WeatherRecord.__table__, AstronomyInfo.__table__])


def clear_mysql_stage3(mysql_engine) -> None:
    with mysql_engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        conn.execute(text("TRUNCATE TABLE astronomy_info"))
        conn.execute(text("TRUNCATE TABLE weather_record"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def copy_weather_record(pg_engine, mysql_engine, batch_size: int) -> int:
    query = text(
        """
        SELECT
            id,
            country,
            location_name,
            last_updated,
            temperature_celsius,
            wind_degree,
            wind_kph,
            wind_direction,
            should_go_outside
        FROM weather_record
        ORDER BY id
        """
    )

    total = 0
    with pg_engine.connect() as src_conn:
        result = src_conn.execute(query)
        while True:
            rows = result.mappings().fetchmany(batch_size)
            if not rows:
                break
            payload = [dict(row) for row in rows]
            with mysql_engine.begin() as dst_conn:
                dst_conn.execute(insert(WeatherRecord), payload)
            total += len(payload)
            print(f"Copied weather_record: {total}")
    return total


def copy_astronomy_info(pg_engine, mysql_engine, batch_size: int) -> int:
    query = text(
        """
        SELECT
            id,
            weather_record_id,
            sunrise,
            sunset,
            moonrise,
            moonset,
            moon_phase,
            moon_illumination
        FROM astronomy_info
        ORDER BY id
        """
    )

    total = 0
    with pg_engine.connect() as src_conn:
        result = src_conn.execute(query)
        while True:
            rows = result.mappings().fetchmany(batch_size)
            if not rows:
                break
            payload = [dict(row) for row in rows]
            with mysql_engine.begin() as dst_conn:
                dst_conn.execute(insert(AstronomyInfo), payload)
            total += len(payload)
            print(f"Copied astronomy_info: {total}")
    return total


def count_rows(engine, table_name: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one())


def migrate_stage3_to_mysql(batch_size: int = 5000) -> dict[str, int]:
    load_dotenv()

    pg_engine = create_engine(build_postgres_url(), future=True)
    mysql_engine = create_engine(build_mysql_url(), future=True)

    ensure_mysql_schema(mysql_engine)
    clear_mysql_stage3(mysql_engine)

    copied_weather = copy_weather_record(pg_engine, mysql_engine, batch_size)
    copied_astronomy = copy_astronomy_info(pg_engine, mysql_engine, batch_size)

    pg_weather_count = count_rows(pg_engine, "weather_record")
    pg_astronomy_count = count_rows(pg_engine, "astronomy_info")
    my_weather_count = count_rows(mysql_engine, "weather_record")
    my_astronomy_count = count_rows(mysql_engine, "astronomy_info")

    print("--- Verification ---")
    print(f"PostgreSQL weather_record: {pg_weather_count}")
    print(f"MySQL      weather_record: {my_weather_count}")
    print(f"PostgreSQL astronomy_info: {pg_astronomy_count}")
    print(f"MySQL      astronomy_info: {my_astronomy_count}")
    print(f"Copied weather_record rows: {copied_weather}")
    print(f"Copied astronomy_info rows: {copied_astronomy}")

    if pg_weather_count != my_weather_count or pg_astronomy_count != my_astronomy_count:
        raise RuntimeError("Row counts mismatch after migration to MySQL")

    print("Migration completed successfully.")
    return {
        "pg_weather_record": pg_weather_count,
        "pg_astronomy_info": pg_astronomy_count,
        "mysql_weather_record": my_weather_count,
        "mysql_astronomy_info": my_astronomy_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate stage3 data from PostgreSQL to MySQL.")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for copy.")
    args = parser.parse_args()

    migrate_stage3_to_mysql(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
