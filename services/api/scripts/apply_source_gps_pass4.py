"""Fourth GPS batch + EasyWake address correction (official: Троицкое)."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "research_source_gps_2026-11-15"

POINTS = [
    {
        "legacy": "NEW-012",
        "lat": 55.698523,
        "lng": 37.887525,
        "query": "GreenWood Wake Park, Наташинские пруды, вход ул. Попова",
        "evidence": "RIAMO Люберцы coords 55.698523,37.887525 for Наташинские пруды / Greenwood; urbanplaces GreenWood Park 55.69978,37.886373",
    },
    {
        "legacy": "NEW-022",
        "lat": 55.982393,
        "lng": 37.565241,
        "query": "EasyWake @ база отдыха Троицкое",
        "evidence": "official easywake.ru: село Троицкое, база отдыха Троицкое (not Новоалександровский залив as research hint); base GPS axaa 55.982393,37.565241",
    },
]

SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = 'address',
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE WHEN geo_status = 'verified' THEN geo_status ELSE 'approximate' END,
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND publication_status <> 'published'
  AND approx_point IS NULL
RETURNING legacy_row_id, raw_name
"""


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        # Correct EasyWake address text to match official site (keep old in snapshot).
        cur.execute(
            """
            UPDATE staging_candidates
            SET raw_address = %(addr)s,
                source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                updated_at = now()
            WHERE legacy_row_id = 'NEW-022'
              AND coalesce(source_snapshot,'') NOT LIKE '%%address_correction_2026-11-15: EasyWake%%'
            RETURNING legacy_row_id
            """,
            {
                "addr": "село Троицкое, база отдыха «Троицкое» (офиц. easywake.ru; research hint был Новоалександровский залив)",
                "note": "address_correction_2026-11-15: EasyWake official site = Троицкое база отдыха, not Новоалександровский залив",
            },
        )
        print("ADDR", cur.fetchone())

        for p in POINTS:
            cur.execute(
                SQL,
                {
                    "legacy": p["legacy"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "query": p["query"][:500],
                    "provider": PROVIDER,
                    "note": f"source_gps:{p['evidence']}"[:900],
                },
            )
            print("SAVED" if cur.fetchone() else "SKIP", p["legacy"])
        conn.commit()

        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL
            ORDER BY legacy_row_id
            """
        )
        miss = cur.fetchall()
        print("REMAINING", len(miss))
        for r in miss:
            print(f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_address']}")

        cur.execute(
            """
            SELECT
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%')::int AS new_total,
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NOT NULL)::int AS with_gps,
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL)::int AS missing
            FROM staging_candidates
            """
        )
        print("COUNTS", dict(cur.fetchone()))


if __name__ == "__main__":
    main()
