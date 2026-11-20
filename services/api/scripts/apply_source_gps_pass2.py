"""Second GPS batch + fix wrong Orlovsky note on legacy 56 (Wakein)."""
from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
PROVIDER = "research_source_gps_2026-11-15"

SOURCE_POINTS: list[dict[str, Any]] = [
    {
        "legacy": "NEW-006",
        "lat": 54.960890,
        "lng": 37.460372,
        "query": "Высокий полёт @ парк-отель Воздвиженское, Авангард",
        "evidence": "official v-parkhotel.ru/contacts GPS 54.960890,37.460372 for park-hotel where wake park operates",
    },
    {
        "legacy": "NEW-017",
        "lat": 55.5458,
        "lng": 37.9766,
        "query": "Tony Wake, Верхнее Мячково, Набережная 39",
        "evidence": "directory GPS for Усадьба Мячково / Набережная 39; tonycompany.ru same address",
    },
    {
        "legacy": "NEW-027",
        "lat": 54.8750763,
        "lng": 37.2820206,
        "query": "Парк-отель Русский / Дракино",
        "evidence": "official russian-drakino.ru/contacts GPS N54.8750763 E37.2820206",
    },
    {
        "legacy": "NEW-028",
        "lat": 56.101158,
        "lng": 40.435111,
        "query": "Водный Яркопарк, Владимир, Загородный парк",
        "evidence": "spravka-region GPS 56.101158,40.435111 for Водный ЯРКОПарк; site: Загородный парк",
    },
    {
        "legacy": "NEW-029",
        "lat": 55.1803,
        "lng": 36.7521,
        "query": "Wake Park Машково / Ivolga",
        "evidence": "bebeshka GPS for вейк парк Машково 55.1803,36.7521; Yandex org Mashkovo",
    },
    {
        "legacy": "NEW-032",
        "lat": 55.636679,
        "lng": 38.019313,
        "query": "Wake Fly Park, Малаховка, Спортивная 9",
        "evidence": "exa place listing WakeFlyPark Sportivnaya 9 GPS 55.636679,38.019313",
    },
    {
        "legacy": "NEW-033",
        "lat": 55.866567,
        "lng": 38.001965,
        "query": "We-Wake Белые Орлы @ Медвежьи Озёра 65А",
        "evidence": "domotdiha GPS for Загородный клуб Медвежьи Озера; we-wake listed at д.65а on same venue",
    },
    {
        "legacy": "NEW-034",
        "lat": 55.821705,
        "lng": 37.383556,
        "query": "Surfphoria @ Shore House, МКАД 65-66 км к5",
        "evidence": "urbanplaces GPS for Surfphoria; Shore House ~55.82145,37.384023",
    },
    {
        "legacy": "NEW-035",
        "lat": 55.982393,
        "lng": 37.565241,
        "query": "Barmaley Surf Club, Троицкое вл7Б причал 5",
        "evidence": "Yandex org address Троицкое вл7Б причал 5; base GPS from axaa Troitskoe 55.982393,37.565241 (pier area approx)",
    },
]

POINT_SQL = """
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
RETURNING id::text, legacy_row_id, raw_name
"""


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()

        # Fix mistaken Orlovsky note on Wakein (legacy 56)
        cur.execute(
            """
            UPDATE staging_candidates
            SET source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                updated_at = now()
            WHERE legacy_row_id = '56'
              AND coalesce(source_snapshot,'') NOT LIKE '%%CORRECTION_2026-11-15: legacy 56 is Wakein%%'
            RETURNING legacy_row_id, raw_name
            """,
            {
                "note": (
                    "CORRECTION_2026-11-15: legacy 56 is Wakein (Авиационная 79), NOT Орловский. "
                    "Previous Orlovsky dedup note on this row is INVALID. "
                    "Orlovsky candidate is NEW-030 only until a matching SM row is identified."
                )
            },
        )
        fix = cur.fetchone()
        print("FIX56", dict(fix) if fix else None)

        # Find any Orlovsky in registry
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address,
                   ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
            FROM staging_candidates
            WHERE raw_name ILIKE '%orlov%' OR raw_address ILIKE '%орлов%'
               OR raw_name ILIKE '%орлов%' OR raw_address ILIKE '%prudish%'
               OR raw_address ILIKE '%прудищ%'
            ORDER BY legacy_row_id
            """
        )
        print("ORLOV MATCHES", [dict(r) for r in cur.fetchall()])

        saved = 0
        for p in SOURCE_POINTS:
            note = f"source_gps:{p['evidence']}"[:900]
            cur.execute(
                POINT_SQL,
                {
                    "legacy": p["legacy"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "query": p["query"][:500],
                    "provider": PROVIDER,
                    "note": note,
                },
            )
            row = cur.fetchone()
            if row:
                saved += 1
                print(f"SAVED {row['legacy_row_id']} {row['raw_name']}")
            else:
                print(f"SKIP {p['legacy']}")
        conn.commit()

        cur.execute(
            """
            SELECT
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL)::int AS missing,
              count(*) FILTER (WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NOT NULL)::int AS with_gps
            FROM staging_candidates
            """
        )
        print("COUNTS", dict(cur.fetchone()))
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL
            ORDER BY legacy_row_id
            """
        )
        missing = cur.fetchall()
        print("STILL MISSING", len(missing))
        for r in missing:
            print(f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_address']}")


if __name__ == "__main__":
    main()
