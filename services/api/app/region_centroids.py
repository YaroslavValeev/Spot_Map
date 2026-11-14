"""Known Russia region/city centroids for staging approximate preview only."""

from __future__ import annotations

import hashlib

# Administrative centers / rough centroids. NOT verified spot coordinates.
REGION_CENTROIDS: dict[str, tuple[float, float]] = {
    "москва": (55.7558, 37.6173),
    "московская область": (55.5037, 37.2551),
    "москва/мо — уточнить": (55.72, 37.45),
    "санкт-петербург": (59.9343, 30.3351),
    "сочи": (43.6028, 39.7342),
    "краснодар": (45.0355, 38.9753),
    "ростов-на-дону": (47.2357, 39.7015),
    "казань": (55.7961, 49.1064),
    "екатеринбург": (56.8389, 60.6057),
    "новосибирск": (55.0084, 82.9357),
    "нижний новгород": (56.2965, 43.9361),
    "самара": (53.1959, 50.1002),
    "россия / отраслевое": (55.7558, 37.6173),
}


def resolve_region_centroid(raw_region: str | None, raw_address: str | None = None) -> tuple[float, float, str] | None:
    region = (raw_region or "").strip().lower()
    if region in REGION_CENTROIDS:
        lat, lng = REGION_CENTROIDS[region]
        return lat, lng, region

    address = (raw_address or "").strip().lower()
    for key, (lat, lng) in REGION_CENTROIDS.items():
        if key in region or (address and key in address):
            return lat, lng, key

    # Generic Moscow mentions in address text.
    if "москв" in address or "москв" in region:
        lat, lng = REGION_CENTROIDS["москва"]
        return lat, lng, "москва"

    # Explicitly unknown regions: still place as coarse Russia-preview pin.
    if region in {"", "не установлено", "вне региона", "россия / отраслевое"} or region is None:
        # Geographic-ish center of Russia for unresolved staging preview only.
        return 61.524, 105.318, "russia_unresolved"

    return None


def display_jitter(candidate_id: str, lat: float, lng: float, *, scale: float = 0.04) -> tuple[float, float]:
    """Small deterministic offset so many region pins are not a single stacked marker."""
    digest = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()
    dx = (int(digest[0:4], 16) / 65535.0 - 0.5) * 2.0 * scale
    dy = (int(digest[4:8], 16) / 65535.0 - 0.5) * 2.0 * scale
    return lat + dy, lng + dx
