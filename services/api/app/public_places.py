"""Public passport-lite for embed club card. Never invents SpotScore."""

from __future__ import annotations

from typing import Any

from .booking_redirect import booking_go_href, ensure_booking_link
from .convenience import merge_convenience_rows, pending_spot_score, pick_lead_cta
from .disciplines import enrich_row_disciplines
from .weather import attach_water_observation, forecast_point
from .wind_eval import evaluate_spot_rideability


SPOT_SQL = """
SELECT
  s.id::text AS id,
  'spot'::text AS entity_type,
  s.display_name AS name,
  s.locality,
  s.address_text,
  s.operation_status,
  s.geo_status,
  s.publication_status,
  ST_Y(s.point::geometry) AS lat,
  ST_X(s.point::geometry) AS lng
FROM spots s
WHERE s.id = %(id)s::uuid
  AND s.publication_status = 'published'
  AND s.geo_status = 'verified'
  AND s.point IS NOT NULL
"""

INSTALLATION_SQL = """
SELECT
  c.id::text AS id,
  'cable_installation'::text AS entity_type,
  c.name AS name,
  s.locality,
  s.address_text,
  c.operation_status,
  c.geo_status,
  c.publication_status,
  ST_Y(c.point::geometry) AS lat,
  ST_X(c.point::geometry) AS lng,
  c.spot_id::text AS parent_spot_id,
  s.display_name AS parent_spot_name
FROM cable_installations c
JOIN spots s ON s.id = c.spot_id
WHERE c.id = %(id)s::uuid
  AND c.publication_status = 'published'
  AND c.geo_status = 'verified'
  AND c.point IS NOT NULL
"""

PROFILE_SQL = """
SELECT website, phone, telegram_url, whatsapp_url, booking_url, notes_public
FROM spot_public_profiles
WHERE spot_id = %(spot_id)s::uuid
"""

FACTS_SQL = """
SELECT checklist_key, state, evidence_note, source_url, observed_at
FROM spot_convenience_facts
WHERE spot_id = %(spot_id)s::uuid
"""

STAGING_HINT_SQL = """
SELECT
  official_or_public_website,
  public_telegram_url,
  source_url,
  raw_disciplines
FROM staging_candidates
WHERE publication_status = 'merged'
  AND (
    raw_name = %(name)s
    OR source_snapshot ILIKE '%%' || %(name)s || '%%'
  )
ORDER BY updated_at DESC NULLS LAST
LIMIT 1
"""


