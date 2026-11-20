import json
import urllib.request

BASE = "http://127.0.0.1:18080"
paths = [
    "/v1/map",
    "/v1/map/pins",
    "/v1/map/features",
    "/health",
    "/docs",
]
for p in paths:
    try:
        r = urllib.request.urlopen(BASE + p, timeout=10)
        print(p, r.status, r.headers.get("content-type"))
        body = r.read()[:200]
        print(" ", body[:120])
    except Exception as e:
        print(p, type(e).__name__, e)


def search(url: str) -> None:
    data = json.loads(urllib.request.urlopen(url, timeout=15).read())
    feats = data.get("features") or data.get("items") or data.get("pins") or data
    if isinstance(feats, dict):
        feats = feats.get("features", [])
    hits = []
    for f in feats:
        p = f.get("properties", f) if isinstance(f, dict) else {}
        n = str(p.get("name") or p.get("title") or "")
        if "istra" in n.lower() or "mywave" in n.lower():
            hits.append((n, p.get("lat") or p.get("latitude"), p.get("lng") or p.get("longitude")))
    print("url", url, "total", len(feats), "hits", hits)


# try common query variants after discovering working path
