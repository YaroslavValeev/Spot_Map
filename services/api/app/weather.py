"""WeatherProvider — normalized point forecast. No invented water temperature."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import settings

# In-process TTL cache (seconds). Does not replace Redis for multi-worker prod.
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 20 * 60


def _cache_get(key: str) -> dict[str, Any] | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    expires, payload = hit
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return payload


def _cache_set(key: str, payload: dict[str, Any]) -> None:
    _CACHE[key] = (time.time() + _CACHE_TTL, payload)


def wind_layer_status() -> dict[str, Any]:
    """Yandex/OpenWeather wind tiles require licensed keys — honest disabled by default."""
    enabled = bool((settings.yandex_weather_tile_key or "").strip())
    return {
        "enabled": enabled,
        "label": "Ветер — слой" if enabled else "Ветровой слой недоступен",
        "reason": None
        if enabled
        else "Нет лицензированного ключа тайлов ветра (Yandex Weather / аналог)",
        "provider": "yandex_weather_tiles" if enabled else None,
    }


def empty_weather_payload(*, reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "provider": None,
        "observed_or_forecast_at": None,
        "updated_at": None,
        "air_c": None,
        "wind_mps": None,
        "direction_from_deg": None,
        "gust_mps": None,
        "precipitation_mm": None,
        "water_c": None,
        "water_status": "no_measurement",
        "water_reason": "Нет свежего измерения температуры воды",
        "hourly": [],
    }


def forecast_point(lat: float, lon: float) -> dict[str, Any]:
    """Open-Meteo pilot for air/wind. Water never inferred from air."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("lat/lon out of range")

    if not settings.weather_open_meteo_enabled:
        payload = empty_weather_payload(reason="Open-Meteo выключен (WEATHER_OPEN_METEO_ENABLED=false)")
        payload["wind_layer"] = wind_layer_status()
        return payload

    key = f"om:{lat:.4f}:{lon:.4f}"
    cached = _cache_get(key)
    if cached:
        out = dict(cached)
        out["cached"] = True
        out["wind_layer"] = wind_layer_status()
        return out

    base = (settings.weather_open_meteo_base_url or "https://api.open-meteo.com").rstrip("/")
    qs = urllib.parse.urlencode(
        {
            "latitude": f"{lat:.5f}",
            "longitude": f"{lon:.5f}",
            "current": "temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation",
            "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation",
            "forecast_days": "2",
            "wind_speed_unit": "ms",
            "timezone": "auto",
        }
    )
    url = f"{base}/v1/forecast?{qs}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SpotMap/0.3 (weather; local-dev)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        payload = empty_weather_payload(reason=f"провайдер недоступен: {type(exc).__name__}")
        payload["wind_layer"] = wind_layer_status()
        return payload

    current = raw.get("current") or {}
    hourly = raw.get("hourly") or {}
    times = hourly.get("time") or []
    hours: list[dict[str, Any]] = []
    for i, t in enumerate(times[:24]):
        hours.append(
            {
                "at": t,
                "air_c": _num(hourly.get("temperature_2m"), i),
                "wind_mps": _num(hourly.get("wind_speed_10m"), i),
                "direction_from_deg": _num(hourly.get("wind_direction_10m"), i),
                "gust_mps": _num(hourly.get("wind_gusts_10m"), i),
                "precipitation_mm": _num(hourly.get("precipitation"), i),
            }
        )

    payload = {
        "status": "ok",
        "reason": None,
        "provider": "open-meteo",
        "observed_or_forecast_at": current.get("time"),
        "updated_at": current.get("time"),
        "air_c": current.get("temperature_2m"),
        "wind_mps": current.get("wind_speed_10m"),
        "direction_from_deg": current.get("wind_direction_10m"),
        "gust_mps": current.get("wind_gusts_10m"),
        "precipitation_mm": current.get("precipitation"),
        "water_c": None,
        "water_status": "no_measurement",
        "water_reason": "Нет свежего измерения температуры воды",
        "hourly": hours,
        "cached": False,
        "license_note": (
            "Open-Meteo pilot for non-commercial/dev. Commercial use needs customer-api license."
        ),
    }
    _cache_set(key, payload)
    out = dict(payload)
    out["wind_layer"] = wind_layer_status()
    return out


def _num(series: Any, index: int) -> float | None:
    if not isinstance(series, list) or index >= len(series):
        return None
    value = series[index]
    return value if isinstance(value, (int, float)) else None


def attach_water_observation(conn, spot_id: str, weather: dict[str, Any]) -> dict[str, Any]:
    """Overlay latest non-expired water measurement if present."""
    out = dict(weather)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT water_c, measured_at, source, confidence, depth_m, location_note
                FROM water_temperature_observations
                WHERE spot_id = %s::uuid
                  AND (expires_at IS NULL OR expires_at > now())
                ORDER BY measured_at DESC
                LIMIT 1
                """,
                (spot_id,),
            )
            row = cur.fetchone()
    except Exception:  # noqa: BLE001 — table may not exist yet
        return out
    if not row:
        return out
    cols = ["water_c", "measured_at", "source", "confidence", "depth_m", "location_note"]
    data = dict(zip(cols, row))
    out["water_c"] = data["water_c"]
    out["water_status"] = "measured"
    out["water_reason"] = None
    out["water_source"] = data["source"]
    out["water_measured_at"] = (
        data["measured_at"].isoformat() if hasattr(data["measured_at"], "isoformat") else data["measured_at"]
    )
    out["water_confidence"] = data["confidence"]
    out["water_depth_m"] = data["depth_m"]
    return out
