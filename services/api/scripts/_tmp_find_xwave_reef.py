import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NEEDLES = ("xwave", "xewave", "xe wave", "reef", "риф")

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_address, geo_status, publication_status,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng,
               id::text, left(coalesce(source_snapshot,''), 200) AS snap
        FROM staging_candidates
        ORDER BY raw_name
        """
    )
    print("=== STAGING ===")
    for r in cur.fetchall():
        blob = f"{r['raw_name']} {r['raw_address']}".lower()
        if any(n in blob for n in NEEDLES):
            print(r)

    cur.execute(
        """
        SELECT id::text, display_name, publication_status, geo_status,
               ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
        FROM spots ORDER BY display_name
        """
    )
    print("=== SPOTS ===")
    for r in cur.fetchall():
        if any(n in (r["display_name"] or "").lower() for n in NEEDLES):
            print(r)

data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=30).read())
print("=== MAP ===")
for f in data["features"]:
    n = (f["properties"].get("name") or "").lower()
    if any(x in n for n_ in NEEDLES for x in [n_]):
        print(f["properties"]["name"], f["geometry"]["coordinates"], f["properties"].get("pin_kind"))
# also fuzzy
for f in data["features"]:
    n = f["properties"].get("name") or ""
    if "wave" in n.lower() or "reef" in n.lower() or "риф" in n.lower():
        print("waveish:", n, f["geometry"]["coordinates"])
