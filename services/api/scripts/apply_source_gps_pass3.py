"""Third GPS batch for remaining NEW-* with published venue/waterbody coords."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "research_source_gps_2026-11-15"

POINTS = [
    {
        "legacy": "NEW-015",
        "lat": 55.80806,
        "lng": 38.65444,
        "query": "Rade & Wabe @ озеро Байкал, Большие Дворы",
        "evidence": "wikimapia Озеро Байкал (Большие Дворы) 55°48'29\"N 38°39'26\"E; Yandex org park in Bolshiye Dvory",
    },
    {
        "legacy": "NEW-016",
        "lat": 55.839557,
        "lng": 37.321766,
        "query": "Red Wake, Красногорск, пруд Старая Плотина",
        "evidence": "mayak.app Wake park RED GPS 55.839557,37.321766 at пруд Старая плотина",
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
            row = cur.fetchone()
            print("SAVED" if row else "SKIP", p["legacy"], row)
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


if __name__ == "__main__":
    main()
