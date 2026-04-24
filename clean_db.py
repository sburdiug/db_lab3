from sqlalchemy import text

from db import engine


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def drop_all_tables() -> None:
    with engine.begin() as conn:
        table_names = conn.execute(
            text(
                "SELECT tablename "
                "FROM pg_tables "
                "WHERE schemaname = 'public' "
                "ORDER BY tablename"
            )
        ).scalars().all()

        if not table_names:
            print("No tables found in schema 'public'.")
            return

        for table_name in table_names:
            conn.execute(text(f"DROP TABLE IF EXISTS {quote_identifier(table_name)} CASCADE"))

    print(f"Dropped {len(table_names)} table(s): {', '.join(table_names)}")


if __name__ == "__main__":
    drop_all_tables()
