"""Quick Yandex geocode for Myakinino shosse 3 (local .env key)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

env = Path(__file__).resolve().parents[1] / ".env"
key = ""
for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
    if line.startswith("YANDEX_MAPS_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
print("KEY_LEN", len(key))
if not key:
    raise SystemExit(1)
q = "Московская область, Красногорск, Мякининское шоссе, 3"
url = "https://geocode-maps.yandex.ru/1.x/?" + urllib.parse.urlencode(
    {"apikey": key, "geocode": q, "format": "json", "results": 5}
)
with urllib.request.urlopen(url, timeout=30) as resp:
    data = json.loads(resp.read().decode())
for m in data["response"]["GeoObjectCollection"]["featureMember"]:
    g = m["GeoObject"]
    print(g["Point"]["pos"], g.get("name"), "|", (g.get("description") or "")[:90])
