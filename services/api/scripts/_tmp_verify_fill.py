import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

d = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=30).read())
print(
    "features",
    len(d["features"]),
    "verified",
    d["meta"].get("verified_count"),
    "missing",
    d["meta"].get("staging_geo_missing"),
)
want = [
    "WakeJump",
    "Gloria",
    "Waveriders",
    "WakeDivision",
    "TeoWake",
    "SURF BROTHERS",
    "ВейкПриют",
    "OceanSpirit",
    "Local Surf",
]
feats = {f["properties"]["name"] for f in d["features"]}
for n in want:
    hit = [x for x in feats if n.lower() in x.lower()]
    print(n, "->", hit or "MISSING")

with psycopg.connect(
    "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap", row_factory=dict_row
) as conn:
    r = conn.execute(
        """
        SELECT count(*) FILTER (
          WHERE publication_status IN ('draft','pending','hidden')
            AND (approx_point IS NULL OR geo_status = 'missing')
        ) AS need
        FROM staging_candidates
        """
    ).fetchone()
    print("still_need_gps", r["need"])
