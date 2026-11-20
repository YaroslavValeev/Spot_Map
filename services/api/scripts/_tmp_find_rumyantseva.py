import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NEEDLES = ("румянц", "rumyant", "воднолыжн")

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id::text, legacy_row_id, raw_name, raw_address, geo_status,
               publication_status, operation_status,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
        FROM staging_candidates
        WHERE raw_name ILIKE '%румянц%' OR raw_name ILIKE '%rumyant%'
           OR raw_name ILIKE '%воднолыж%'
        """
    )
    print("STAGING", cur.fetchall())
    cur.execute(
        """
        SELECT id::text, display_name, publication_status, operation_status, geo_status,
               ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
        FROM spots
        WHERE display_name ILIKE '%румянц%' OR display_name ILIKE '%rumyant%'
           OR display_name ILIKE '%воднолыж%'
        """
    )
    print("SPOTS", cur.fetchall())
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name='spots' ORDER BY ordinal_position
        """
    )
    print("SPOT_COLS", [r["column_name"] for r in cur.fetchall()])

data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=30).read())
for f in data["features"]:
    n = f["properties"].get("name") or ""
    if any(x in n.lower() for x in ("румянц", "rumyant", "воднолыж")):
        print("MAP", n, f["properties"], f["geometry"]["coordinates"])
