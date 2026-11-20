"""Find ring/reverse/boat candidates related to Myakinino / Polati / Lawa / Wake-home."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NEEDLES = (
    "%живопис%",
    "%мякин%",
    "%полат%",
    "%кроват%",
    "%lawa%",
    "%wake-home%",
    "%wakehome%",
    "%wake home%",
    "%кольц%",
    "%cable_ring%",
    "%ring%",
)


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, display_name, publication_status, geo_status, operation_status,
                       ST_Y(point::geometry) lat, ST_X(point::geometry) lng, address_text
                FROM spots
                WHERE display_name ILIKE ANY(%s)
                   OR address_text ILIKE ANY(%s)
                   OR locality ILIKE ANY(%s)
                ORDER BY display_name
                """,
                [list(NEEDLES)] * 3,
            )
            print("=== SPOTS ===")
            for r in cur.fetchall():
                print(r)

            cur.execute(
                """
                SELECT id::text, legacy_row_id, raw_name, raw_address, raw_region, raw_disciplines,
                       publication_status, geo_status, operation_status,
                       ST_Y(approx_point::geometry) lat, ST_X(approx_point::geometry) lng
                FROM staging_candidates
                WHERE raw_name ILIKE ANY(%s)
                   OR raw_address ILIKE ANY(%s)
                   OR raw_region ILIKE ANY(%s)
                   OR raw_disciplines ILIKE ANY(%s)
                ORDER BY raw_name
                """,
                [list(NEEDLES)] * 4,
            )
            print("=== STAGING ===")
            for r in cur.fetchall():
                print(r)

            cur.execute(
                """
                SELECT c.id::text, c.name, c.publication_status, c.geo_status,
                       ST_Y(c.point::geometry) lat, ST_X(c.point::geometry) lng,
                       s.display_name AS spot_name
                FROM cable_installations c
                LEFT JOIN spots s ON s.id = c.spot_id
                ORDER BY c.name
                LIMIT 50
                """
            )
            print("=== CABLE INSTALLATIONS ===")
            for r in cur.fetchall():
                print(r)

            # Count published by discipline tags via map enrichment raw
            cur.execute(
                """
                SELECT raw_disciplines, count(*) 
                FROM staging_candidates
                WHERE publication_status IN ('published','merged','draft','pending','hidden')
                  AND (raw_disciplines ILIKE '%кольц%' OR raw_disciplines ILIKE '%ring%'
                       OR raw_disciplines ILIKE '%RING%' OR raw_disciplines ILIKE '%cable_ring%')
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT 30
                """
            )
            print("=== RING-ISH DISCIPLINES ===")
            for r in cur.fetchall():
                print(r)


if __name__ == "__main__":
    main()
