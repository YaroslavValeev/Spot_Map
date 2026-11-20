"""Dump map feature disciplines for promoted venues."""
from __future__ import annotations

import json
import urllib.request

API = "http://127.0.0.1:18080"
with urllib.request.urlopen(f"{API}/v1/map/points?limit=300", timeout=30) as resp:
    data = json.loads(resp.read().decode())
for f in data.get("features", []):
    n = f["properties"]["name"]
    if any(x in n.lower() for x in ("мякинино", "wakehome", "lawave", "полати", "живописн")):
        print(n, f["properties"].get("disciplines"), f["properties"].get("entity_type"))
print("meta_counts", data.get("meta", {}).get("discipline_counts"))
