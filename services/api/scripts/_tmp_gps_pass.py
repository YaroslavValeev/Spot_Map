"""One-off GPS/dedup pass helper. Temporary; do not invent coords."""
from __future__ import annotations

import json
import sys

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "inspect"
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'staging_candidates'
            ORDER BY ordinal_position
            """
        )
        cols = cur.fetchall()
        print("=== COLUMNS ===")
        for c in cols:
            print(f"{c['column_name']}: {c['data_type']}")

        if mode == "schema":
            return

        # Probe a row to see which id field exists
        cur.execute("SELECT * FROM staging_candidates LIMIT 1")
        sample = cur.fetchone()
        print("=== SAMPLE KEYS ===")
        print(sorted(sample.keys()) if sample else None)

        cur.execute(
            """
            SELECT *
            FROM staging_candidates
            WHERE COALESCE(legacy_row_id, candidate_id::text, id::text) IN (
              'SM-056','NEW-005','SM-037','NEW-010','SM-062','NEW-037','NEW-007'
            )
            OR raw_name ILIKE '%orlov%'
            OR display_name ILIKE '%orlov%'
            OR raw_name ILIKE '%go wake%'
            OR display_name ILIKE '%go wake%'
            OR raw_name ILIKE '%local surf%'
            OR display_name ILIKE '%local surf%'
            OR raw_name ILIKE '%dolwake%'
            OR display_name ILIKE '%dolwake%'
            ORDER BY 1
            """
        )
        # fallback if columns differ
        try:
            rows = cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            print("query failed", exc)
            return
        print("=== DEDUP ROWS ===", len(rows))
        for r in rows:
            slim = {k: r[k] for k in r if k not in ("snapshot",) or True}
            # print compact
            out = {}
            for k, v in r.items():
                if k == "snapshot" and isinstance(v, dict):
                    out["match_note"] = (v.get("source_meta") or {}).get("match_note")
                    out["source_url"] = (v.get("source_meta") or {}).get("source_url") or v.get("source_url")
                    out["address_hint"] = (v.get("source_meta") or {}).get("address_hint")
                elif k not in ("snapshot",):
                    out[k] = v
            print(json.dumps(out, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
