"""Audit likely duplicate spots on the public map."""
from __future__ import annotations

import json
from collections import defaultdict

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id::text, display_name, address_text, locality,
                   geo_status, publication_status, operation_status,
                   ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
            FROM spots
            WHERE publication_status = 'published'
            ORDER BY display_name
            """
        )
        spots = cur.fetchall()
        print("PUBLISHED_SPOTS", len(spots))

        # Exact name duplicates
        by_name: dict[str, list] = defaultdict(list)
        for s in spots:
            key = (s["display_name"] or "").strip().lower()
            by_name[key].append(s)
        print("\n=== EXACT NAME DUPES ===")
        for k, rows in sorted(by_name.items()):
            if len(rows) > 1:
                print(f"{len(rows)}x {rows[0]['display_name']}")
                for r in rows:
                    print(f"  {r['id'][:8]} {r['geo_status']} {r['lat']},{r['lng']} | {r['address_text']}")

        # Near duplicates < 150m
        print("\n=== NEAR DUPES <150m ===")
        cur.execute(
            """
            SELECT a.id::text AS id_a, a.display_name AS name_a,
                   b.id::text AS id_b, b.display_name AS name_b,
                   ST_Distance(a.point, b.point) AS dist_m,
                   ST_Y(a.point::geometry) AS lat_a, ST_X(a.point::geometry) AS lng_a,
                   ST_Y(b.point::geometry) AS lat_b, ST_X(b.point::geometry) AS lng_b
            FROM spots a
            JOIN spots b ON a.id < b.id
            WHERE a.publication_status = 'published'
              AND b.publication_status = 'published'
              AND ST_DWithin(a.point, b.point, 150)
            ORDER BY dist_m
            """
        )
        near = cur.fetchall()
        print("pairs", len(near))
        for r in near:
            print(
                f"{int(r['dist_m'])}m | {r['name_a']} <-> {r['name_b']} | "
                f"{r['lat_a']:.5f},{r['lng_a']:.5f} vs {r['lat_b']:.5f},{r['lng_b']:.5f}"
            )

        # Near <500m with similar names (token overlap)
        print("\n=== NEAR <800m NAME-ISH ===")
        cur.execute(
            """
            SELECT a.id::text AS id_a, a.display_name AS name_a,
                   b.id::text AS id_b, b.display_name AS name_b,
                   ST_Distance(a.point, b.point) AS dist_m
            FROM spots a
            JOIN spots b ON a.id < b.id
            WHERE a.publication_status = 'published'
              AND b.publication_status = 'published'
              AND ST_DWithin(a.point, b.point, 800)
            ORDER BY dist_m
            """
        )
        for r in cur.fetchall():
            na = (r["name_a"] or "").lower()
            nb = (r["name_b"] or "").lower()
            tokens_a = {t for t in na.replace("«", " ").replace("»", " ").replace("-", " ").split() if len(t) > 3}
            tokens_b = {t for t in nb.replace("«", " ").replace("»", " ").replace("-", " ").split() if len(t) > 3}
            overlap = tokens_a & tokens_b
            if overlap or int(r["dist_m"]) < 80:
                print(f"{int(r['dist_m'])}m overlap={sorted(overlap)} | {r['name_a']} <-> {r['name_b']}")

        # Staging merged from NEW that might duplicate older SM published
        print("\n=== STAGING MERGED NEW vs SM-like names on map ===")
        cur.execute(
            """
            SELECT legacy_row_id, raw_name, publication_status, geo_status,
                   left(coalesce(source_snapshot,''), 120) AS snap
            FROM staging_candidates
            WHERE publication_status = 'merged'
              AND legacy_row_id LIKE 'NEW-%%'
            ORDER BY legacy_row_id
            """
        )
        merged = cur.fetchall()
        print("merged_new", len(merged))

        # Known risk pairs
        keys = ["go wake", "local surf", "orlov", "dolwake", "wave motion", "jolie", "strogino", "sigma"]
        print("\n=== RISK NAME SEARCH ON SPOTS ===")
        for k in keys:
            hits = [s for s in spots if k in (s["display_name"] or "").lower()]
            if hits:
                print(f"-- {k} ({len(hits)})")
                for s in hits:
                    print(f"  {s['display_name']} | {s['lat']},{s['lng']} | {s['address_text']}")


if __name__ == "__main__":
    main()
