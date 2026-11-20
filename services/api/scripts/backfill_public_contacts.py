"""Backfill spot_public_profiles + convenience facts from known OSINT (no secrets)."""
from __future__ import annotations

from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

DSN = "postgresql://spotmap:spotmap_dev_only@127.0.0.1:5432/spotmap"
NOW = datetime.now(timezone.utc)

# name substring (ilike) → contacts + optional convenience yes-keys with evidence
PROFILES = [
    {
        "match": "MyWave Wake",
        "website": "https://mywavewake.ru/",
        "phone": "+79957883344",
        "facts": {
            "booking_contact": ("yes", "mywavewake.ru + phone listings", "https://mywavewake.ru/"),
            "gear_rental": ("yes", "club offers wakesurf sessions / gear", "https://mywavewake.ru/"),
            "coaching_available": ("yes", "training mentioned on site", "https://mywavewake.ru/"),
        },
    },
    {
        "match": "WakeDivision Завидово",
        "website": "https://wakedivision.ru/opa-wake-zavidovo",
        "phone": "+79037269691",
        "facts": {
            "booking_contact": ("yes", "public phones", "https://wakedivision.ru/opa-wake-zavidovo"),
        },
    },
    {
        "match": "SecretSpot",
        "website": "https://www.secretspotwake.ru/",
        "phone": "+79157371195",
        "facts": {
            "booking_contact": ("yes", "secretspotwake.ru contacts", "https://www.secretspotwake.ru/"),
            "gear_rental": ("yes", "equipment listed on site", "https://www.secretspotwake.ru/"),
            "coaching_available": ("yes", "instructors listed", "https://www.secretspotwake.ru/"),
            "guest_comfort": ("yes", "hotel/territory on site", "https://www.secretspotwake.ru/"),
        },
    },
    {
        "match": "Riversurf Завидово",
        "website": "https://riversurf.ru/",
        "phone": "+79261023898",
        "facts": {
            "booking_contact": ("yes", "riversurf.ru contacts", "https://riversurf.ru/"),
            "pricing_clarity": ("yes", "price page", "https://riversurf.ru/price"),
        },
    },
    {
        "match": "Акватория Лета",
        "website": "https://aqualeto-zavidovo.com/",
        "phone": "+74957640290",
        "facts": {
            "booking_contact": ("yes", "aqualeto site", "https://aqualeto-zavidovo.com/"),
            "gear_rental": ("yes", "wake park rental mentioned", "https://aqualeto-zavidovo.com/"),
            "coaching_available": ("yes", "academy programs", "https://aqualeto-zavidovo.com/"),
        },
    },
    {
        "match": "WakeDivision",
        "website": "https://wakedivision.ru/wakedivision-sbercity",
        "phone": "+79801250585",
        "exclude": "Завидово",
        "facts": {
            "booking_contact": ("yes", "wakedivision sbercity page", "https://wakedivision.ru/wakedivision-sbercity"),
        },
    },
    {
        "match": "Waveriders",
        "website": "https://waveriders.ru/",
        "phone": "+79895772126",
        "facts": {
            "booking_contact": ("yes", "waveriders.ru", "https://waveriders.ru/"),
        },
    },
    {
        "match": "WakeJump",
        "website": "https://www.wakejump.ru/",
        "phone": "+79258331618",
        "facts": {
            "booking_contact": ("yes", "wakejump.ru GPS/contacts", "https://www.wakejump.ru/"),
            "gear_rental": ("yes", "equipment included per site", "https://www.wakejump.ru/"),
            "coaching_available": ("yes", "instructors on site", "https://www.wakejump.ru/"),
        },
    },
    {
        "match": "SURF BROTHERS",
        "website": "https://skolkovo.surfbrothers.ru/",
        "phone": "+74952412444",
        "booking_url": "https://skolkovo.surfbrothers.ru/contacts",
        "facts": {
            "booking_contact": ("yes", "surfbrothers contacts", "https://skolkovo.surfbrothers.ru/contacts"),
            "pricing_clarity": ("yes", "booking on site", "https://skolkovo.surfbrothers.ru/"),
            "changing_facilities": ("yes", "fitness/spa center", "https://skolkovo.surfbrothers.ru/"),
        },
    },
    {
        "match": "IstraWake",
        "website": "http://istrawake.ru/",
        "phone": "+74951666606",
        "facts": {
            "booking_contact": ("yes", "istrawake.ru", "http://istrawake.ru/"),
        },
    },
]


def upsert_profile(cur, spot_id: str, profile: dict) -> None:
    cur.execute(
        """
        INSERT INTO spot_public_profiles (
          spot_id, website, phone, telegram_url, whatsapp_url, booking_url, updated_at
        ) VALUES (
          %(spot_id)s::uuid, %(website)s, %(phone)s, %(telegram)s, %(whatsapp)s, %(booking)s, now()
        )
        ON CONFLICT (spot_id) DO UPDATE SET
          website = COALESCE(EXCLUDED.website, spot_public_profiles.website),
          phone = COALESCE(EXCLUDED.phone, spot_public_profiles.phone),
          telegram_url = COALESCE(EXCLUDED.telegram_url, spot_public_profiles.telegram_url),
          whatsapp_url = COALESCE(EXCLUDED.whatsapp_url, spot_public_profiles.whatsapp_url),
          booking_url = COALESCE(EXCLUDED.booking_url, spot_public_profiles.booking_url),
          updated_at = now()
        """,
        {
            "spot_id": spot_id,
            "website": profile.get("website"),
            "phone": profile.get("phone"),
            "telegram": profile.get("telegram_url"),
            "whatsapp": profile.get("whatsapp_url"),
            "booking": profile.get("booking_url"),
        },
    )


def upsert_facts(cur, spot_id: str, facts: dict) -> None:
    for key, (state, note, url) in facts.items():
        cur.execute(
            """
            INSERT INTO spot_convenience_facts (
              spot_id, checklist_key, state, evidence_note, source_url, observed_at, updated_at
            ) VALUES (
              %(spot_id)s::uuid, %(key)s, %(state)s, %(note)s, %(url)s, %(obs)s, now()
            )
            ON CONFLICT (spot_id, checklist_key) DO UPDATE SET
              state = EXCLUDED.state,
              evidence_note = EXCLUDED.evidence_note,
              source_url = EXCLUDED.source_url,
              observed_at = EXCLUDED.observed_at,
              updated_at = now()
            """,
            {
                "spot_id": spot_id,
                "key": key,
                "state": state,
                "note": note,
                "url": url,
                "obs": NOW,
            },
        )


def main() -> None:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        cur = conn.cursor()
        updated = 0
        for profile in PROFILES:
            cur.execute(
                """
                SELECT id::text, display_name
                FROM spots
                WHERE publication_status = 'published'
                  AND display_name ILIKE %(pat)s
                """,
                {"pat": f"%{profile['match']}%"},
            )
            rows = cur.fetchall()
            exclude = profile.get("exclude")
            for row in rows:
                if exclude and exclude.lower() in (row["display_name"] or "").lower():
                    continue
                # For bare "WakeDivision" skip Zavidovo/Secret already handled
                if profile["match"] == "WakeDivision" and (
                    "завидов" in row["display_name"].lower()
                    or "secret" in row["display_name"].lower()
                ):
                    continue
                upsert_profile(cur, row["id"], profile)
                upsert_facts(cur, row["id"], profile.get("facts") or {})
                updated += 1
                print("OK", row["display_name"], row["id"])
        conn.commit()
        print("UPDATED", updated)


if __name__ == "__main__":
    main()
