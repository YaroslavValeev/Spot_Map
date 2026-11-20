"""Verify published Myakinino/WakeHome/Lawave/Polati + map discipline filter."""
from __future__ import annotations

import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

from app.disciplines import enrich_row_disciplines

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"


def main() -> None:
    needles = ["%мякинино%", "%wakehome%", "%lawave%", "%полати%"]
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.display_name, s.publication_status, s.geo_status,
                       ST_Y(s.point::geometry) AS lat, ST_X(s.point::geometry) AS lng,
                       (
                         SELECT sc.raw_disciplines
                         FROM staging_candidates sc
                         WHERE sc.publication_status = 'merged'
                           AND lower(trim(sc.raw_name)) = lower(trim(s.display_name))
                         ORDER BY sc.updated_at DESC NULLS LAST
                         LIMIT 1
                       ) AS raw_disc,
                       EXISTS (
                         SELECT 1 FROM cable_installations c
                         WHERE c.spot_id = s.id AND c.publication_status = 'published'
                       ) AS has_cable
                FROM spots s
                WHERE s.display_name ILIKE ANY(%s)
                ORDER BY s.display_name
                """,
                (needles,),
            )
            print("=== DB ===")
            for r in cur.fetchall():
                et = "cable_installation" if r["has_cable"] else "spot"
                row = enrich_row_disciplines(
                    {
                        "name": r["display_name"],
                        "raw_disciplines": r["raw_disc"],
                        "entity_type": et,
                        "raw_address": None,
                    }
                )
                print(
                    r["display_name"],
                    r["publication_status"],
                    round(r["lat"], 6),
                    round(r["lng"], 6),
                    "cable=" + str(r["has_cable"]),
                    "tags=" + ",".join(row["disciplines"]),
                    "raw=" + str(r["raw_disc"]),
                )

    for disc in ("cable_ring", "cable_reverse", "wakeboard"):
        url = f"{API}/v1/map/points?discipline={disc}&limit=200"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        names = [f["properties"]["name"] for f in data.get("features", [])]
        hits = [
            n
            for n in names
            if any(x in n.lower() for x in ("мякинино", "wakehome", "lawave", "полати", "живописн"))
        ]
        print(f"=== MAP {disc} count={len(names)} hits={hits} ===")


if __name__ == "__main__":
    main()
