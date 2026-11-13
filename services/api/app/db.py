from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from .config import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    # connect_timeout avoids hung health checks when Docker/WSL networking stalls
    conn = psycopg.connect(settings.database_url, connect_timeout=5)
    try:
        yield conn
    finally:
        conn.close()
