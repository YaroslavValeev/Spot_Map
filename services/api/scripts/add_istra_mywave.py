"""Add/fix IstraWake (Istra) + MyWave Wake (Ozerninskoye) and publish to map."""
from __future__ import annotations

import hashlib
import json
import urllib.request

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_source_gps_2026-11-18"

ISTRA = {
    "legacy": "67",
    "name": "IstraWake",
    "region": "МО / Истринское вдхр.",
    "address": "МО, Солнечногорский р-н, д. Лопотово, загородный клуб «Романтик» (Истринское вдхр.)",
    "disciplines": "WAKEBOARD_BOAT;WAKESURF",
    "lat": 56.044619,
    "lng": 36.841933,
    "query": "IstraWake @ ЗК Романтик, Лопотово",
    "note": (
        "source_gps:sssromantik.ru contacts 56.044619,36.841933; "
        "istrawake.ru — клуб на территории ЗК Романтик, Истринское вдхр.; "
        "exa IstraWake ~56.04467,36.848403; phone +74951666606"
    ),
    "website": "http://istrawake.ru/",
}

MYWAVE = {
    "legacy": "NEW-040",
    "name": "MyWave Wake",
    "region": "МО / Озернинское вдхр. / Руза",
    "address": "МО, Рузский округ, д. Нововолково, берег Озернинского вдхр. (ориентир остановка «Родник» / зона ICE Пляж)",
    "disciplines": "WAKESURF;WAKEBOARD_BOAT",
    "lat": 55.758853,
    "lng": 36.260719,
    "query": "MyWave Wake @ Озернинское / ICE Пляж / Родник",
    "note": (
        "source_gps:katalogturbaz ICE Пляж 55.758853,36.260719 (Нововолково, Озернинское); "
        "Yandex org MyWave 90003306477 — Рузский округ, ~400м от остановки Родник; "
        "reviews: пирс/шатёр у пляжа; mywavewake.ru; +79957883344 / +79160117179; "
        "NOT SkyWake cable (same shore zone, separate operator)"
    ),
    "website": "https://mywavewake.ru/",
}


def fingerprint(legacy: str, name: str) -> str:
    raw = f"osint:{legacy}:{name}".strip().lower().encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def upsert_point(cur, *, legacy: str, lat: float, lng: float, query: str, note: str, address: str, disciplines: str) -> None:
    cur.execute(
        """
        UPDATE staging_candidates
        SET approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
            approx_precision = 'address',
            approx_geocode_query = %(query)s,
            approx_geocoded_at = now(),
            approx_geocode_provider = %(provider)s,
            geo_status = 'approximate',
            raw_address = %(address)s,
            raw_region = COALESCE(%(region)s, raw_region),
            raw_disciplines = %(disciplines)s,
            raw_name = COALESCE(%(name)s, raw_name),
            source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
            publication_status = CASE
              WHEN publication_status IN ('hidden','merged','published') THEN publication_status
              ELSE 'draft'
            END,
            updated_at = now()
        WHERE legacy_row_id = %(legacy)s
          AND publication_status NOT IN ('published', 'merged')
        RETURNING id::text, legacy_row_id, raw_name
        """,
        {
            "legacy": legacy,
            "lat": lat,
            "lng": lng,
            "query": query[:500],
            "provider": PROVIDER,
            "address": address,
            "region": None,
            "disciplines": disciplines,
            "name": None,
            "note": note[:900],
        },
    )


def insert_mywave(cur) -> str:
    fp = fingerprint(MYWAVE["legacy"], MYWAVE["name"])
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
        RETURNING id::text
        """,
        {
            "legacy": MYWAVE["legacy"],
            "fp": fp,
            "name": MYWAVE["name"],
            "region": MYWAVE["region"],
            "address": MYWAVE["address"],
            "disciplines": MYWAVE["disciplines"],
            "website": MYWAVE["website"],
            "note": MYWAVE["note"][:900],
            "lat": MYWAVE["lat"],
            "lng": MYWAVE["lng"],
            "query": MYWAVE["query"][:500],
            "provider": PROVIDER,
        },
    )
    return cur.fetchone()["id"]


def promote(uuid: str, lat: float, lng: float, evidence: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": evidence[:500],
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()

        # Fix IstraWake
        cur.execute(
            """
            UPDATE staging_candidates
            SET raw_name = %(name)s,
                raw_region = %(region)s,
                raw_address = %(address)s,
                raw_disciplines = %(disciplines)s,
                official_or_public_website = %(website)s,
                source_url = %(website)s,
                approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                approx_precision = 'address',
                approx_geocode_query = %(query)s,
                approx_geocoded_at = now(),
                approx_geocode_provider = %(provider)s,
                geo_status = 'approximate',
                publication_status = 'draft',
                source_snapshot = left(coalesce(source_snapshot,'') || E'\\n' || %(note)s, 2000),
                updated_at = now()
            WHERE legacy_row_id = '67'
            RETURNING id::text, legacy_row_id, raw_name, raw_address,
                      ST_Y(approx_point::geometry) AS lat, ST_X(approx_point::geometry) AS lng
            """,
            {
                "name": ISTRA["name"],
                "region": ISTRA["region"],
                "address": ISTRA["address"],
                "disciplines": ISTRA["disciplines"],
                "website": ISTRA["website"],
                "lat": ISTRA["lat"],
                "lng": ISTRA["lng"],
                "query": ISTRA["query"],
                "provider": PROVIDER,
                "note": ISTRA["note"],
            },
        )
        istra_rows = cur.fetchall()
        print("ISTRA", istra_rows)
        istra_id = istra_rows[0]["id"] if istra_rows else None

        mywave_id = insert_mywave(cur)
        print("MYWAVE", mywave_id)
        conn.commit()

    # Publish both so they appear without staging checkbox
    if istra_id:
        print("PROMOTE_ISTRA", promote(istra_id, ISTRA["lat"], ISTRA["lng"], ISTRA["note"][:200]))
    print("PROMOTE_MYWAVE", promote(mywave_id, MYWAVE["lat"], MYWAVE["lng"], MYWAVE["note"][:200]))


if __name__ == "__main__":
    main()
