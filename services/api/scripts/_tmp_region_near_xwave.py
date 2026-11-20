"""List map/DB spots near XWAVE/Reef (Dolgoprudny–Gribki corridor)."""
import json
import math
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
# Center between XWAVE and Reef
CX, CY = 37.538, 55.970
# ~12 km box
RADIUS_KM = 12.0


def dist_km(lat1, lng1, lat2, lng2):
    # rough equirectangular at ~56N
    dy = (lat1 - lat2) * 111.32
    dx = (lng1 - lng2) * 62.5
    return math.hypot(dx, dy)


data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points?include_staging=true", timeout=30).read())
rows = []
for f in data["features"]:
    lng, lat = f["geometry"]["coordinates"]
    d = dist_km(lat, lng, CY, CX)
    if d <= RADIUS_KM:
        p = f["properties"]
        rows.append((d, p.get("name"), p.get("pin_kind"), p.get("primary_discipline"), lat, lng, p.get("id")))

rows.sort()
print(f"MAP within {RADIUS_KM} km of Dolgoprudny/Gribki ({CY},{CX}): {len(rows)}")
for d, name, kind, disc, lat, lng, _id in rows:
    print(f"  {d:5.1f} km | {kind:<22} | {name} | {lat:.5f},{lng:.5f} | {disc or '-'}")

# Also staging missing geo in related names/regions
with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_address, raw_region, geo_status, publication_status,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
        FROM staging_candidates
        WHERE raw_address ILIKE '%долгопруд%'
           OR raw_address ILIKE '%грибк%'
           OR raw_address ILIKE '%хлебников%'
           OR raw_region ILIKE '%долгопруд%'
           OR raw_name ILIKE '%xwave%'
           OR raw_name ILIKE '%reef%'
           OR raw_name ILIKE '%мегаспорт%'
           OR raw_name ILIKE '%wakestar%'
        ORDER BY raw_name
        """
    )
    print("\nSTAGING name/address hits:")
    for r in cur.fetchall():
        print(
            f"  {r['legacy_row_id']}|{r['publication_status']}|{r['geo_status']}|"
            f"{r['raw_name']}|{r['raw_address']}|{r['lat']},{r['lng']}"
        )
