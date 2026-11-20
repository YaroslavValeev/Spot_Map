"""Discipline tags for map filters. ADR-006 (amended): co-location rules, no SUP/kneeboard/barefoot."""

from __future__ import annotations

from typing import Any, Iterable

# Sport catalog + installation facets. Kneeboard, barefoot, wakeskate_cable removed.
DISCIPLINE_CATALOG: list[dict[str, str]] = [
    {"slug": "waterski_slalom", "label": "Водные лыжи — слалом", "short": "Слалом", "icon": "waterski", "symbol": "disc-waterski", "color": "#7B5CFF", "kind": "sport"},
    {"slug": "waterski_tricks", "label": "Водные лыжи — фигурное", "short": "Фигурное", "icon": "waterski", "symbol": "disc-waterski", "color": "#8B5CF6", "kind": "sport"},
    {"slug": "waterski_jump", "label": "Водные лыжи — прыжки", "short": "Прыжки", "icon": "waterski", "symbol": "disc-waterski", "color": "#A78BFA", "kind": "sport"},
    {"slug": "adaptive_waterski", "label": "Адаптивные водные лыжи", "short": "Адаптив", "icon": "waterski", "symbol": "disc-waterski", "color": "#6366F1", "kind": "sport"},
    {"slug": "wakeboard_boat", "label": "Вейкборд — катер", "short": "Вейкборд", "icon": "wakeboat", "symbol": "disc-wakeboat", "color": "#1D4ED8", "kind": "sport"},
    {"slug": "wakeskate", "label": "Вейкскейт", "short": "Вейкскейт", "icon": "wakeboat", "symbol": "disc-wakeboat", "color": "#2563EB", "kind": "sport"},
    {"slug": "wakesurf", "label": "Вейксерф", "short": "Вейксерф", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#14B8A6", "kind": "sport"},
    {"slug": "wakeskim", "label": "Вейкским", "short": "Вейкским", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#2DD4BF", "kind": "sport"},
    {"slug": "wakesurf_longboard", "label": "Вейксерф-лонгборд", "short": "Лонгборд", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#0D9488", "kind": "sport"},
    {"slug": "wakefoil", "label": "Вейкфойл", "short": "Вейкфойл", "icon": "wakesurf", "symbol": "disc-wakesurf", "color": "#0F766E", "kind": "sport"},
    {"slug": "wakeboard_cable", "label": "Вейкборд — электротяга", "short": "Кабель-вейк", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#059669", "kind": "sport"},
    {"slug": "waterski_cable", "label": "Водные лыжи — электротяга", "short": "Лыжи-кабель", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#10B981", "kind": "sport"},
    # Installation facets (not sport count).
    {"slug": "cable_ring", "label": "Кольцо — электротяга", "short": "Кольцо", "icon": "cable-ring", "symbol": "disc-cable-ring", "color": "#22C55E", "kind": "installation"},
    {"slug": "cable_reverse", "label": "Реверс — электротяга", "short": "Реверс", "icon": "cable-reverse", "symbol": "disc-cable-reverse", "color": "#EC4899", "kind": "installation"},
    {"slug": "cable_pool", "label": "Бассейн — электротяга", "short": "Бассейн", "icon": "cable-pool", "symbol": "disc-cable-pool", "color": "#38BDF8", "kind": "installation"},
]

SPORT_SLUGS = frozenset(i["slug"] for i in DISCIPLINE_CATALOG if i.get("kind") == "sport")
INSTALL_SLUGS = frozenset(i["slug"] for i in DISCIPLINE_CATALOG if i.get("kind") == "installation")
SLUGS = frozenset(item["slug"] for item in DISCIPLINE_CATALOG)
CABLE_SLUGS = frozenset(
    {"cable_ring", "cable_reverse", "cable_pool", "wakeboard_cable", "waterski_cable", "wakeskate"}
)

# Classic waterski suite — only at waterski clubs.
WATERSKI_CLUB_TAGS = frozenset(
    {"waterski_slalom", "waterski_tricks", "waterski_jump", "adaptive_waterski"}
)
# Always co-located with wakesurf (boat).
WAKESURF_FAMILY = frozenset({"wakesurf", "wakeskim", "wakesurf_longboard", "wakefoil"})
# Boat-only sports — never show on cable-only parks without explicit boat ops.
BOAT_ONLY_SPORTS = WAKESURF_FAMILY | {"wakeboard_boat"} | WATERSKI_CLUB_TAGS

FILTER_ALIASES: dict[str, frozenset[str]] = {
    "waterski": frozenset(WATERSKI_CLUB_TAGS | {"waterski_cable"}),
    "wakesurf_skim": frozenset(WAKESURF_FAMILY),
    "wakesurf": frozenset(WAKESURF_FAMILY),
    "wakeboard": frozenset({"wakeboard_boat"}),
    "wakeboard_boat": frozenset({"wakeboard_boat"}),
    "wakeboard_cable": frozenset(
        {"wakeboard_cable", "cable_ring", "cable_reverse", "cable_pool", "wakeskate", "waterski_cable"}
    ),
    # Removed slugs still expand harmlessly if old UI sends them.
    "barefoot": frozenset(WATERSKI_CLUB_TAGS),
    "kneeboard": frozenset({"wakeboard_boat"}),
    "wakeskate_cable": frozenset({"wakeskate", "cable_ring", "cable_reverse"}),
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
    "waterski_cable",
    "wakeskate",
    "wakeboard_boat",
    "waterski_slalom",
    "waterski_tricks",
    "waterski_jump",
    "adaptive_waterski",
)


def _blob(*parts: str | None) -> str:
    return " ".join((p or "").lower() for p in parts)


def _has_explicit_boat_ops(text: str) -> bool:
    """True only for real boat operations — not noisy WAKEBOARD_BOAT/WAKESURF staging tags."""
    return any(
        m in text
        for m in (
            "катер",
            "катерн",
            "на катере",
            "tow boat",
            "surf boat",
            "boat wake",
            "катерный",
        )
    )


def _is_waterski_club(text: str, *, cableish: bool = False) -> bool:
    """True for classic waterski clubs — not WATER_SKI tags on cable parks."""
    if any(
        m in text
        for m in (
            "воднолыж",
            "воднолыжный",
            "water ski club",
            "waterski club",
        )
    ):
        return True
    # On cable venues WATER_SKI / waterski means waterski_cable, not classic suite.
    if cableish:
        return False
    if any(
        m in text
        for m in (
            "водные лыжи",
            "water ski",
            "water-ski",
            "water_ski",
            "waterski_slalom",
            "waterski_tricks",
            "waterski_jump",
            "adaptive_waterski",
        )
    ):
        return True
    if "waterski" in text and "wakeboard" not in text and "вейк" not in text:
        return True
    return False


def _attach_wakesurf_family(found: set[str]) -> None:
    if found & {"wakesurf", "wakeskim", "wakesurf_longboard", "wakefoil"}:
        found.update(WAKESURF_FAMILY)


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

    is_pool = any(
        m in text for m in ("бассейн", "indoor_pool", "энигма", "крытый вейк", "50-метровый", "cable_pool")
    )
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
    cable_primary = bool(
        candidate_kind == "cable_installation" or is_pool or is_ring or is_reverse or is_cableish
    )
    boat_ops = _has_explicit_boat_ops(text)

    # --- Waterski clubs: classic trio + adaptive (never from bare WATER_SKI on cable) ---
    if _is_waterski_club(text, cableish=cable_primary):
        found.update(WATERSKI_CLUB_TAGS)

    # --- Wakesurf family (boat). Skip noisy WAKESURF tags on cable-only parks. ---
    allow_boat_surf = boat_ops or not cable_primary
    if allow_boat_surf:
        if any(m in text for m in ("wakesurf_longboard", "лонгборд", "longboard")):
            found.add("wakesurf_longboard")
        if any(m in text for m in ("wakefoil", "вейкфойл", "wake foil", "гидрофойл")):
            found.add("wakefoil")
        if any(m in text for m in ("wakeskim", "вейкским", "wake skim")):
            found.add("wakeskim")
        if any(m in text for m in ("wakesurf", "вейксерф", "вейксёрф")):
            found.add("wakesurf")
        elif (
            "серф" in text
            and "искусствен" not in text
            and not cable_primary
            and "сап" not in text
            and "sup" not in text
        ):
            found.add("wakesurf")
        _attach_wakesurf_family(found)

    # --- Boat / cable wakeboard ---
    if any(m in text for m in ("wakeboard", "вейкборд", "вейк борд", "wakeboard_boat")):
        if cable_primary:
            found.add("wakeboard_cable")
            if boat_ops:
                found.add("wakeboard_boat")
        else:
            found.add("wakeboard_boat")

    # Explicit wakeskate mention (non-cable-only slug).
    if "wakeskate" in text or "вейкскейт" in text:
        found.add("wakeskate")

    # --- Installation facets + co-location rules ---
    if is_pool:
        found.add("cable_pool")
        found.add("wakeboard_cable")
        found.add("waterski_cable")
    if is_ring:
        found.add("cable_ring")
        found.add("wakeboard_cable")
        found.add("wakeskate")  # вейкскейт на кольце
        found.add("waterski_cable")
    if is_reverse:
        found.add("cable_reverse")
        found.add("wakeboard_cable")
        found.add("wakeskate")  # вейкскейт на реверсе
        found.add("waterski_cable")
    if is_cableish and not (is_pool or is_ring or is_reverse):
        found.add("cable_reverse")
        found.add("wakeboard_cable")
        found.add("wakeskate")
        found.add("waterski_cable")
    elif is_cableish or is_pool:
        # Any electro / pool always carries waterski_cable.
        found.add("waterski_cable")
        found.add("wakeboard_cable")

    # Staging clubs without explicit sport text: default P0 boat mix (never foil family alone).
    if not found and candidate_kind != "cable_installation":
        found.update({"wakesurf", "wakeboard_boat"})
        _attach_wakesurf_family(found)

    # Cable-only parks: strip boat sports unless explicit boat ops (катер…).
    if cable_primary and not boat_ops:
        found -= BOAT_ONLY_SPORTS

    # Never emit removed slugs.
    found.discard("kneeboard")
    found.discard("barefoot")
    found.discard("wakeskate_cable")
    found.discard("show_ski")
    found.discard("sup")

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
    counts = {item["slug"]: 0 for item in DISCIPLINE_CATALOG}
    for row in rows:
        for slug in set(row.get("disciplines") or []):
            if slug in counts:
                counts[slug] += 1
    return counts
