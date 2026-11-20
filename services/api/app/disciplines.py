"""Discipline tags for map icons/filters. ADR-006: 16 sports + install facets. No SUP."""

from __future__ import annotations

from typing import Any, Iterable

# 16 sport disciplines (ADR-006) + 3 installation facets (not counted in the 16).
DISCIPLINE_CATALOG: list[dict[str, str]] = [
    {"slug": "waterski_slalom", "label": "Водные лыжи — слалом", "short": "Слалом", "icon": "waterski", "symbol": "disc-waterski", "color": "#7B5CFF", "kind": "sport"},
    {"slug": "waterski_tricks", "label": "Водные лыжи — фигурное", "short": "Фигурное", "icon": "waterski", "symbol": "disc-waterski", "color": "#8B5CF6", "kind": "sport"},
    {"slug": "waterski_jump", "label": "Водные лыжи — прыжки", "short": "Прыжки", "icon": "waterski", "symbol": "disc-waterski", "color": "#A78BFA", "kind": "sport"},
    {"slug": "barefoot", "label": "Барефут", "short": "Барефут", "icon": "waterski", "symbol": "disc-waterski", "color": "#C4B5FD", "kind": "sport"},
    {"slug": "wakeboard_boat", "label": "Вейкборд — катер", "short": "Вейкборд", "icon": "wakeboat", "symbol": "disc-wakeboat", "color": "#1D4ED8", "kind": "sport"},
    {"slug": "wakeskate", "label": "Вейкскейт", "short": "Вейкскейт", "icon": "wakeboat", "symbol": "disc-wakeboat", "color": "#2563EB", "kind": "sport"},
    {"slug": "kneeboard", "label": "Ниборд", "short": "Ниборд", "icon": "wakeboat", "symbol": "disc-wakeboat", "color": "#3B82F6", "kind": "sport"},
    {"slug": "wakesurf", "label": "Вейксерф", "short": "Вейксерф", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#14B8A6", "kind": "sport"},
    {"slug": "wakeskim", "label": "Вейкским", "short": "Вейкским", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#2DD4BF", "kind": "sport"},
    {"slug": "wakeboard_cable", "label": "Вейкборд — электротяга", "short": "Кабель-вейк", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#059669", "kind": "sport"},
    {"slug": "waterski_cable", "label": "Водные лыжи — электротяга", "short": "Лыжи-кабель", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#10B981", "kind": "sport"},
    {"slug": "wakeskate_cable", "label": "Вейкскейт — электротяга", "short": "Скейт-кабель", "icon": "cable-reverse", "symbol": "disc-cable-reverse", "color": "#34D399", "kind": "sport"},
    {"slug": "adaptive_waterski", "label": "Адаптивные водные лыжи", "short": "Адаптив", "icon": "waterski", "symbol": "disc-waterski", "color": "#6366F1", "kind": "sport"},
    {"slug": "show_ski", "label": "Фигурно-показательные лыжи", "short": "Show ski", "icon": "waterski", "symbol": "disc-waterski", "color": "#818CF8", "kind": "sport"},
    {"slug": "wakesurf_longboard", "label": "Вейксерф-лонгборд", "short": "Лонгборд", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#0D9488", "kind": "sport"},
    {"slug": "wakefoil", "label": "Вейкфойл", "short": "Вейкфойл", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#0F766E", "kind": "sport"},
    # Installation facets (not part of the 16).
    {"slug": "cable_ring", "label": "Кольцо — электротяга", "short": "Кольцо", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#22C55E", "kind": "installation"},
    {"slug": "cable_reverse", "label": "Реверс — электротяга", "short": "Реверс", "icon": "cable-reverse", "symbol": "disc-cable-reverse", "color": "#EC4899", "kind": "installation"},
    {"slug": "cable_pool", "label": "Бассейн — электротяга", "short": "Бассейн", "icon": "cable-pool", "symbol": "disc-cable-pool", "color": "#38BDF8", "kind": "installation"},
]

SPORT_SLUGS = frozenset(i["slug"] for i in DISCIPLINE_CATALOG if i.get("kind") == "sport")
INSTALL_SLUGS = frozenset(i["slug"] for i in DISCIPLINE_CATALOG if i.get("kind") == "installation")
SLUGS = frozenset(item["slug"] for item in DISCIPLINE_CATALOG)
CABLE_SLUGS = frozenset({"cable_ring", "cable_reverse", "cable_pool", "wakeboard_cable", "waterski_cable", "wakeskate_cable"})

# Legacy UI filter aliases → expand to matching tags on a pin.
FILTER_ALIASES: dict[str, frozenset[str]] = {
    "waterski": frozenset(
        {
            "waterski_slalom",
            "waterski_tricks",
            "waterski_jump",
            "barefoot",
            "adaptive_waterski",
            "show_ski",
            "waterski_cable",
        }
    ),
    "wakesurf_skim": frozenset({"wakesurf", "wakeskim", "wakesurf_longboard"}),
    "wakeboard": frozenset({"wakeboard_boat"}),
    "wakeboard_boat": frozenset({"wakeboard_boat"}),
    "wakeboard_cable": frozenset(
        {"wakeboard_cable", "cable_ring", "cable_reverse", "cable_pool", "wakeskate_cable", "waterski_cable"}
    ),
}

PRIMARY_ORDER = (
    "cable_pool",
    "cable_ring",
    "cable_reverse",
    "wakefoil",
    "wakesurf_longboard",
    "wakesurf",
    "wakeskim",
    "wakeboard_cable",
    "wakeskate_cable",
    "waterski_cable",
    "wakeboard_boat",
    "wakeskate",
    "kneeboard",
    "waterski_slalom",
    "waterski_tricks",
    "waterski_jump",
    "barefoot",
    "adaptive_waterski",
    "show_ski",
)


def _blob(*parts: str | None) -> str:
    return " ".join((p or "").lower() for p in parts)


def classify_disciplines(
    *,
    name: str | None = None,
    raw_disciplines: str | None = None,
    raw_address: str | None = None,
    candidate_kind: str | None = None,
) -> list[str]:
    """Return ordered unique discipline slugs for a staging/map row."""
    text = _blob(name, raw_disciplines, raw_address, candidate_kind)
    found: set[str] = set()

    # Hard ban SUP — never classify as a sport from paddle text alone.
    # (Explicit SUP mentions are ignored.)

    is_pool = any(m in text for m in ("бассейн", "indoor_pool", "энигма", "крытый вейк", "50-метровый", "cable_pool"))
    is_ring = any(
        m in text
        for m in ("кольц", "circuit", "full_size_circuit", "кольцевая", "cable_circuit", "cable_ring")
    )
    is_reverse = any(m in text for m in ("реверс", "two_tower", "reversible", "cable_reverse"))
    is_cableish = candidate_kind == "cable_installation" or any(
        m in text
        for m in (
            "лебёд",
            "лебед",
            "электротяг",
            "кабельн",
            "cable",
            "wakeboard_cable",
            "rixen",
        )
    )

    if "water_ski" in text or "воднолыж" in text or "waterski_slalom" in text:
        found.add("waterski_slalom")
    if "waterski_tricks" in text or "фигурн" in text and "лыж" in text:
        found.add("waterski_tricks")
    if "waterski_jump" in text or ("прыж" in text and "лыж" in text):
        found.add("waterski_jump")
    if "barefoot" in text or "барефут" in text:
        found.add("barefoot")
    if "adaptive" in text or "адаптив" in text:
        found.add("adaptive_waterski")
    if "show_ski" in text or "показательн" in text:
        found.add("show_ski")
    if "kneeboard" in text or "ниборд" in text or "knee board" in text:
        found.add("kneeboard")
    if "wakesurf_longboard" in text or "лонгборд" in text or "longboard" in text:
        found.add("wakesurf_longboard")
    if "wakefoil" in text or "вейкфойл" in text or "wake foil" in text or "гидрофойл" in text:
        found.add("wakefoil")
    if "wakeskim" in text or "вейкским" in text or "wake skim" in text:
        found.add("wakeskim")
    if any(m in text for m in ("wakesurf", "вейксерф", "вейксёрф")) and "longboard" not in text and "лонгборд" not in text:
        found.add("wakesurf")
    elif "серф" in text and "искусствен" not in text and not is_cableish and "сап" not in text and "sup" not in text:
        found.add("wakesurf")

    if "wakeskate_cable" in text:
        found.add("wakeskate_cable")
    elif "wakeskate" in text or "вейкскейт" in text:
        found.add("wakeskate_cable" if is_cableish else "wakeskate")

    if "waterski_cable" in text:
        found.add("waterski_cable")
    elif is_cableish and any(m in text for m in ("водн", "лыж", "waterski")):
        found.add("waterski_cable")

    if any(m in text for m in ("wakeboard", "вейкборд", "вейк борд", "wakeboard_boat")):
        if is_cableish or is_pool or is_ring or is_reverse or "cable_" in text:
            found.add("wakeboard_cable")
        else:
            found.add("wakeboard_boat")

    if is_pool:
        found.add("cable_pool")
        found.add("wakeboard_cable")
    if is_ring:
        found.add("cable_ring")
        found.add("wakeboard_cable")
    if is_reverse:
        found.add("cable_reverse")
        found.add("wakeboard_cable")
    if is_cableish and not (is_pool or is_ring or is_reverse):
        found.add("cable_reverse")
        found.add("wakeboard_cable")

    if any(m in text for m in ("лыж", "waterski", "water ski", "water-ski", "воднолыж", "water_ski")):
        if not any(s in found for s in ("waterski_slalom", "waterski_tricks", "waterski_jump", "waterski_cable", "barefoot")):
            if is_cableish:
                found.add("waterski_cable")
            else:
                found.add("waterski_slalom")

    # Staging clubs without explicit sport text: default P0 boat mix (never foil/longboard/SUP).
    if not found and candidate_kind != "cable_installation":
        found.update({"wakesurf", "wakeboard_boat"})

    ordered = [slug for slug in PRIMARY_ORDER if slug in found]
    for slug in sorted(found):
        if slug not in ordered:
            ordered.append(slug)
    return ordered


def primary_discipline(slugs: Iterable[str]) -> str | None:
    present = set(slugs)
    for slug in PRIMARY_ORDER:
        if slug in present:
            return slug
    return next(iter(present), None)


def catalog_by_slug() -> dict[str, dict[str, str]]:
    return {item["slug"]: item for item in DISCIPLINE_CATALOG}


def expand_filter_selection(selected: set[str]) -> set[str]:
    """Expand legacy aliases so old UI chips still match new tags."""
    out: set[str] = set()
    for slug in selected:
        if not slug:
            continue
        out.add(slug)
        out |= FILTER_ALIASES.get(slug, frozenset())
    return out


def enrich_row_disciplines(row: dict[str, Any]) -> dict[str, Any]:
    slugs = classify_disciplines(
        name=row.get("name") or row.get("raw_name"),
        raw_disciplines=row.get("raw_disciplines"),
        raw_address=row.get("raw_address"),
        candidate_kind=row.get("entity_type") or row.get("candidate_kind"),
    )
    primary = primary_discipline(slugs)
    meta = catalog_by_slug().get(primary or "", {})
    out = dict(row)
    out["disciplines"] = slugs
    out["primary_discipline"] = primary
    out["discipline_color"] = meta.get("color") or "#64748B"
    out["discipline_symbol"] = meta.get("symbol") or "disc-wakesurf"
    out["discipline_label"] = meta.get("label") or primary
    return out


def row_matches_discipline_filter(row: dict[str, Any], selected: set[str] | None) -> bool:
    if not selected:
        return True
    expanded = expand_filter_selection(selected)
    tags = set(row.get("disciplines") or [])
    return bool(tags & expanded)


def count_disciplines(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count map objects that carry each discipline tag (one object may count in several)."""
    counts = {item["slug"]: 0 for item in DISCIPLINE_CATALOG}
    for row in rows:
        for slug in set(row.get("disciplines") or []):
            if slug in counts:
                counts[slug] += 1
    return counts
