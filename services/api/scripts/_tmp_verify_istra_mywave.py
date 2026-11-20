import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.id::text, s.display_name, s.publication_status, s.geo_status,
               ST_Y(s.point::geometry) AS lat, ST_X(s.point::geometry) AS lng
        FROM spots s
        WHERE s.display_name ILIKE '%istra%' OR s.display_name ILIKE '%mywave%'
        """
    )
    print("SPOTS", cur.fetchall())
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, publication_status, geo_status,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
        FROM staging_candidates
        WHERE legacy_row_id IN ('67','NEW-040')
        """
    )
    print("STAGING", cur.fetchall())
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'spot_disciplines' ORDER BY ordinal_position
        """
    )
    print("SD_COLS", [r["column_name"] for r in cur.fetchall()])
    cur.execute(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name ILIKE '%disc%'
        """
    )
    print("DISC_TABLES", cur.fetchall())

data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=20).read())
print("top_keys", list(data.keys()))
feats = data.get("features") or []
print("features", len(feats))
hits = []
for f in feats:
    p = f.get("properties", {})
    n = str(p.get("name") or "")
    if "istra" in n.lower() or "mywave" in n.lower():
        hits.append({"name": n, "props": p, "geom": f.get("geometry")})
print("hits", hits)
# also scan by coords
for label, lat0, lng0 in [("istra", 56.044619, 36.841933), ("mywave", 55.758853, 36.260719)]:
    found = []
    for f in feats:
        coords = (f.get("geometry") or {}).get("coordinates") or [None, None]
        lng, lat = coords[0], coords[1]
        if lat is None:
            continue
        if abs(lat - lat0) < 0.02 and abs(lng - lng0) < 0.02:
            found.append(f.get("properties", {}).get("name"))
    print(label, "near_names", found)
