"""Yandex Geocoder helpers for staging approximate pins. Never marks verified."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass


USELESS_ADDRESS_MARKERS = (
    "геолокация не проверена",
    "не указан",
    "unknown",
    "n/a",
    "нет адреса",
)


@dataclass(frozen=True)
class GeocodeHit:
    lat: float
    lng: float
    precision: str
    query: str
    provider: str = "yandex_geocoder"


def build_geocode_query(raw_name: str, raw_region: str | None, raw_address: str | None) -> tuple[str, str]:
    """Return (query, precision_hint). Prefer concrete address; else region/name."""
    address = (raw_address or "").strip()
    region = (raw_region or "").strip()
    name = (raw_name or "").strip()

    address_l = address.lower()
    useless = (not address) or any(m in address_l for m in USELESS_ADDRESS_MARKERS)
    # "Москва" alone as address is weak but usable with country.
    if not useless:
        if region and region.lower() not in address_l:
            return f"Россия, {region}, {address}", "address"
        return f"Россия, {address}", "address"

    if region:
        if name:
            return f"Россия, {region}, {name}", "name_region"
        return f"Россия, {region}", "region"

    if name:
        return f"Россия, {name}", "name_region"

    raise ValueError("no geocodeable fields")


def geocode_yandex(
    api_key: str,
    query: str,
    *,
    timeout: float = 20.0,
    http_referer: str | None = "http://127.0.0.1:18080/",
) -> GeocodeHit | None:
    params = urllib.parse.urlencode(
        {
            "apikey": api_key,
            "geocode": query,
            "format": "json",
            "results": "1",
            "lang": "ru_RU",
        }
    )
    url = f"https://geocode-maps.yandex.ru/1.x/?{params}"
    headers = {"User-Agent": "SpotMap/0.2 (staging-geocode)"}
    # Keys restricted by HTTP referrer reject bare server calls with 403.
    if http_referer:
        headers["Referer"] = http_referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    members = (
        payload.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )
    if not members:
        return None
    pos = members[0]["GeoObject"]["Point"]["pos"]  # "lng lat"
    lng_s, lat_s = pos.split()
    lat = float(lat_s)
    lng = float(lng_s)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return GeocodeHit(lat=lat, lng=lng, precision="address", query=query)


_SPACE_RE = re.compile(r"\s+")


def normalize_query(text: str) -> str:
    return _SPACE_RE.sub(" ", text).strip()
