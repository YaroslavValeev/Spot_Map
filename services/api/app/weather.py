"""WeatherProvider — MET Norway preferred, Open-Meteo fallback. No invented water temp."""

from __future__ import annotations

import json
import math
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import settings

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:  # noqa: BLE001
    _SSL_CONTEXT = ssl.create_default_context()

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


def weather_user_agent() -> str:
    """MET Norway requires identifiable UA with contact (CC BY / ToS)."""
    contact = (settings.weather_met_norway_contact or "").strip()
    if not contact:
        contact = "SpotMap https://mywavewake.ru y.valeev@gmail.com"
    return f"SpotMap/0.4 ({contact})"


def wind_layer_status() -> dict[str, Any]:
    """Free path A: vector arrows from point forecasts (not paid weather tiles)."""
    mode = (settings.weather_wind_layer_mode or "arrows_grid").strip().lower()
    if mode in {"arrows_grid", "a", "arrows"}:
        return {
            "enabled": True,
            "mode": "arrows_grid",
            "label": "Ветер — стрелки",
            "reason": None,
            "provider": "met_norway_or_open_meteo_grid",
        }
    return {
        "enabled": False,
        "mode": mode or "disabled",
        "label": "Ветровой слой недоступен",
        "reason": "Режим слоя выключен (WEATHER_WIND_LAYER_MODE)",
        "provider": None,
    }


