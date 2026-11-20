import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          count(*) FILTER (WHERE publication_status IN ('draft','pending','hidden')
                           AND (approx_point IS NULL OR geo_status = 'missing')) AS need_gps,
          count(*) FILTER (WHERE publication_status IN ('draft','pending','hidden')
                           AND approx_point IS NOT NULL
                           AND geo_status IN ('approximate','verified')) AS have_approx,
          count(*) FILTER (WHERE publication_status = 'published') AS published,
          count(*) FILTER (WHERE publication_status = 'merged') AS merged,
          count(*) AS total
        FROM staging_candidates
        """
    )
    print("STATS", cur.fetchone())
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_region, raw_address,
               geo_status, publication_status,
               approx_geocode_provider,
               left(coalesce(raw_disciplines,''), 80) AS disc
        FROM staging_candidates
        WHERE publication_status IN ('draft','pending','hidden')
          AND (approx_point IS NULL OR geo_status = 'missing'
               OR coalesce(approx_geocode_provider,'') = 'region_centroid_v1')
        ORDER BY
          CASE WHEN legacy_row_id LIKE 'NEW-%' THEN 0 ELSE 1 END,
          legacy_row_id
        """
    )
    rows = cur.fetchall()
    print("NEED_COUNT", len(rows))
    for r in rows:
        print(
            f"{r['legacy_row_id']:>8} | {r['geo_status']:<12} | {r['publication_status']:<8} | "
            f"{(r['approx_geocode_provider'] or '-'):<28} | {r['raw_name']} | "
            f"{(r['raw_address'] or r['raw_region'] or '')[:60]}"
        )

# what map meta says
data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=20).read())
print("META", data.get("meta"))
