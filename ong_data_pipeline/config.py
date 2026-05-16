import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_database_url() -> str | None:
    """Return a SQLAlchemy-compatible database URL from env vars.

    Priority:
      - AIVEN_DB_URL
      - SQLALCHEMY_DATABASE_URL / DATABASE_URL
      - DB_USER/DB_PASS/DB_HOST/DB_NAME
    """
    return (
        os.getenv("AIVEN_DB_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or (
            os.getenv("DB_USER")
            and os.getenv("DB_PASS")
            and os.getenv("DB_HOST")
            and os.getenv("DB_NAME")
            and (
                f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','3306')}/{os.getenv('DB_NAME')}"
            )
        )
    )


def get_engine(echo: bool = False):
    url = get_database_url()
    if not url:
        return None
    return create_engine(url, echo=echo, future=True)
