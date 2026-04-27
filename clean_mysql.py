import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text


def quote_identifier(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def build_mysql_url() -> str:
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    name = os.getenv("MYSQL_DB_NAME")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD", "")

    if not name or not user:
        raise ValueError("Set MYSQL_HOST/MYSQL_PORT/MYSQL_DB_NAME/MYSQL_USER/MYSQL_PASSWORD in .env")

    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"


def drop_all_tables_mysql() -> None:
    load_dotenv()

    engine = create_engine(build_mysql_url(), future=True)
    with engine.begin() as conn:
        inspector = inspect(conn)
        table_names = inspector.get_table_names()
        if not table_names:
            print("No tables found in MySQL database.")
            return

        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table_name in table_names:
            conn.execute(text(f"DROP TABLE IF EXISTS {quote_identifier(table_name)}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print(f"Dropped {len(table_names)} MySQL table(s): {', '.join(table_names)}")


if __name__ == "__main__":
    drop_all_tables_mysql()
