import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://weatheruser:weatherpass@localhost:5432/weatherdb")


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
