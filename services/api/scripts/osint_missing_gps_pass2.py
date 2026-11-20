"""Second OSINT batch for remaining missing GPS."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "osint_source_gps_2026-11-18"

POINTS = [
    {
        "legacy": "59",
        "lat": 55.801182,
        "lng": 37.755796,
        "query": "WakeTeamPool @ бассейн РГУФК, Сиреневый б-р 2",
        "address": "Москва, Сиреневый бульвар, 2с1а, бассейн РГУФК / Измайлово",
        "disciplines": "CABLE_POOL",
        "note": "source_gps:okclub бассейн РГУФК 55.801182,37.755796; waketeampool.ru Сиреневый 2с1а; +79858414910",
    },
    {
        "legacy": "NEW-039",
        "lat": 56.2239,
        "lng": 41.2829,
        "query": "Добрый / Good Wake Park @ парк-отель Доброград Grand",
        "address": "Владимирская обл., Доброград, за корпусом GRAND парк-отеля «Доброград» (подъезд со стороны школы МИР)",
        "disciplines": "CABLE_CIRCUIT;CABLE_REVERSE",
        "note": "source_gps:park-hotel Grand GPS N56.2239 E41.2829; dobrograd.ru — вейк-парк за корпусом Grand; +79157792387 goodwakepark.ru",
    },
    {
        "legacy": "45",
        "lat": 0.0,
        "lng": 0.0,
        "query": "OceanSpirit",
        "address": "Москва, ул. Исаковского, 37к1с1 (не 37к2с1)",
        "disciplines": None,
        "note": "osint_hold: registry — координат здания OceanSpirit нет; не путать с 37к2с1",
        "skip": True,
        "address_only": True,
    },
    {
        "legacy": "68",
        "lat": 55.982393,
        "lng": 37.565241,
        "query": "Moswake, Троицкое",
        "address": "МО, Мытищи, с. Троицкое, база отдыха «Троицкое»",
        "disciplines": "WAKESURF;WAKEBOARD_BOAT",
        "note": "source_gps:Troitskoe base 55.982393,37.565241; staging Moswake Троицкое — confirm berth vs EasyWake/Barmaley",
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
  raw_address = COALESCE(%(address)s, raw_address),
  raw_disciplines = COALESCE(%(disciplines)s, raw_disciplines),
  source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
  updated_at = now()
WHERE legacy_row_id = %(legacy)s
  AND publication_status = 'draft'
  AND approx_point IS NULL
RETURNING legacy_row_id, raw_name
"""


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        for p in POINTS:
            if p.get("address_only"):
                cur.execute(
                    """
                    UPDATE staging_candidates
                    SET raw_address = COALESCE(%(address)s, raw_address),
                        source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                        updated_at = now()
                    WHERE legacy_row_id = %(legacy)s AND publication_status='draft'
                    RETURNING legacy_row_id
                    """,
                    {
                        "legacy": p["legacy"],
                        "address": p.get("address"),
                        "note": p["note"][:900],
                    },
                )
                print("META", p["legacy"], cur.fetchone())
                continue
            if p.get("skip"):
                print("SKIP", p["legacy"])
                continue
            cur.execute(
                SQL,
                {
                    "legacy": p["legacy"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "query": p["query"][:500],
                    "provider": PROVIDER,
                    "address": p.get("address"),
                    "disciplines": p.get("disciplines"),
                    "note": p["note"][:900],
                },
            )
            rows = cur.fetchall()
            print("SAVED" if rows else "NONE", p["legacy"], rows)

        # Hide empty-GPS duplicates when a twin with GPS exists
        cur.execute(
            """
            UPDATE staging_candidates a
            SET publication_status = 'hidden',
                source_snapshot = left(coalesce(a.source_snapshot,'') || E'\\n' ||
                  'dedupe_2026-11-18: hidden empty-GPS duplicate twin', 2000),
                updated_at = now()
            WHERE a.approx_point IS NULL
              AND a.publication_status = 'draft'
              AND EXISTS (
                SELECT 1 FROM staging_candidates b
                WHERE b.legacy_row_id = a.legacy_row_id
                  AND b.id <> a.id
                  AND b.approx_point IS NOT NULL
                  AND b.publication_status IN ('draft','pending')
              )
            RETURNING a.legacy_row_id, a.raw_name
            """
        )
        for r in cur.fetchall():
            print("HIDDEN", r)

        # Special enrich WakeStyle phones on all draft rows with GPS
        cur.execute(
            """
            UPDATE staging_candidates
            SET source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                updated_at = now()
            WHERE legacy_row_id IN ('10','11')
              AND publication_status = 'draft'
              AND coalesce(source_snapshot,'') NOT LIKE '%%booking_phones_2026-11-18%%'
            RETURNING legacy_row_id
            """,
            {
                "note": (
                    "booking_phones_2026-11-18: +79997104295 Кирилл (TG), +79999997178 Артём (TG); "
                    "channel t.me/wakestylespot; Spot=Крылатская 8к1 ×3 Spin reverse; "
                    "Pool=Живописная 21с1 winter Spin"
                )
            },
        )
        print("PHONE_NOTE", cur.fetchall())
        conn.commit()

        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address,
                   ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
            FROM staging_candidates
            WHERE legacy_row_id IN ('10','11','8','19','29','59','71','68','NEW-039','NEW-023')
              AND publication_status = 'draft'
            ORDER BY legacy_row_id
            """
        )
        print("CHECK")
        for r in cur.fetchall():
            print(dict(r))

        cur.execute(
            """
            SELECT count(*)::int
            FROM staging_candidates
            WHERE approx_point IS NULL AND publication_status='draft'
            """
        )
        print("STILL_MISSING_DRAFT", cur.fetchone()["count"])


if __name__ == "__main__":
    main()
