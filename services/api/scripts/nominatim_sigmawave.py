"""Nominatim for SigmaWave street address only."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.geocode import geocode_nominatim  # noqa: E402

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"


def main() -> None:
    queries = [
        ("NEW-021", "Россия, Москва, улица Исаковского, 37к1с2"),
        ("NEW-021b", "Россия, Москва, улица Исаковского, 37 корпус 1 строение 2"),
        ("NEW-014", "Россия, Московская область, Егорьевский округ, деревня Семёновская, КП Любляна"),
        ("NEW-023", "Россия, Мытищи, Мегаспорт"),
    ]
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        for key, q in queries:
            legacy = key.replace("b", "")
            print("QUERY", key, q)
            hit = geocode_nominatim(q)
            print("HIT", hit)
            time.sleep(1.2)
            if hit is None:
                continue
            if key.endswith("b"):
                continue  # just probe
            if legacy != "NEW-021":
                # only save NEW-021 from street; others may be coarse
                if legacy == "NEW-023":
                    print("SKIP auto-save coarse venue", legacy)
                    continue
                if legacy == "NEW-014":
                    print("SKIP auto-save КП without exact building", legacy)
                    continue
            cur.execute(
                """
                UPDATE staging_candidates
                SET approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                    approx_precision = 'address',
                    approx_geocode_query = %(query)s,
                    approx_geocoded_at = now(),
                    approx_geocode_provider = 'nominatim_source_pass_2026-11-15',
                    geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
                    source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                    updated_at = now()
                WHERE legacy_row_id = %(legacy)s AND approx_point IS NULL
                RETURNING legacy_row_id
                """,
                {
                    "legacy": "NEW-021",
                    "lat": hit.lat,
                    "lng": hit.lng,
                    "query": q[:500],
                    "note": f"source_gps:nominatim for Исаковского 37к1с2; pier №14 still approximate building-level"[:900],
                },
            )
            print("SAVED", cur.fetchone())
            conn.commit()
            break


if __name__ == "__main__":
    main()
