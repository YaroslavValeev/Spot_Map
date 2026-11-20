"""Client convenience checklist v1 — maps to SpotScore domains, not a second rating."""

from __future__ import annotations

from typing import Any

CHECKLIST_V1: list[dict[str, str]] = [
    {
        "key": "booking_contact",
        "label": "Удобная запись и связь",
        "domain": "service",
    },
    {
        "key": "pricing_clarity",
        "label": "Понятные цены / длительность сета",
        "domain": "value",
    },
    {
        "key": "parking_access",
        "label": "Парковка и подъезд",
        "domain": "infrastructure",
    },
    {
        "key": "changing_facilities",
        "label": "Раздевалки / душ / туалет",
        "domain": "infrastructure",
    },
    {
        "key": "gear_rental",
        "label": "Прокат досок и жилетов",
        "domain": "equipment",
    },
    {
        "key": "coaching_available",
        "label": "Инструктор / обучение новичков",
        "domain": "coaching",
    },
    {
        "key": "safety_basics",
        "label": "Безопасность (брифинг, жилет, правила)",
        "domain": "safety",
    },
    {
        "key": "riding_quality",
        "label": "Качество волны / трассы под уровень",
        "domain": "riding_conditions_or_course_setup",
    },
    {
        "key": "guest_comfort",
        "label": "Зона ожидания / кафе / комфорт семьи",
        "domain": "infrastructure_service",
    },
    {
        "key": "hours_freshness",
        "label": "Актуальность сезона / часы работы",
        "domain": "freshness",
    },
]

CHECKLIST_KEYS = frozenset(item["key"] for item in CHECKLIST_V1)
VALID_STATES = frozenset({"yes", "no", "unknown", "unsupported"})


def pending_spot_score() -> dict[str, str]:
    return {
        "status": "pending",
        "label": "Появится позже",
        "hint": "Собираем отзывы и проверенные факты",
    }


def merge_convenience_rows(fact_rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Return full checklist; missing DB rows → unknown (missing ≠ false)."""
    by_key = {r["checklist_key"]: r for r in (fact_rows or []) if r.get("checklist_key")}
    out: list[dict[str, Any]] = []
    for item in CHECKLIST_V1:
        fact = by_key.get(item["key"]) or {}
        state = fact.get("state") or "unknown"
        if state not in VALID_STATES:
            state = "unknown"
        out.append(
            {
                "key": item["key"],
                "label": item["label"],
                "domain": item["domain"],
                "state": state,
                "evidence_note": fact.get("evidence_note"),
                "source_url": fact.get("source_url"),
                "observed_at": (
                    fact["observed_at"].isoformat()
                    if hasattr(fact.get("observed_at"), "isoformat")
                    else fact.get("observed_at")
                ),
            }
        )
    return out


def pick_lead_cta(
    contacts: dict[str, Any] | None,
    *,
    booking_go_href: str | None = None,
) -> dict[str, str] | None:
    """Priority: verified /go link → booking_url → whatsapp → telegram → phone → website.

    Label always means «переход к записи у клуба», never «вы записаны».
    """
    c = contacts or {}
    if booking_go_href:
        return {
            "kind": "booking_go",
            "href": booking_go_href,
            "label": "Записаться у клуба",
            "disclaimer": "Вы переходите на сайт клуба",
        }
    ordered = (
        ("booking", c.get("booking_url")),
        ("whatsapp", c.get("whatsapp_url")),
        ("telegram", c.get("telegram_url")),
        ("phone", c.get("phone")),
        ("website", c.get("website")),
    )
    for kind, value in ordered:
        if not value:
            continue
        href = str(value).strip()
        if not href:
            continue
        if kind == "phone" and not href.lower().startswith(("tel:", "http")):
            digits = "".join(ch for ch in href if ch.isdigit() or ch == "+")
            href = f"tel:{digits}" if digits else href
        label = "Записаться у клуба" if kind == "booking" else "Записаться"
        return {"kind": kind, "href": href, "label": label}
    return None
