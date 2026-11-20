"""Yandex-geocode remaining NEW-* with street-like addresses only."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.geocode import geocode_yandex  # noqa: E402

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "yandex_geocoder_source_pass_2026-11-15"

# Only queries that include a concrete street/building/named venue object — not settlement alone.
QUERIES = {
    "NEW-021": "Россия, Москва, улица Исаковского, 37к1с2",
    "NEW-015": "Россия, Московская область, Большие Дворы, озеро Байкал, вейк парк",
    "NEW-032": "Россия, Малаховка, Спортивная улица, 9",  # already has GPS; skip if set
    "NEW-014": "Россия, Московская область, Егорьевск, Семёновская, КП Любляна",
    "NEW-023": "Россия, Мытищи, Мегаспорт",
    "NEW-039": "Россия, Владимирская область, Доброград, вейк-парк Добрый",
}


def load_key() -> str:
    env_path = ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("YANDEX_MAPS_API_KEY="):
                return line.split("=", 1)[1].strip()
    return (os.environ.get("YANDEX_MAPS_API_KEY") or "").strip()


def main() -> None:
    key = load_key()
    if not key:
        print("NO_KEY")
        return
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id::text, legacy_row_id, raw_name, raw_address
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL
            ORDER BY legacy_row_id
            """
        )
        rows = cur.fetchall()
        for r in rows:
            legacy = r["legacy_row_id"]
            q = QUERIES.get(legacy)
            if not q:
                print(f"SKIP_NO_QUERY {legacy} {r['raw_name']}")
                continue
            hit = geocode_yandex(key, q)
            if hit is None:
                print(f"MISS {legacy} [{q}]")
                continue
            # Reject very coarse precision if Yandex marks it
            print(
                f"HIT {legacy} {hit.lat},{hit.lng} precision={hit.precision} q={q}"
            )
            # Only auto-save if precision looks like exact/number/street (from geocode module)
            prec = (hit.precision or "").lower()
            if prec in {"other", "region", "area", "province", "country", "locality"}:
                print(f"  REJECT coarse precision={prec}")
                continue
            cur.execute(
                """
                UPDATE staging_candidates
                SET approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                    approx_precision = 'address',
                    approx_geocode_query = %(query)s,
                    approx_geocoded_at = now(),
                    approx_geocode_provider = %(provider)s,
                    geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
                    source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                    updated_at = now()
                WHERE id = %(id)s::uuid AND approx_point IS NULL
                RETURNING legacy_row_id
                """,
                {
                    "id": r["id"],
                    "lat": hit.lat,
                    "lng": hit.lng,
                    "query": q[:500],
                    "provider": PROVIDER,
                    "note": f"source_gps:yandex_geocoder precision={hit.precision}; query={q}"[:900],
                },
            )
            saved = cur.fetchone()
            print(f"  SAVED {saved['legacy_row_id'] if saved else None}")
        conn.commit()
        cur.execute(
            """
            SELECT legacy_row_id, raw_name
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL
            ORDER BY legacy_row_id
            """
        )
        miss = cur.fetchall()
        print("REMAINING", len(miss))
        for m in miss:
            print(f"{m['legacy_row_id']}|{m['raw_name']}")


if __name__ == "__main__":
    main()
