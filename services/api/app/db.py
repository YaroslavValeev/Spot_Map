from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg

from .config import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()
