"""Run map SQL fragment for promoted cables."""
from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"

SQL = """
SELECT
  c.id::text AS id,
  c.name AS name,
  (
    SELECT sc.raw_disciplines
    FROM staging_candidates sc
    WHERE sc.publication_status = 'merged'
      AND lower(trim(sc.raw_name)) = lower(trim(c.name))
    ORDER BY sc.updated_at DESC NULLS LAST
    LIMIT 1
  ) AS from_staging,
  COALESCE(
    (
      SELECT sc.raw_disciplines
      FROM staging_candidates sc
      WHERE sc.publication_status = 'merged'
        AND lower(trim(sc.raw_name)) = lower(trim(c.name))
      ORDER BY sc.updated_at DESC NULLS LAST
      LIMIT 1
    ),
    c.name || ' wakeboard cable'
  ) AS raw_disciplines
FROM cable_installations c
WHERE c.publication_status = 'published'
  AND c.name ILIKE ANY(%s)
"""

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute(SQL, (["%мякинино%", "%WakeHome%", "%полати%"],))
        for r in cur.fetchall():
            print(r)
        cur.execute(
            """
            SELECT raw_name, publication_status, raw_disciplines
            FROM staging_candidates
            WHERE raw_name ILIKE ANY(%s)
            """,
            (["%мякинино%", "%WakeHome%", "%полати%", "%Lawave%"],),
        )
        print("STAGING ROWS")
        for r in cur.fetchall():
            print(r)
