"""Batch-geocode staging candidates via Yandex. Sets approximate pins only."""

from __future__ import annotations

import argparse
import sys
import time

from .config import settings
from .db import get_connection
from .geocode import build_geocode_query, geocode_yandex, normalize_query

UPDATE_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = %(precision)s,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = 'yandex_geocoder',
  geo_status = CASE
    WHEN geo_status = 'verified' THEN geo_status
    ELSE 'approximate'
  END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geocode staging candidates (approximate only).")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--sleep", type=float, default=0.15, help="Pause between geocoder calls")
    parser.add_argument("--force", action="store_true", help="Re-geocode even if approx_point exists")
    args = parser.parse_args(argv)

    api_key = (settings.yandex_maps_api_key or "").strip()
    if not api_key:
        print("ERROR: YANDEX_MAPS_API_KEY is empty", file=sys.stderr)
        return 2

    where = "TRUE" if args.force else "approx_point IS NULL"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id::text, raw_name, raw_region, raw_address
                FROM staging_candidates
                WHERE {where}
                ORDER BY imported_at ASC
                LIMIT %s
                """,
                (args.limit,),
            )
            rows = cur.fetchall()

        ok = fail = skip = 0
        for cand_id, name, region, address in rows:
            try:
                query, precision_hint = build_geocode_query(name, region, address)
                query = normalize_query(query)
            except ValueError:
                skip += 1
                print(f"SKIP {name}: no geocodeable fields")
                continue

            try:
                hit = geocode_yandex(api_key, query)
            except Exception as exc:  # noqa: BLE001
                fail += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
                time.sleep(args.sleep)
                continue

            if hit is None:
                fail += 1
                print(f"FAIL {name}: empty geocoder result for [{query}]")
                time.sleep(args.sleep)
                continue

            with conn.cursor() as cur:
                cur.execute(
                    UPDATE_SQL,
                    {
                        "id": cand_id,
                        "lat": hit.lat,
                        "lng": hit.lng,
                        "precision": precision_hint,
                        "query": query,
                    },
                )
            conn.commit()
            ok += 1
            print(
                f"OK {name}: {hit.lat:.5f},{hit.lng:.5f} "
                f"precision={precision_hint} query=[{query}]"
            )
            time.sleep(args.sleep)

    print(f"done ok={ok} fail={fail} skip={skip} total_seen={len(rows)}")
    print("NOTE: geo_status becomes approximate; publication_status stays draft; not verified.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
