import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NEEDLES = (
    "zavidovo",
    "завидов",
    "secret",
    "секрет",
    "aquatoria",
    "акватори",
    "лета",
    "river surf",
    "riversurf",
    "wakedivision",
    "wake division",
)

with psycopg.connect(DSN, row_factory=dict_row) as conn:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT legacy_row_id, raw_name, raw_region, raw_address, geo_status,
               publication_status, official_or_public_website, public_telegram_url,
               ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng,
               id::text
        FROM staging_candidates
        ORDER BY legacy_row_id NULLS LAST, raw_name
        """
    )
    print("=== STAGING ===")
    for r in cur.fetchall():
        blob = " ".join(
            str(r.get(k) or "")
            for k in ("raw_name", "raw_region", "raw_address", "official_or_public_website")
        ).lower()
        if any(n in blob for n in NEEDLES):
            print(
                f"{r['legacy_row_id']}|{r['publication_status']}|{r['geo_status']}|"
                f"{r['lat']},{r['lng']}|{r['raw_name']}|{r['raw_address']}|{r['id']}"
            )

    cur.execute(
        """
        SELECT id::text, display_name, publication_status, geo_status,
               ST_Y(point::geometry) AS lat, ST_X(point::geometry) AS lng
        FROM spots
        ORDER BY display_name
        """
    )
    print("=== SPOTS ===")
    for r in cur.fetchall():
        blob = (r["display_name"] or "").lower()
        if any(n in blob for n in NEEDLES):
            print(r)

data = json.loads(urllib.request.urlopen("http://127.0.0.1:18080/v1/map/points", timeout=30).read())
print("=== MAP ===")
for f in data["features"]:
    n = (f["properties"].get("name") or "").lower()
    if any(x in n for x in NEEDLES):
        print(f["properties"]["name"], f["geometry"]["coordinates"], f["properties"].get("pin_kind"))
