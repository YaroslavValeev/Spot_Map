import json
from pathlib import Path

p = Path(__file__).resolve().parents[3] / (
    "data/imports/SpotMap_Research_Moscow_MO_2026-11-14/promote_targets_approx.json"
)
d = json.loads(p.read_text(encoding="utf-8"))
print(f"# count={d['count']}")
for i in d["items"]:
    print(
        f"{i['legacy_row_id']}|{i['uuid']}|{i['lat']}|{i['lng']}|{i['raw_name']}"
    )
