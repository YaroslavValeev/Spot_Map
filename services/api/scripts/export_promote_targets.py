"""Export approximate NEW/SM rows ready for owner promote-geo review."""
from __future__ import annotations

import json

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id::text AS uuid, legacy_row_id, raw_name, raw_region, raw_address,
                   raw_disciplines, geo_status, publication_status,
                   ST_Y(approx_point::geometry) AS lat,
                   ST_X(approx_point::geometry) AS lng,
                   approx_geocode_provider, approx_geocode_query
            FROM staging_candidates
            WHERE approx_point IS NOT NULL
              AND publication_status = 'draft'
              AND geo_status = 'approximate'
              AND (
                legacy_row_id LIKE 'NEW-%%'
                OR legacy_row_id IN ('37','62')
              )
            ORDER BY legacy_row_id
            """
        )
        rows = [dict(r) for r in cur.fetchall()]
        out = {
            "count": len(rows),
            "note": "approximate only — promote-geo + publish is owner action",
            "items": rows,
        }
        path = (
            r"f:\Проекты MyWave\NEW2026\Spot Map\data\imports"
            r"\SpotMap_Research_Moscow_MO_2026-11-14\promote_targets_approx.json"
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("wrote", path, "count", len(rows))

        cur.execute(
            """
            SELECT legacy_row_id, raw_name, raw_address
            FROM staging_candidates
            WHERE legacy_row_id LIKE 'NEW-%%' AND approx_point IS NULL
            ORDER BY legacy_row_id
            """
        )
        miss = [dict(r) for r in cur.fetchall()]
        csv_path = (
            r"f:\Проекты MyWave\NEW2026\Spot Map\data\imports"
            r"\SpotMap_Research_Moscow_MO_2026-11-14\NEW_missing_gps_for_manual.csv"
        )
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("legacy_row_id,raw_name,raw_address,needed\n")
            for r in miss:
                name = (r["raw_name"] or "").replace(",", " ")
                addr = (r["raw_address"] or "").replace(",", " ")
                f.write(f"{r['legacy_row_id']},{name},{addr},manual lat/lng from source\n")
        print("updated missing csv", len(miss))


if __name__ == "__main__":
    main()
