import os
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect

from db import engine
from import_weather_raw import import_csv


def build_jdbc_url() -> str:
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise ValueError("DB_NAME is not set in .env")
    return f"jdbc:postgresql://{host}:{port}/{db_name}"


def table_exists(table_name: str) -> bool:
    with engine.connect() as conn:
        inspector = inspect(conn)
        return inspector.has_table(table_name, schema="public")


def ensure_raw_stage(csv_path: Path, batch_size: int) -> None:
    if table_exists("weather_record") and table_exists("astronomy_info"):
        print("Stage 2 tables already exist. weather_raw bootstrap is not required.")
        return

    if table_exists("weather_raw"):
        print("weather_raw already exists. Skipping import.")
        return

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print("weather_raw is missing. Importing CSV...")
    inserted = import_csv(csv_path=csv_path, batch_size=batch_size)
    print(f"Import finished. Inserted {inserted} rows into weather_raw.")


def run_stage2_migration() -> None:

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    if not user:
        raise ValueError("DB_USER is not set in .env")

    liquibase_cmd = os.getenv("LIQUIBASE_CMD", "liquibase")
    if not shutil.which(liquibase_cmd):
        raise RuntimeError(
            "Liquibase executable not found. Install Liquibase or set LIQUIBASE_CMD in .env."
        )

    changelog = Path("liquibase/changelog/db.changelog-master.yaml")
    if not changelog.exists():
        raise FileNotFoundError(f"Changelog not found: {changelog}")

    command = [
        liquibase_cmd,
        f"--changelog-file={changelog.as_posix()}",
        f"--url={build_jdbc_url()}",
        f"--username={user}",
        f"--password={password}",
        "update",
    ]

    child_env = os.environ.copy()
    child_env.pop("LIQUIBASE_CMD", None)

    subprocess.run(command, check=True, env=child_env)
    print("Liquibase changes applied.")


def run_liquibase_update() -> None:
    load_dotenv()

    csv_path = Path(os.getenv("CSV_PATH", "GlobalWeatherRepository.csv"))
    batch_size = int(os.getenv("IMPORT_BATCH_SIZE", "5000"))

    ensure_raw_stage(csv_path=csv_path, batch_size=batch_size)
    run_stage2_migration()


if __name__ == "__main__":
    run_liquibase_update()
