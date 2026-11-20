"""Add WakeDivision Zavidovo, SecretSpot, Riversurf Zavidovo, Aquatoria Leta."""
from __future__ import annotations

import hashlib
import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_zavidovo_2026-11-18"

SPOTS = [
    {
        "legacy": "NEW-041",
        "name": "WakeDivision Завидово",
        "region": "Тверская обл. / Завидово",
        "address": "Тверская обл., Конаковский округ, д. Городище, Майская ул., 2",
        "disciplines": "WAKESURF;WAKEBOARD_BOAT",
        "lat": 56.6094,
        "lng": 36.5756,
        "website": "https://wakedivision.ru/opa-wake-zavidovo",
        "query": "WakeDivision Завидово Городище",
        "note": (
            "bebeshka 56.6094,36.5756; 2GIS Городище Майская 2; "
            "+79037269691; отдельная площадка от WakeDivision СберСити"
        ),
    },
    {
        "legacy": "NEW-042",
        "name": "SecretSpot Russia (WakeDivision)",
        "region": "Тверская обл. / Иваньковское вдхр.",
        "address": "Тверская обл., Конаковский р-н, д. Фёдоровское, ул. Ивановская, 33",
        "disciplines": "WAKESURF;WAKEBOARD_BOAT;WAKEBOARD_CABLE",
        "lat": 56.748505,
        "lng": 36.959637,
        "website": "https://www.secretspotwake.ru/",
        "query": "SecretSpot WakeDivision Фёдоровское",
        "note": (
            "secretspotwake.ru; exa 56.748505,36.959637; Yandex org 193322817190; "
            "+79157371195 / +79261530052; катера + реверс; ≠ WakeDivision Завидово/СберСити"
        ),
    },
    {
        "legacy": "NEW-043",
        "name": "Riversurf Завидово",
        "region": "Тверская обл. / Завидово",
        "address": "Тверская обл., Конаковский округ, КП «Московское Море-2» / Лазурная",
        "disciplines": "WAKESURF;WAKEBOARD_BOAT",
        "lat": 56.587578,
        "lng": 36.454014,
        "website": "https://riversurf.ru/",
        "query": "Riversurf Zavidovo Московское Море-2",
        "note": (
            "riversurf.ru — спот Завидово КП Московское Море-2; exa 56.587578,36.454014; "
            "prowakesurf Riversurf Zavidovo; отдельный venue от бренда Riversurf Москва"
        ),
    },
    {
        "legacy": "NEW-044",
        "name": "Акватория Лета Завидово",
        "region": "Тверская обл. / Завидово",
        "address": "Тверская обл., д. Вараксино, 117 км Ленинградского ш. / Живописная ул.",
        "disciplines": "WAKEBOARD_CABLE;WAKESURF;WAKEBOARD_BOAT",
        "lat": 56.597751,
        "lng": 36.512313,
        "website": "https://aqualeto-zavidovo.com/",
        "query": "Акватория Лета Завидово Wake Park Вараксино",
        "note": (
            "aqualeto-zavidovo.com; Zavidovo Wake Park exa 56.597751,36.512313; "
            "bebeshka 56.598,36.5159; 2 реверса + кольцо; +74957640290"
        ),
    },
]


def fingerprint(legacy: str, name: str) -> str:
    raw = f"osint:{legacy}:{name}".strip().lower().encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def upsert(cur, spot: dict) -> str:
    fp = fingerprint(spot["legacy"], spot["name"])
    cur.execute(
        """
        INSERT INTO staging_candidates (
          legacy_row_id, fingerprint, raw_name, raw_region, raw_address,
          raw_disciplines, candidate_kind, official_or_public_website, source_url,
          source_snapshot, geo_status, operation_status, publication_status,
          approx_point, approx_precision, approx_geocode_query, approx_geocoded_at,
          approx_geocode_provider
        ) VALUES (
          %(legacy)s, %(fp)s, %(name)s, %(region)s, %(address)s,
          %(disciplines)s, 'spot_or_club', %(website)s, %(website)s,
          %(note)s, 'approximate', 'unknown', 'draft',
          ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
          'address', %(query)s, now(), %(provider)s
        )
        ON CONFLICT (fingerprint) DO UPDATE SET
          raw_name = EXCLUDED.raw_name,
          raw_address = EXCLUDED.raw_address,
          raw_region = EXCLUDED.raw_region,
          raw_disciplines = EXCLUDED.raw_disciplines,
          approx_point = EXCLUDED.approx_point,
          approx_precision = EXCLUDED.approx_precision,
          approx_geocode_query = EXCLUDED.approx_geocode_query,
          approx_geocoded_at = now(),
          approx_geocode_provider = EXCLUDED.approx_geocode_provider,
          geo_status = 'approximate',
          publication_status = CASE
            WHEN staging_candidates.publication_status IN ('published','merged')
              THEN staging_candidates.publication_status
            ELSE 'draft'
          END,
          source_snapshot = left(coalesce(staging_candidates.source_snapshot,'') || E'\\n' || EXCLUDED.source_snapshot, 2000),
          updated_at = now()
        RETURNING id::text, publication_status
        """,
        {
            "legacy": spot["legacy"],
            "fp": fp,
            "name": spot["name"],
            "region": spot["region"],
            "address": spot["address"],
            "disciplines": spot["disciplines"],
            "website": spot["website"],
            "note": spot["note"][:900],
            "lat": spot["lat"],
            "lng": spot["lng"],
            "query": spot["query"][:500],
            "provider": PROVIDER,
        },
    )
    row = cur.fetchone()
    return row["id"], row["publication_status"]


def promote(uuid: str, lat: float, lng: float, note: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": note[:500],
            "publish": True,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/v1/moderation/candidates/{uuid}/promote-geo",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-SpotMap-Moderation-Token": TOKEN,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    ids: list[tuple[dict, str]] = []
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        for spot in SPOTS:
            cid, status = upsert(cur, spot)
            print("UPSERT", spot["legacy"], spot["name"], cid, status)
            ids.append((spot, cid))
        conn.commit()

    for spot, cid in ids:
        # If already merged, find by name on spots or re-promote only if draft
        res = promote(cid, spot["lat"], spot["lng"], spot["note"])
        print("PROMOTE", spot["name"], res.get("map_visible"), res.get("spot_id") or res)


if __name__ == "__main__":
    main()
