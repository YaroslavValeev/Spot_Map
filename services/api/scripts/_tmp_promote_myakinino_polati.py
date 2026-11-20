"""Promote WakeHome, Lawave, Polati, Myakinino ring with documented GPS + disciplines."""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
API = "http://127.0.0.1:18080"
TOKEN = "local-dev-only-change-me"
PROVIDER = "osint_owner_confirm_2026-11-20"
NOW = datetime.now(timezone.utc)

# Proven / documented approximate GPS (not invented tower pins).
VENUES = [
    {
        "legacy": "NEW-MYAK-RING",
        "existing_id": None,
        "name": "Вейк-парк Мякинино (Живописная бухта)",
        "region": "МО / Красногорск / Мякинино",
        "address": "МО, Красногорск, Мякининское шоссе, владение 3 (Живописная бухта)",
        "kind": "cable_installation",
        "disciplines": "CABLE_CIRCUIT;кольцевая лебёдка;WAKEBOARD_CABLE;WATER_SKI",
        "lat": 55.796481,
        "lng": 37.364141,
        "website": "https://wakeplace.ru/",
        "phone": "+79773775990",
        "telegram_url": None,
        "booking_url": "https://wakeplace.ru/",
        "evidence": (
            "Кольцевая пятиопорная лебёдка Rixen в Живописной бухте (Мякининская пойма). "
            "Адрес: Мякининское ш., вл. 3. GPS listing 55.796481,37.364141 "
            "(urbanplaces/otzywy org card; совпадает с bebeshka ~55.7966,37.3644). "
            "Источники: wakeplace.ru, wakesurf-wakeboard.ru/wake-park-myakinino. "
            "Отдельно от WakeHome (вл.1) и катерных клубов Shore House."
        ),
        "facts": {
            "booking_contact": ("yes", "wakeplace.ru / +79773775990", "https://wakeplace.ru/"),
            "riding_quality": ("yes", "кольцевая 5 опор Rixen — сайт парка", "https://wakeplace.ru/"),
            "gear_rental": ("yes", "прокат wake/лыж — сайт", "https://wakeplace.ru/"),
            "parking_access": ("yes", "Мякининское ш., зона отдыха Рублёво", "https://wakeplace.ru/"),
            "hours_freshness": ("unknown", "на сайте/карточках часы расходятся — уточнять", "https://wakeplace.ru/"),
        },
    },
    {
        "legacy": "8",
        "existing_id": "c3d40c19-5e40-4c66-a558-f647c0944f21",
        "name": "WakeHome",
        "region": "МО / Красногорск / Мякинино",
        "address": "МО, Красногорск, Мякининское шоссе, 1",
        "kind": "cable_installation",
        "disciplines": "CABLE_REVERSE;реверсивная лебёдка;WAKESURF;WAKEBOARD_BOAT",
        "lat": 55.794117,
        "lng": 37.358813,
        "website": "https://wakehome.ru/",
        "phone": "+79265872000",
        "telegram_url": None,
        "booking_url": "https://wakehome.ru/",
        "evidence": (
            "WakeHome — реверсивная лебёдка в той же акватории Мякининской поймы. "
            "Адрес: Мякининское ш., 1. GPS 55.794117,37.358813 "
            "(OSINT 2026-11-18: urbanplaces + wakehome.ru). "
            "Не путать с кольцевым парком на вл.3."
        ),
        "facts": {
            "booking_contact": ("yes", "wakehome.ru / +79265872000", "https://wakehome.ru/"),
            "riding_quality": ("yes", "реверс — подтверждение владельца + сайт", "https://wakehome.ru/"),
            "parking_access": ("yes", "Мякининское ш. 1", "https://wakehome.ru/"),
        },
    },
    {
        "legacy": "65",
        "existing_id": "e8a22424-e1a5-4075-833e-e876aec150e2",
        "name": "Lawave",
        "region": "Москва/МО — Shore House / Мякинино",
        "address": "Москва, 66-й км МКАД, Shore House (район Мякинино)",
        "kind": "spot_or_club",
        "disciplines": "WAKEBOARD_BOAT;WAKESURF;катер",
        "lat": 55.821375,
        "lng": 37.383401,
        "website": None,
        "phone": None,
        "telegram_url": None,
        "booking_url": None,
        "evidence": (
            "Lawave / Lawa wake — катерный спот в акватории Shore House (66 км МКАД). "
            "GPS каталога 55.821375,37.383401 (SpotMap 86 registry / directory_point). "
            "Владелец подтвердил катерный характер; точный причал не измерен — pin района."
        ),
        "facts": {
            "booking_contact": ("unknown", "контакты уточняются", None),
            "riding_quality": ("yes", "катерный спот — подтверждение владельца", None),
            "parking_access": ("yes", "Shore House / 66 км МКАД", None),
        },
    },
    {
        "legacy": "30",
        "existing_id": "43a10eeb-1587-4cdc-837a-cc5299937426",
        "name": "Полати Кровати",
        "region": "МО / Мытищи",
        "address": "МО, Мытищи, мкр. 17А, Большой Рупасовский пруд, Проектируемый проезд №6446",
        "kind": "cable_installation",
        "disciplines": "CABLE_CIRCUIT;CABLE_REVERSE;Кольцо / 2 реверса",
        "lat": 55.931789,
        "lng": 37.733123,
        "website": "https://polati-krovati.ru/",
        "phone": None,
        "telegram_url": "https://t.me/polati_krovati",
        "booking_url": "https://t.me/polati_krovati",
        "evidence": (
            "Полати Кровати: 1 кольцевая + 2 реверса на Большом Рупасовском пруду. "
            "GPS 55.931789,37.733123 — центр проезда №6446 из SpotMap 86 registry "
            "(street_center; не отдельные опоры). Источники: t.me/polati_krovati, "
            "polati.ru, Yandex org polati_krovati. Отдельные GPS установок — позже."
        ),
        "facts": {
            "booking_contact": ("yes", "Telegram @polati_krovati", "https://t.me/polati_krovati"),
            "riding_quality": ("yes", "кольцо + 2 реверса — registry/новости polati", "https://polati.ru/ru/news/veik-park"),
            "hours_freshness": ("unknown", "сезонность — уточнять в канале", "https://t.me/polati_krovati"),
        },
    },
]


