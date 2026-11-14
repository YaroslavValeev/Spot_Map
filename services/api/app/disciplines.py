"""Discipline tags for map icons/filters. Infer from staging text only — no invented facts."""

from __future__ import annotations

from typing import Any, Iterable

# UI + API slugs — colors from approved SpotMap pictogram sheet.
DISCIPLINE_CATALOG: list[dict[str, str]] = [
    {
        "slug": "waterski",
        "label": "Водные лыжи",
        "short": "Водные лыжи",
        "icon": "waterski",
        "symbol": "disc-waterski",
        "color": "#7B5CFF",
    },
    {
        "slug": "wakesurf_skim",
        "label": "Вейксерф / вейкским",
        "short": "Вейксерф / вейкским",
        "icon": "wakesurf",
        "symbol": "disc-wakesurf",
        "color": "#14B8A6",
    },
    {
        "slug": "wakeboard",
        "label": "Вейкборд — катер",
        "short": "Вейкборд — катер",
        "icon": "wakeboat",
        "symbol": "disc-wakeboat",
        "color": "#1D4ED8",
    },
    {
        "slug": "cable_ring",
        "label": "Кольцо — электротяга",
        "short": "Кольцо — электротяга",
        "icon": "cable-ring",
        "symbol": "disc-cable-ring",
        "color": "#22C55E",
    },
    {
        "slug": "cable_reverse",
        "label": "Реверс — электротяга",
        "short": "Реверс — электротяга",
        "icon": "cable-reverse",
        "symbol": "disc-cable-reverse",
        "color": "#EC4899",
    },
    {
        "slug": "cable_pool",
        "label": "Бассейн — электротяга",
        "short": "Бассейн — электротяга",
        "icon": "cable-pool",
        "symbol": "disc-cable-pool",
        "color": "#38BDF8",
    },
]

SLUGS = frozenset(item["slug"] for item in DISCIPLINE_CATALOG)
CABLE_SLUGS = frozenset({"cable_ring", "cable_reverse", "cable_pool"})

# Primary icon priority when a pin has several disciplines.
PRIMARY_ORDER = (
    "cable_pool",
    "cable_ring",
    "cable_reverse",
    "wakesurf_skim",
    "wakeboard",
    "waterski",
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

    is_pool = any(
        m in text
        for m in (
            "бассейн",
            "indoor_pool",
            "энигма",
            "крытый вейк",
            "50-метровый",
        )
    )
    is_ring = any(
        m in text
        for m in (
            "кольц",
            "circuit",
            "full_size_circuit",
            "кольцевая",
        )
    )
    is_reverse = any(
        m in text
        for m in (
            "реверс",
            "two_tower",
            "reversible",
        )
    )
    is_cableish = (
        candidate_kind == "cable_installation"
        or any(
            m in text
            for m in (
                "лебёд",
                "лебед",
                "электротяг",
                "кабельн",
                "cable",
                "wakeboard_cable",
            )
        )
    )

    # Explicit research taxonomy tags (from SpotMap research xlsx).
    if "water_ski" in text or "воднолыж" in text:
        found.add("waterski")
    if "cable_circuit" in text:
        found.add("cable_ring")
        is_ring = True
    if "cable_reverse" in text:
        found.add("cable_reverse")
        is_reverse = True
    if "cable_pool" in text:
        found.add("cable_pool")
        is_pool = True
    if "wakeboard_boat" in text:
        found.add("wakeboard")
    if "wakesurf" in text and "cable_" not in text.replace("wakesurf", ""):
        # keep wakesurf detection below as well
        pass

    if is_pool:
        found.add("cable_pool")
    if is_ring:
        found.add("cable_ring")
    if is_reverse:
        found.add("cable_reverse")
    if is_cableish and not (is_pool or is_ring or is_reverse):
        # Untyped cable installation — show under any electro filter via cable_reverse bucket.
        found.add("cable_reverse")

    if any(m in text for m in ("водн", "waterski", "water ski", "water-ski", "лыж")):
        # Avoid matching unrelated words; require ski/лыж context.
        if (
            "лыж" in text
            or "waterski" in text
            or "water ski" in text
            or "water-ski" in text
            or "воднолыж" in text
            or "water_ski" in text
        ):
            found.add("waterski")

    if any(
        m in text
        for m in (
            "wakesurf",
            "вейксерф",
            "вейксёрф",
            "wakeskim",
            "вейкским",
            "wake skim",
        )
    ):
        found.add("wakesurf_skim")
    elif "серф" in text and "искусствен" not in text and not is_cableish:
        # Generic "серф" at boat clubs usually means wakesurf in this dataset.
        found.add("wakesurf_skim")

    if any(m in text for m in ("wakeboard", "вейкборд", "вейк борд", "wakeboard_boat")):
        if is_cableish or is_pool or is_ring or is_reverse or "cable_" in text:
            # Cable wakeboard already covered by cable_* tags.
            pass
        else:
            found.add("wakeboard")

    # Staging clubs without explicit sport text: default P0 boat mix (not cable, not waterski).
    if not found and candidate_kind != "cable_installation":
        found.update({"wakesurf_skim", "wakeboard"})

    ordered = [slug for slug in PRIMARY_ORDER if slug in found]
    # Append any unexpected future slugs last.
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
    tags = set(row.get("disciplines") or [])
    return bool(tags & selected)


def count_disciplines(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count map objects that carry each discipline tag (one object may count in several)."""
    counts = {item["slug"]: 0 for item in DISCIPLINE_CATALOG}
    for row in rows:
        for slug in set(row.get("disciplines") or []):
            if slug in counts:
                counts[slug] += 1
    return counts