def _contacts_from_profile(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {
            "website": None,
            "phone": None,
            "telegram_url": None,
            "whatsapp_url": None,
            "booking_url": None,
            "notes_public": None,
        }
    return {
        "website": row.get("website"),
        "phone": row.get("phone"),
        "telegram_url": row.get("telegram_url"),
        "whatsapp_url": row.get("whatsapp_url"),
        "booking_url": row.get("booking_url"),
        "notes_public": row.get("notes_public"),
    }


def _route_url(lat: float | None, lng: float | None, _name: str = "") -> str | None:
    if lat is None or lng is None:
        return None
    # Empty origin (~lat,lng) → Yandex opens route builder to the spot.
    return f"https://yandex.ru/maps/?rtext=~{lat},{lng}&rtt=auto"


def fetch_public_place(
    conn,
    *,
    place_id: str,
    entity_type: str = "spot",
    include_live_services: bool = True,
) -> dict[str, Any]:
    entity_type = (entity_type or "spot").strip().lower()
    if entity_type not in {"spot", "cable_installation"}:
        raise ValueError("entity_type must be spot or cable_installation")

    with conn.cursor() as cur:
        if entity_type == "spot":
            cur.execute(SPOT_SQL, {"id": place_id})
        else:
            cur.execute(INSTALLATION_SQL, {"id": place_id})
        row = cur.fetchone()
        if not row:
            raise KeyError("place not found")
        cols = [d.name for d in cur.description]
        place = dict(zip(cols, row))

        profile_spot_id = place_id if entity_type == "spot" else place.get("parent_spot_id")
        contacts = _contacts_from_profile(None)
        facts: list[dict[str, Any]] = []
        if profile_spot_id:
            cur.execute(PROFILE_SQL, {"spot_id": profile_spot_id})
            prow = cur.fetchone()
            if prow:
                pcols = [d.name for d in cur.description]
                contacts = _contacts_from_profile(dict(zip(pcols, prow)))
            cur.execute(FACTS_SQL, {"spot_id": profile_spot_id})
            fcols = [d.name for d in cur.description]
            facts = [dict(zip(fcols, r)) for r in cur.fetchall()]

        # Fallback website/telegram from merged staging by name (read-only hint).
        if not contacts.get("website") or not contacts.get("telegram_url"):
            cur.execute(STAGING_HINT_SQL, {"name": place.get("name") or ""})
            hint = cur.fetchone()
            if hint:
                hcols = [d.name for d in cur.description]
                h = dict(zip(hcols, hint))
                if not contacts.get("website"):
                    contacts["website"] = h.get("official_or_public_website") or h.get("source_url")
                if not contacts.get("telegram_url"):
                    contacts["telegram_url"] = h.get("public_telegram_url")
                place["raw_disciplines"] = h.get("raw_disciplines")

    enriched = enrich_row_disciplines(
        {
            "name": place.get("name"),
            "raw_disciplines": place.get("raw_disciplines"),
            "raw_address": place.get("address_text"),
            "entity_type": place.get("entity_type"),
        }
    )

    profile_spot = profile_spot_id or place_id
    go_id = None
    weather = None
    rideability = {
        "status": "not_configured",
        "verdict": None,
        "label": "Не оценено",
        "reason": "Ветровой профиль не утверждён",
    }
    lat = place.get("lat")
    lng = place.get("lng")

    if include_live_services:
        if contacts.get("booking_url"):
            try:
                go_id = ensure_booking_link(
                    conn,
                    spot_id=profile_spot,
                    target_url=str(contacts["booking_url"]),
                )
                conn.commit()
            except Exception:  # noqa: BLE001
                try:
                    conn.rollback()
                except Exception:  # noqa: BLE001
                    pass
                go_id = None

        if lat is not None and lng is not None:
            try:
                weather = forecast_point(float(lat), float(lng))
                weather = attach_water_observation(conn, profile_spot, weather)
            except Exception:  # noqa: BLE001
                weather = None
            try:
                rideability = evaluate_spot_rideability(
                    conn,
                    spot_id=profile_spot,
                    forecast=weather,
                    discipline_id=enriched.get("primary_discipline"),
                )
            except Exception:  # noqa: BLE001
                pass

    lead = pick_lead_cta(contacts, booking_go_href=booking_go_href(go_id))

    return {
        "id": place["id"],
        "entity_type": place["entity_type"],
        "name": place["name"],
        "locality": place.get("locality"),
        "address_text": place.get("address_text"),
        "operation_status": place.get("operation_status"),
        "geo_status": place.get("geo_status"),
        "coordinates": {"lat": float(lat), "lng": float(lng)} if lat is not None else None,
        "disciplines": enriched.get("disciplines") or [],
        "primary_discipline": enriched.get("primary_discipline"),
        "discipline_label": enriched.get("discipline_label"),
        "parent_spot_id": place.get("parent_spot_id"),
        "parent_spot_name": place.get("parent_spot_name"),
        "contacts": contacts,
        "lead_cta": lead,
        "booking_link_id": go_id,
        "route_url": _route_url(
            float(lat) if lat is not None else None,
            float(lng) if lng is not None else None,
            place.get("name") or "SpotMap",
        ),
        "spot_score": pending_spot_score(),
        "ratings": {
            "spot_score": pending_spot_score(),
            "external": [],
            "remote_audit": {"status": "not_configured", "label": "Дистанционная оценка не заполнена"},
            "field_expert": {"status": "not_configured", "label": "Личная полевая проверка не выполнена"},
        },
        "rideability": rideability
        or {
            "status": "not_configured",
            "verdict": None,
            "label": "Не оценено",
            "reason": "Ветровой профиль не утверждён",
        },
        "weather": weather,
        "convenience": merge_convenience_rows(facts),
        "club_manage": {
            "cta_label": "Это мой спот",
            "manage_spot_id": profile_spot or place_id,
            "moderator_telegram": "@MyWave23",
            "moderator_email": "y.valeev@gmail.com",
            "hint": "Заявка уходит модератору. Редактор паспорта откроется после подтверждения.",
        },
    }
