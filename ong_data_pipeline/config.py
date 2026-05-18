import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_database_url() -> str | None:
    url = (
        os.getenv("AIVEN_DB_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
    )
    # SQLAlchemy 2.x não aceita postgres://, só postgresql://
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if url:
        return url

    # Fallback por partes — só monta se TODAS as variáveis existirem
    required = ["DB_USER", "DB_PASS", "DB_HOST", "DB_NAME"]
    if all(os.getenv(v) for v in required):
        return (
            f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"
        )

    return None


def get_engine(echo: bool = False):
    url = get_database_url()
    if not url:
        return None
    return create_engine(url, echo=echo, future=True)
