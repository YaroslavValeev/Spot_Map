"""Seed verified_booking_links from spot_public_profiles.booking_url."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.rows import dict_row

from app.booking_redirect import ensure_booking_link
from app.config import settings


def main() -> None:
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT spot_id::text, booking_url
                FROM spot_public_profiles
                WHERE booking_url IS NOT NULL AND length(trim(booking_url)) > 0
                """
            )
            rows = cur.fetchall()
        n_ok = n_skip = 0
        for row in rows:
            link_id = ensure_booking_link(
                conn,
                spot_id=row["spot_id"],
                target_url=row["booking_url"],
            )
            if link_id:
                n_ok += 1
                print("OK", row["spot_id"][:8], link_id[:8], row["booking_url"][:60])
            else:
                n_skip += 1
                print("SKIP", row["spot_id"][:8], row["booking_url"][:60])
        conn.commit()
    print(f"done ok={n_ok} skip={n_skip}")


if __name__ == "__main__":
    main()
