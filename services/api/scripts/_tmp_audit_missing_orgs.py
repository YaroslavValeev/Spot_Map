import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NEEDLES = (
    "wakesummer",
    "wakeweekend",
    "wake weekend",
    "prowakesurf",
    "лыжеборд",
    "skiboard",
    "sokolniki",
    "остров мечты",
    "dream island",
    "flowmoscow",
    "flow moscow",
    "freezone",
    "free zone",
    "фвлс",
    "fvls",
    "борисов",
)

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_address, geo_status, publication_status,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng,
               id::text
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
        SELECT id::text, display_name, publication_status, geo_status, operation_status,
               ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
        FROM spots ORDER BY display_name
        """
    )
    print("=== SPOTS ===")
    for r in cur.fetchall():
        blob = (r["display_name"] or "").lower()
        if any(n in blob for n in NEEDLES):
            print(r)

data = json.loads(
    urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points?include_staging=false", timeout=30).read()
)
print("=== MAP verified", len(data["features"]), "===")
for f in data["features"]:
    n = (f["properties"].get("name") or "").lower()
    if any(x in n for x in NEEDLES):
        print(f["properties"]["name"], f["geometry"]["coordinates"], f["properties"].get("pin_kind"))
