"""Promote Take&Wake Konakovo with address-level GPS from public hotel listing at Krutye Berega 31."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_takewake_2026-11-20"
NOW = datetime.now(timezone.utc)

# GPS: гостиница «Вейк», ул. Крутые Берега 31 — N 56°45'56.2104" E 36°44'27.6468"
# Source: https://www.komandirovka.ru/hotels/konakovo/wake/ (same address as takewake.ru)
LAT = 56.765614
LNG = 36.741013

SPOT = {
    "legacy": "NEW-049",
    "name": "Take&Wake Konakovo",
    "region": "Тверская область / Конаково",
    "address": "Тверская обл., Конаково, ул. Крутые Берега, 31",
    "disciplines": "WAKESURF;WAKEBOARD;катер;реверс",
    "website": "http://takewake.ru/",
    "phone": "+79051282284",
    "booking_url": "http://takewake.ru/",
    "note": (
        "Take&Wake Konakovo на территории Конаково Ривер Клаб. "
        "GPS по адресу Крутые Берега 31 (публичный listing гостиницы Вейк). "
        "Контакты: takewake.ru, +7 905 128-22-84. "
        "Wake Weekend — историческое событие на споте, не клуб."
    ),
}


def fingerprint(legacy: str, name: str) -> str:
    return hashlib.sha256(f"osint:{legacy}:{name}".strip().lower().encode()).hexdigest()


def promote(uuid: str) -> dict:
    body = json.dumps(
        {
            "latitude": LAT,
            "longitude": LNG,
            "evidence_note": SPOT["note"][:500],
            "publish": True,
        }
    ).encode()
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
        return json.loads(resp.read().decode())


def upsert_profile(cur, spot_id: str) -> None:
    cur.execute(
        """
        INSERT INTO spot_public_profiles (
          spot_id, website, phone, whatsapp_url, booking_url, notes_public, updated_at
        ) VALUES (
          %(id)s::uuid, %(website)s, %(phone)s, %(wa)s, %(book)s, %(notes)s, now()
        )
        ON CONFLICT (spot_id) DO UPDATE SET
          website = EXCLUDED.website,
          phone = EXCLUDED.phone,
          whatsapp_url = EXCLUDED.whatsapp_url,
          booking_url = EXCLUDED.booking_url,
          notes_public = EXCLUDED.notes_public,
          updated_at = now()
        """,
        {
            "id": spot_id,
            "website": SPOT["website"],
            "phone": SPOT["phone"],
            "wa": "https://wa.me/79051282284",
            "book": SPOT["booking_url"],
            "notes": SPOT["note"][:900],
        },
    )


def upsert_facts(cur, spot_id: str) -> None:
    facts = {
        "booking_contact": ("yes", "takewake.ru / +79051282284", "http://takewake.ru/"),
        "pricing_clarity": ("yes", "сеты в Яндекс.Картах / каталогах", "https://yandex.ru/maps/org/take_wake_konakovo/110769591192/"),
        "riding_quality": ("yes", "Nautique G23/G25 + реверс — сайт", "http://takewake.ru/"),
        "gear_rental": ("yes", "экипировка на споте — VK/сайт", "https://vk.com/takewakekonakovo"),
        "coaching_available": ("unknown", "уточнять при записи", None),
        "changing_facilities": ("yes", "сёрф-отель на споте — сайт", "http://takewake.ru/"),
        "guest_comfort": ("yes", "отель / спортплощадка", "http://takewake.ru/"),
        "hours_freshness": ("yes", "в источниках ~10:00–20:00 / по записи", "https://wakepulse.biz/wakepark?id=59"),
        "parking_access": ("yes", "Конаково Ривер Клаб", "http://takewake.ru/"),
        "safety_basics": ("unknown", "уточнять на площадке", None),
    }
    for key, (state, note, url) in facts.items():
        cur.execute(
            """
            INSERT INTO spot_convenience_facts (
              spot_id, checklist_key, state, evidence_note, source_url, observed_at, updated_at
            ) VALUES (%(id)s::uuid, %(key)s, %(state)s, %(note)s, %(url)s, %(obs)s, now())
            ON CONFLICT (spot_id, checklist_key) DO UPDATE SET
              state = EXCLUDED.state,
              evidence_note = EXCLUDED.evidence_note,
              source_url = EXCLUDED.source_url,
              observed_at = EXCLUDED.observed_at,
              updated_at = now()
            """,
            {"id": spot_id, "key": key, "state": state, "note": note, "url": url, "obs": NOW},
        )


def main() -> None:
    fp = fingerprint(SPOT["legacy"], SPOT["name"])
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
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
                  approx_point = EXCLUDED.approx_point,
                  publication_status = CASE
                    WHEN staging_candidates.publication_status IN ('published','merged')
                      THEN staging_candidates.publication_status
                    ELSE 'draft'
                  END,
                  updated_at = now()
                RETURNING id::text, publication_status
                """,
                {
                    "legacy": SPOT["legacy"],
                    "fp": fp,
                    "name": SPOT["name"],
                    "region": SPOT["region"],
                    "address": SPOT["address"],
                    "disciplines": SPOT["disciplines"],
                    "website": SPOT["website"],
                    "note": SPOT["note"][:900],
                    "lat": LAT,
                    "lng": LNG,
                    "query": SPOT["address"],
                    "provider": PROVIDER,
                },
            )
            row = cur.fetchone()
        conn.commit()

    print("STAGING", row)
    if row["publication_status"] == "merged":
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id::text FROM spots WHERE display_name = %s LIMIT 1",
                    (SPOT["name"],),
                )
                s = cur.fetchone()
                if s:
                    upsert_profile(cur, s["id"])
                    upsert_facts(cur, s["id"])
                    conn.commit()
                    print("UPDATED", s["id"])
        return

    res = promote(row["id"])
    print("PROMOTE", res)
    sid = res.get("spot_id")
    if sid:
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                upsert_profile(cur, sid)
                upsert_facts(cur, sid)
            conn.commit()
            print("PROFILE", sid)


if __name__ == "__main__":
    main()