def empty_weather_payload(*, reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "provider": None,
        "attribution": None,
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


def _num(series: Any, index: int) -> float | None:
    if not isinstance(series, list) or index >= len(series):
        return None
    value = series[index]
    return float(value) if isinstance(value, (int, float)) else None


def _http_json(url: str, *, timeout: float = 12) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": weather_user_agent()})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode())


def _fetch_open_meteo(lat: float, lon: float) -> dict[str, Any]:
    if not settings.weather_open_meteo_enabled:
        raise RuntimeError("open_meteo_disabled")
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
    raw = _http_json(f"{base}/v1/forecast?{qs}")
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
    return {
        "status": "ok",
        "reason": None,
        "provider": "open-meteo",
        "attribution": "Weather data from Open-Meteo.com (CC BY 4.0)",
        "license_note": (
            "Open-Meteo fallback. Non-commercial free tier; commercial may need customer-api."
        ),
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
    }


def _met_details(entry: dict[str, Any]) -> dict[str, Any]:
    return (entry.get("data") or {}).get("instant", {}).get("details") or {}


def _fetch_met_norway(lat: float, lon: float) -> dict[str, Any]:
    if not settings.weather_met_norway_enabled:
        raise RuntimeError("met_norway_disabled")
    base = (settings.weather_met_norway_base_url or "https://api.met.no").rstrip("/")
    qs = urllib.parse.urlencode({"lat": f"{lat:.4f}", "lon": f"{lon:.4f}"})
    raw = _http_json(f"{base}/weatherapi/locationforecast/2.0/compact?{qs}")
    series = ((raw.get("properties") or {}).get("timeseries") or [])
    if not series:
        raise RuntimeError("met_norway_empty")
    now = series[0]
    details = _met_details(now)
    hours: list[dict[str, Any]] = []
    for entry in series[:24]:
        d = _met_details(entry)
        next1 = ((entry.get("data") or {}).get("next_1_hours") or {}).get("details") or {}
        hours.append(
            {
                "at": entry.get("time"),
                "air_c": d.get("air_temperature"),
                "wind_mps": d.get("wind_speed"),
                "direction_from_deg": d.get("wind_from_direction"),
                "gust_mps": d.get("wind_speed_of_gust"),
                "precipitation_mm": next1.get("precipitation_amount"),
            }
        )
    return {
        "status": "ok",
        "reason": None,
        "provider": "met-norway",
        "attribution": "Weather forecast from the Norwegian Meteorological Institute (MET Norway), CC BY 4.0",
        "license_note": "https://api.met.no/doc/License.html — attribution required",
        "observed_or_forecast_at": now.get("time"),
        "updated_at": ((raw.get("properties") or {}).get("meta") or {}).get("updated_at")
        or now.get("time"),
        "air_c": details.get("air_temperature"),
        "wind_mps": details.get("wind_speed"),
        "direction_from_deg": details.get("wind_from_direction"),
        "gust_mps": details.get("wind_speed_of_gust"),
        "precipitation_mm": (
            ((now.get("data") or {}).get("next_1_hours") or {}).get("details") or {}
        ).get("precipitation_amount"),
        "water_c": None,
        "water_status": "no_measurement",
        "water_reason": "Нет свежего измерения температуры воды",
        "hourly": hours,
        "cached": False,
    }


def forecast_point(lat: float, lon: float) -> dict[str, Any]:
    """Preferred MET Norway, fallback Open-Meteo. Water never inferred from air."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("lat/lon out of range")

    preferred = (settings.weather_provider or "met_norway").strip().lower()
    key = f"wx:{preferred}:{lat:.4f}:{lon:.4f}"
    cached = _cache_get(key)
    if cached:
        out = dict(cached)
        out["cached"] = True
        out["wind_layer"] = wind_layer_status()
        return out

    errors: list[str] = []
    order = ["met_norway", "open_meteo"] if preferred.startswith("met") else ["open_meteo", "met_norway"]
    # Always try preferred first then the other enabled provider.
    tried: set[str] = set()
    payload: dict[str, Any] | None = None
    for name in order:
        if name in tried:
            continue
        tried.add(name)
        try:
            if name == "met_norway":
                payload = _fetch_met_norway(lat, lon)
            else:
                payload = _fetch_open_meteo(lat, lon)
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}:{type(exc).__name__}")
            payload = None

    if payload is None:
        out = empty_weather_payload(reason="провайдеры недоступны: " + ", ".join(errors) or "unknown")
        out["wind_layer"] = wind_layer_status()
        return out

    _cache_set(key, payload)
    out = dict(payload)
    out["wind_layer"] = wind_layer_status()
    if errors:
        out["fallback_note"] = "tried: " + ", ".join(errors)
    return out


def wind_grid(
    *,
    min_lat: float,
    min_lng: float,
    max_lat: float,
    max_lng: float,
    step: float = 0.35,
) -> dict[str, Any]:
    """Sparse wind vectors for free overlay A. Caps grid size to protect free APIs."""
    if step <= 0 or step > 2:
        raise ValueError("step out of range")
    if min_lat > max_lat or min_lng > max_lng:
        raise ValueError("bbox invalid")
    # Expand tiny bboxes slightly.
    if abs(max_lat - min_lat) < 0.05:
        min_lat -= 0.1
        max_lat += 0.1
    if abs(max_lng - min_lng) < 0.05:
        min_lng -= 0.1
        max_lng += 0.1

    lats: list[float] = []
    lat = min_lat
    while lat <= max_lat + 1e-9:
        lats.append(round(lat, 4))
        lat += step
    lngs: list[float] = []
    lng = min_lng
    while lng <= max_lng + 1e-9:
        lngs.append(round(lng, 4))
        lng += step
    # Cap cells (e.g. 5x5=25).
    while len(lats) * len(lngs) > 25 and step < 2:
        step = min(2.0, step * 1.4)
        lats = []
        lat = min_lat
        while lat <= max_lat + 1e-9:
            lats.append(round(lat, 4))
            lat += step
        lngs = []
        lng = min_lng
        while lng <= max_lng + 1e-9:
            lngs.append(round(lng, 4))
            lng += step
    lats = lats[:5]
    lngs = lngs[:5]

    points: list[dict[str, Any]] = []
    provider = None
    attribution = None
    for la in lats:
        for lo in lngs:
            wx = forecast_point(la, lo)
            if wx.get("status") != "ok":
                continue
            provider = wx.get("provider") or provider
            attribution = wx.get("attribution") or attribution
            direction = wx.get("direction_from_deg")
            speed = wx.get("wind_mps")
            if direction is None or speed is None:
                continue
            # Meteorological FROM degrees → math angle for arrow TO direction (+180).
            to_deg = (float(direction) + 180.0) % 360.0
            rad = math.radians(to_deg)
            points.append(
                {
                    "lat": la,
                    "lng": lo,
                    "wind_mps": float(speed),
                    "direction_from_deg": float(direction),
                    "u": math.sin(rad) * float(speed),
                    "v": math.cos(rad) * float(speed),
                }
            )
    return {
        "status": "ok" if points else "unavailable",
        "mode": "arrows_grid",
        "provider": provider,
        "attribution": attribution,
        "step_deg": step,
        "points": points,
        "wind_layer": wind_layer_status(),
    }


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
