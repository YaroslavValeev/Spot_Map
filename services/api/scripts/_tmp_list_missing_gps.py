import json
import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_region, raw_address, raw_disciplines,
               candidate_kind, geo_status, publication_status, source_url,
               public_telegram_url, official_or_public_website,
               left(coalesce(source_snapshot,''), 180) AS snap
        FROM staging_candidates
        WHERE approx_point IS NULL
          AND publication_status <> 'published'
          AND publication_status <> 'merged'
        ORDER BY
          CASE WHEN legacy_row_id LIKE 'NEW-%%' THEN 0 ELSE 1 END,
          legacy_row_id
        """
    )
    rows = cur.fetchall()
    print("MISSING", len(rows))
    for r in rows:
        print(
            f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_region']}|{r['raw_address']}|"
            f"{r['raw_disciplines']}|{r['geo_status']}|{r['source_url']}"
        )
    # Wake style related
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_address, approx_point IS NOT NULL AS has_gps,
               geo_status, publication_status
        FROM staging_candidates
        WHERE raw_name ILIKE '%wake%style%' OR raw_name ILIKE '%wakestyle%'
           OR raw_address ILIKE '%крылат%' OR raw_address ILIKE '%живописн%'
        ORDER BY legacy_row_id
        """
    )
    print("WAKESTYLE_HITS")
    for r in cur.fetchall():
        print(dict(r))