def fingerprint(legacy: str, name: str) -> str:
    return hashlib.sha256(f"osint:{legacy}:{name}".strip().lower().encode()).hexdigest()


def promote(uuid: str, lat: float, lng: float, evidence: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": evidence[:500],
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


def upsert_staging(cur, v: dict) -> dict:
    fp = fingerprint(v["legacy"], v["name"])
    if v["existing_id"]:
        cur.execute(
            """
            UPDATE staging_candidates SET
              raw_name = %(name)s,
              raw_region = %(region)s,
              raw_address = %(address)s,
              raw_disciplines = %(disciplines)s,
              candidate_kind = %(kind)s,
              official_or_public_website = %(website)s,
              source_url = COALESCE(%(website)s, source_url),
              source_snapshot = %(evidence)s,
              geo_status = 'approximate',
              operation_status = 'unknown',
              publication_status = CASE
                WHEN publication_status IN ('merged', 'published') THEN publication_status
                ELSE 'draft'
              END,
              approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
              approx_precision = 'address',
              approx_geocode_query = %(address)s,
              approx_geocoded_at = now(),
              approx_geocode_provider = %(provider)s,
              updated_at = now()
            WHERE id = %(id)s::uuid
            RETURNING id::text, publication_status
            """,
            {
                **v,
                "id": v["existing_id"],
                "provider": PROVIDER,
                "evidence": v["evidence"][:900],
            },
        )
        row = cur.fetchone()
        if row:
            return row

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
          %(disciplines)s, %(kind)s, %(website)s, %(website)s,
          %(evidence)s, 'approximate', 'unknown', 'draft',
          ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
          'address', %(address)s, now(), %(provider)s
        )
        ON CONFLICT (fingerprint) DO UPDATE SET
          raw_name = EXCLUDED.raw_name,
          raw_address = EXCLUDED.raw_address,
          raw_disciplines = EXCLUDED.raw_disciplines,
          candidate_kind = EXCLUDED.candidate_kind,
          approx_point = EXCLUDED.approx_point,
          publication_status = CASE
            WHEN staging_candidates.publication_status IN ('published', 'merged')
              THEN staging_candidates.publication_status
            ELSE 'draft'
          END,
          updated_at = now()
        RETURNING id::text, publication_status
        """,
        {
            **v,
            "fp": fp,
            "provider": PROVIDER,
            "evidence": v["evidence"][:900],
        },
    )
    return cur.fetchone()


def find_spot_id(cur, name: str) -> str | None:
    cur.execute(
        "SELECT id::text FROM spots WHERE display_name = %s ORDER BY updated_at DESC NULLS LAST LIMIT 1",
        (name,),
    )
    row = cur.fetchone()
    return row["id"] if row else None


def upsert_profile(cur, spot_id: str, v: dict) -> None:
    cur.execute(
        """
        INSERT INTO spot_public_profiles (
          spot_id, website, phone, telegram_url, booking_url, notes_public, updated_at
        ) VALUES (
          %(id)s::uuid, %(website)s, %(phone)s, %(tg)s, %(book)s, %(notes)s, now()
        )
        ON CONFLICT (spot_id) DO UPDATE SET
          website = COALESCE(EXCLUDED.website, spot_public_profiles.website),
          phone = COALESCE(EXCLUDED.phone, spot_public_profiles.phone),
          telegram_url = COALESCE(EXCLUDED.telegram_url, spot_public_profiles.telegram_url),
          booking_url = COALESCE(EXCLUDED.booking_url, spot_public_profiles.booking_url),
          notes_public = EXCLUDED.notes_public,
          updated_at = now()
        """,
        {
            "id": spot_id,
            "website": v.get("website"),
            "phone": v.get("phone"),
            "tg": v.get("telegram_url"),
            "book": v.get("booking_url"),
            "notes": v["evidence"][:900],
        },
    )


def upsert_facts(cur, spot_id: str, facts: dict) -> None:
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
            {
                "id": spot_id,
                "key": key,
                "state": state,
                "note": note,
                "url": url,
                "obs": NOW,
            },
        )


def ensure_booking(cur, spot_id: str, url: str | None) -> None:
    if not url:
        return
    cur.execute(
        """
        INSERT INTO verified_booking_links (spot_id, target_url, label, https_only, is_active)
        VALUES (%(id)s::uuid, %(url)s, 'Записаться у клуба', true, true)
        ON CONFLICT (spot_id, target_url) DO UPDATE SET is_active = true
        """,
        {"id": spot_id, "url": url},
    )


def main() -> None:
    results = []
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            for v in VENUES:
                row = upsert_staging(cur, v)
                print("STAGING", v["name"], row)
                results.append((v, row))
        conn.commit()

    for v, row in results:
        cand_id = row["id"]
        status = row["publication_status"]
        spot_id = None
        if status == "merged":
            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    spot_id = find_spot_id(cur, v["name"])
                    if spot_id:
                        # Ensure published
                        cur.execute(
                            """
                            UPDATE spots SET publication_status='published', geo_status='verified',
                              point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                              address_text = %(address)s, updated_at=now()
                            WHERE id = %(id)s::uuid
                            """,
                            {"id": spot_id, "lat": v["lat"], "lng": v["lng"], "address": v["address"]},
                        )
                        if v["kind"] == "cable_installation":
                            cur.execute(
                                """
                                UPDATE cable_installations SET publication_status='published', geo_status='verified',
                                  point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                                  updated_at=now()
                                WHERE spot_id = %(id)s::uuid
                                """,
                                {"id": spot_id, "lat": v["lat"], "lng": v["lng"]},
                            )
                        upsert_profile(cur, spot_id, v)
                        upsert_facts(cur, spot_id, v["facts"])
                        ensure_booking(cur, spot_id, v.get("booking_url"))
                    conn.commit()
            print("MERGED_REFRESH", v["name"], spot_id)
            continue

        try:
            res = promote(cand_id, v["lat"], v["lng"], v["evidence"])
        except urllib.error.HTTPError as err:
            body = err.read().decode(errors="replace")
            print("PROMOTE_FAIL", v["name"], err.code, body[:300])
            continue
        print("PROMOTE", v["name"], res)
        spot_id = res.get("spot_id")
        if not spot_id:
            continue
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                upsert_profile(cur, spot_id, v)
                upsert_facts(cur, spot_id, v["facts"])
                ensure_booking(cur, spot_id, v.get("booking_url"))
            conn.commit()
            print("PROFILE", v["name"], spot_id)


if __name__ == "__main__":
    main()
