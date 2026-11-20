import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        WITH ranked AS (
          SELECT id, legacy_row_id,
                 row_number() OVER (
                   PARTITION BY legacy_row_id
                   ORDER BY updated_at DESC NULLS LAST, imported_at DESC NULLS LAST
                 ) AS rn
          FROM staging_candidates
          WHERE publication_status = 'draft'
            AND approx_point IS NOT NULL
            AND legacy_row_id IN (
              SELECT legacy_row_id
              FROM staging_candidates
              WHERE publication_status = 'draft' AND approx_point IS NOT NULL
              GROUP BY legacy_row_id
              HAVING count(*) > 1
            )
        )
        UPDATE staging_candidates s
        SET publication_status = 'hidden',
            source_snapshot = left(
              coalesce(source_snapshot,'') || E'\\n' ||
              'dedupe_2026-11-18: hidden duplicate draft with GPS',
              2000
            ),
            updated_at = now()
        FROM ranked r
        WHERE s.id = r.id AND r.rn > 1
        RETURNING s.legacy_row_id, s.raw_name
        """
    )
    print("HIDDEN", cur.fetchall())
    conn.commit()

    cur.execute(
        """
        SELECT count(*) FILTER (
          WHERE approx_point IS NULL AND publication_status='draft'
        )::int AS missing,
        count(*) FILTER (
          WHERE approx_point IS NOT NULL AND publication_status='draft'
        )::int AS with_gps
        FROM staging_candidates
        """
    )
    print("COUNTS", dict(cur.fetchone()))

    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_address
        FROM staging_candidates
        WHERE approx_point IS NULL AND publication_status='draft'
        ORDER BY legacy_row_id
        """
    )
    rows = cur.fetchall()
    print("MISSING", len(rows))
    for r in rows:
        print(f"{r['legacy_row_id']}|{r['raw_name']}|{r['raw_address']}")
