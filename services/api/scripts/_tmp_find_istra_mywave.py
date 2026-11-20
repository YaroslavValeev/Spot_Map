import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id::text, legacy_row_id, raw_name, raw_region, raw_address,
               geo_status, publication_status,
               approx_point IS NOT NULL AS has_gps,
               ST_Y(approx_point::geometry) AS lat,
               ST_X(approx_point::geometry) AS lng
        FROM staging_candidates
        WHERE raw_name ILIKE '%istra%'
           OR raw_name ILIKE '%истра%'
           OR raw_name ILIKE '%mywave%'
           OR raw_name ILIKE '%озерн%'
           OR raw_address ILIKE '%истра%'
           OR raw_address ILIKE '%озерн%'
           OR raw_address ILIKE '%романтик%'
           OR raw_name ILIKE '%skywake%'
           OR raw_name ILIKE '%onewake%'
        ORDER BY legacy_row_id
        """
    )
    rows = cur.fetchall()
    print("STAGING", len(rows))
    for r in rows:
        print(dict(r))
    cur.execute(
        """
        SELECT id::text, display_name, publication_status, geo_status,
               ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
        FROM spots
        WHERE display_name ILIKE '%istra%'
           OR display_name ILIKE '%mywave%'
           OR display_name ILIKE '%озерн%'
           OR display_name ILIKE '%романтик%'
           OR display_name ILIKE '%onewake%'
        """
    )
    print("SPOTS", [dict(r) for r in cur.fetchall()])
