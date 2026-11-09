
import psycopg

from . import config


def get_connection():
    return psycopg.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def initialize_db() -> None:
    schema_path = config.BASE_DIR / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8-sig")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)