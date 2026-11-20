import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id::text, legacy_row_id, raw_name, raw_region, raw_address,
               raw_disciplines, official_or_public_website, public_telegram_url,
               source_url, left(coalesce(source_snapshot,''), 300) AS snap,
               approx_geocode_provider, geo_status, publication_status
        FROM staging_candidates
        WHERE publication_status IN ('draft','pending','hidden')
          AND (approx_point IS NULL OR geo_status = 'missing'
               OR coalesce(approx_geocode_provider,'') = 'region_centroid_v1')
        ORDER BY CASE WHEN legacy_row_id LIKE 'NEW-%' THEN 0 ELSE 1 END, legacy_row_id
        """
    )
    for r in cur.fetchall():
        print("=" * 80)
        print(r["legacy_row_id"], "|", r["raw_name"], "|", r["id"])
        print("region:", r["raw_region"])
        print("address:", r["raw_address"])
        print("disc:", r["raw_disciplines"])
        print("web:", r["official_or_public_website"] or r["source_url"])
        print("tg:", r["public_telegram_url"])
        print("provider:", r["approx_geocode_provider"])
        print("snap:", r["snap"])
