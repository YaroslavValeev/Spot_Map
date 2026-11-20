"""Hide WakeWeekend (not a club); find/add Take&Wake Konakovo with proven public data."""
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

# Yandex org / 2GIS / takewake.ru: Конаково, Крутые Берега 31
# Geocode via Nominatim for building-level coords
TAKEWAKE = {
    "legacy": "NEW-049",
    "name": "Take&Wake Konakovo",
    "region": "Тверская область / Конаково",
    "address": "Тверская обл., Конаково, ул. Крутые Берега, 31 (Конаково Ривер Клаб)",
    "disciplines": "WAKESURF;WAKEBOARD;катер;реверс",
    "website": "http://takewake.ru/",
    "phone": "+79051282284",
    "booking_url": "http://takewake.ru/",
    "note": (
        "Take&Wake Konakovo — сёрф/вейк за катером Nautique + реверс на территории "
        "Конаково Ривер Клаб. Контакты takewake.ru / +7 905 128-22-84. "
        "Wake Weekend — историческое событие на споте, не отдельный клуб."
    ),
}


def fingerprint(legacy: str, name: str) -> str:
    return hashlib.sha256(f"osint:{legacy}:{name}".strip().lower().encode()).hexdigest()


def nominatim(query: str) -> tuple[float, float] | None:
    url = (
        "https://nominatim.openstreetmap.org/search?"
        + urllib.parse.urlencode({"q": query, "format": "json", "limit": 3})
    )
    req = urllib.request.Request(url, headers={"User-Agent": "SpotMap/1.0 (local-dev)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def promote(uuid: str, lat: float, lng: float, note: str) -> dict:
    body = json.dumps(
        {
            "latitude": lat,
            "longitude": lng,
            "evidence_note": note[:500],
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


def upsert_profile(cur, spot_id: str, p: dict) -> None:
    cur.execute(
        """
        INSERT INTO spot_public_profiles (
          spot_id, website, phone, telegram_url, whatsapp_url, booking_url, notes_public, updated_at
        ) VALUES (
          %(id)s::uuid, %(website)s, %(phone)s, NULL, %(wa)s, %(book)s, %(notes)s, now()
        )
        ON CONFLICT (spot_id) DO UPDATE SET
          website = COALESCE(EXCLUDED.website, spot_public_profiles.website),
          phone = COALESCE(EXCLUDED.phone, spot_public_profiles.phone),
          whatsapp_url = COALESCE(EXCLUDED.whatsapp_url, spot_public_profiles.whatsapp_url),
          booking_url = COALESCE(EXCLUDED.booking_url, spot_public_profiles.booking_url),
          notes_public = COALESCE(EXCLUDED.notes_public, spot_public_profiles.notes_public),
          updated_at = now()
        """,
        {
            "id": spot_id,
            "website": p.get("website"),
            "phone": p.get("phone"),
            "wa": f"https://wa.me/{p['phone'].lstrip('+')}" if p.get("phone") else None,
            "book": p.get("booking_url"),
            "notes": (p.get("note") or "")[:900],
        },
    )


def upsert_facts(cur, spot_id: str) -> None:
    facts = {
        "booking_contact": ("yes", "takewake.ru / +79051282284", "http://takewake.ru/"),
        "pricing_clarity": ("yes", "тарифы на Яндекс.Картах / каталогах", "https://yandex.ru/maps/org/take_wake_konakovo/110769591192/"),
        "riding_quality": ("yes", "Nautique G23/G25 + реверс — сайт", "http://takewake.ru/"),
        "gear_rental": ("yes", "доски/экипировка на споте — VK/сайт", "https://vk.com/takewakekonakovo"),
        "coaching_available": ("unknown", "уточнять при записи", None),
        "changing_facilities": ("yes", "сёрф-отель / инфраструктура Ривер Клаб — сайт", "http://takewake.ru/"),
        "guest_comfort": ("yes", "отель/спортплощадка на территории", "http://takewake.ru/"),
        "hours_freshness": ("yes", "в источниках ~10:00–20:00 / по записи", "https://wakepulse.biz/wakepark?id=59"),
        "parking_access": ("yes", "Конаково Ривер Клаб — подъезд с шоссе", "http://takewake.ru/"),
        "safety_basics": ("unknown", "уточнять на площадке", None),
    }
    for key, (state, note, url) in facts.items():
        cur.execute(
            """
            INSERT INTO spot_convenience_facts (
              spot_id, checklist_key, state, evidence_note, source_url, observed_at, updated_at
            ) VALUES (
              %(id)s::uuid, %(key)s, %(state)s, %(note)s, %(url)s, %(obs)s, now()
            )
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


def main() -> None:
    import urllib.parse  # noqa: PLC0415 — used by nominatim

    globals()["urllib"] = urllib  # for nominatim helper namespace
    # patch nominatim to use urllib.parse from this scope
    def _nom(q: str):
        url = (
            "https://nominatim.openstreetmap.org/search?"
            + urllib.parse.urlencode({"q": q, "format": "json", "limit": 3})
        )
        req = urllib.request.Request(url, headers={"User-Agent": "SpotMap/1.0 (local-dev)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        print("NOMINATIM", [(d.get("display_name"), d.get("lat"), d.get("lon")) for d in data[:3]])
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])

    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Search existing
            cur.execute(
                """
                SELECT id::text, display_name, publication_status, geo_status,
                       ST_Y(point::geometry) lat, ST_X(point::geometry) lng
                FROM spots
                WHERE display_name ILIKE '%wakeweekend%'
                   OR display_name ILIKE '%wake weekend%'
                   OR display_name ILIKE '%take%wake%'
                   OR display_name ILIKE '%takewake%'
                   OR display_name ILIKE '%конаково%'
                ORDER BY display_name
                """
            )
            print("SPOTS", cur.fetchall())
            cur.execute(
                """
                SELECT id::text, legacy_row_id, raw_name, publication_status, geo_status
                FROM staging_candidates
                WHERE raw_name ILIKE '%wakeweekend%'
                   OR raw_name ILIKE '%take%wake%'
                   OR raw_name ILIKE '%takewake%'
                   OR raw_name ILIKE '%конаково%'
                ORDER BY raw_name
                """
            )
            print("STAGING", cur.fetchall())

            # Hide WakeWeekend — not a club
            cur.execute(
                """
                UPDATE spots
                SET publication_status = 'hidden',
                    operation_status = 'permanently_closed',
                    updated_at = now()
                WHERE display_name ILIKE '%wakeweekend%'
                   OR display_name ILIKE '%wake weekend%'
                RETURNING id::text, display_name, publication_status
                """
            )
            print("HIDE_WW_SPOT", cur.fetchall())
            cur.execute(
                """
                UPDATE staging_candidates
                SET publication_status = 'hidden',
                    operation_status = 'permanently_closed',
                    source_snapshot = left(coalesce(source_snapshot,'') ||
                      E'\\n[2026-11-20] WakeWeekend is an event series, not a club — hidden', 2000),
                    updated_at = now()
                WHERE raw_name ILIKE '%wakeweekend%'
                   OR raw_name ILIKE '%wake weekend%'
                RETURNING id::text, raw_name
                """
            )
            print("HIDE_WW_STAGING", cur.fetchall())

            # Update Wakesummer note: WakeWeekend was events, not club
            cur.execute(
                """
                UPDATE spot_public_profiles
                SET notes_public = left(
                  regexp_replace(
                    coalesce(notes_public,''),
                    'WakeWeekend[^.]*(.|$)',
                    '',
                    'gi'
                  ) || E' Исторически на площадках проводились события WakeWeekend — это не отдельный клуб.',
                  900
                ),
                updated_at = now()
                WHERE spot_id IN (
                  SELECT id FROM spots WHERE display_name ILIKE '%wakesummer%борисов%'
                )
                RETURNING spot_id::text
                """
            )
            print("NOTE_WS", cur.fetchall())

        conn.commit()

    coords = _nom("Конаково Крутые Берега 31")
    if not coords:
        coords = _nom("Konakovo Krutye Berega 31")
    if not coords:
        # Fallback: Konakovo River Club approximate from public maps listings
        # Prefer fail over inventing — abort promote if no geocode
        print("NO_GEOCODE — skip promote")
        return
    lat, lng = coords
    print("COORDS", lat, lng)

    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Already published?
            cur.execute(
                """
                SELECT id::text FROM spots
                WHERE display_name ILIKE '%take%wake%'
                   OR display_name ILIKE '%takewake%'
                LIMIT 1
                """
            )
            existing = cur.fetchone()
            if existing:
                sid = existing["id"]
                cur.execute(
                    """
                    UPDATE spots
                    SET display_name = %(name)s,
                        address_text = %(address)s,
                        locality = %(region)s,
                        point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
                        geo_status = 'verified',
                        publication_status = 'published',
                        updated_at = now()
                    WHERE id = %(id)s::uuid
                    RETURNING id::text, display_name
                    """,
                    {
                        "id": sid,
                        "name": TAKEWAKE["name"],
                        "address": TAKEWAKE["address"],
                        "region": TAKEWAKE["region"],
                        "lat": lat,
                        "lng": lng,
                    },
                )
                print("UPDATE_EXISTING", cur.fetchone())
                upsert_profile(cur, sid, TAKEWAKE)
                upsert_facts(cur, sid)
                conn.commit()
                print("DONE_EXISTING", sid)
                return

            fp = fingerprint(TAKEWAKE["legacy"], TAKEWAKE["name"])
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
                    "legacy": TAKEWAKE["legacy"],
                    "fp": fp,
                    "name": TAKEWAKE["name"],
                    "region": TAKEWAKE["region"],
                    "address": TAKEWAKE["address"],
                    "disciplines": TAKEWAKE["disciplines"],
                    "website": TAKEWAKE["website"],
                    "note": TAKEWAKE["note"][:900],
                    "lat": lat,
                    "lng": lng,
                    "query": TAKEWAKE["address"][:500],
                    "provider": PROVIDER,
                },
            )
            row = cur.fetchone()
            print("STAGING_UPSERT", row)
        conn.commit()
        cid, status = row["id"], row["publication_status"]

    if status == "merged":
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id::text FROM spots WHERE display_name = %s LIMIT 1",
                    (TAKEWAKE["name"],),
                )
                r = cur.fetchone()
                if r:
                    upsert_profile(cur, r["id"], TAKEWAKE)
                    upsert_facts(cur, r["id"])
                    conn.commit()
                    print("PROFILE_MERGED", r["id"])
        return

    res = promote(cid, lat, lng, TAKEWAKE["note"])
    print("PROMOTE", res)
    sid = res.get("spot_id")
    if sid:
        with psycopg.connect(DSN, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                upsert_profile(cur, sid, TAKEWAKE)
                upsert_facts(cur, sid)
            conn.commit()
            print("PROFILE_NEW", sid)


if __name__ == "__main__":
    main()
