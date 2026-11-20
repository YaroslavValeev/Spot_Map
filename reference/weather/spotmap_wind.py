"""SpotMap wind evaluation core. No weather requests or invented profiles.

The input direction is meteorological FROM direction in degrees (0=N, 90=E).
Profile is always hand approved. A profile without manual rules produces NO score.
"""
from __future__ import annotations

from typing import Any

VALID_VERDICTS = {"excellent", "good", "limited", "unsuitable"}


def angular_sector_match(direction_from_deg: float, start_deg: float, end_deg: float) -> bool:
    """Inclusive circular arc, including sectors crossing north (e.g. 315..45)."""
    for n in (direction_from_deg, start_deg, end_deg):
        if not isinstance(n, (int, float)) or not (0 <= n <= 360):
            raise ValueError("Wind angles must be numbers from 0 to 360")
    direction, start, end = (direction_from_deg % 360, start_deg % 360, end_deg % 360)
    if start == end:
        # Deliberately no implicit full-circle interpretation: ambiguous manual input.
        return direction == start
    return start <= direction <= end if start < end else direction >= start or direction <= end


def suitability_for_hour(profile: dict[str, Any] | None, forecast: dict[str, Any] | None) -> dict[str, Any]:
    """Returns an explanatory status, not a fake numerical SpotScore.

    Expected profile keys: approved, sectors[], discipline_id, spot_id, version.
    Each sector has from_deg, to_deg, verdict, max_wind_mps?, max_gust_mps?.
    Evaluate one spot + one discipline + one forecast hour independently.
    Do not use this function to issue safety permissions for activities.
    """
    if not profile or not profile.get("approved") or not profile.get("sectors"):
        return {"status": "not_configured", "verdict": None, "reason": "Ветровой профиль не утверждён"}
    if not forecast or any(forecast.get(k) is None for k in ("direction_from_deg", "wind_mps")):
        return {"status": "missing_forecast", "verdict": None, "reason": "Недостаточно погодных данных"}
    direction = forecast["direction_from_deg"]
    if not isinstance(direction, (int, float)) or not 0 <= direction <= 360:
        return {"status": "invalid_forecast", "verdict": None, "reason": "Некорректное направление ветра"}
    wind = forecast["wind_mps"]
    gust = forecast.get("gust_mps")
    if not isinstance(wind, (int, float)) or wind < 0:
        return {"status": "invalid_forecast", "verdict": None, "reason": "Некорректная скорость ветра"}
    if gust is not None and (not isinstance(gust, (int, float)) or gust < 0):
        return {"status": "invalid_forecast", "verdict": None, "reason": "Некорректные порывы"}
    matched = []
    for i, sector in enumerate(profile["sectors"]):
        try:
            is_match = angular_sector_match(direction, sector["from_deg"], sector["to_deg"])
        except (ValueError, KeyError, TypeError):
            return {"status": "invalid_profile", "verdict": None, "reason": "Ошибка ветрового профиля"}
        if is_match:
            matched.append((i, sector))
    if len(matched) != 1:
        # Overlapping or missing rules should be reviewed, never guessed.
        return {"status": "ambiguous_profile" if matched else "no_rule_for_direction", "verdict": None, "reason": "Сектор не определён однозначно"}
    index, sector = matched[0]
    verdict = sector.get("verdict")
    if verdict not in VALID_VERDICTS:
        return {"status": "invalid_profile", "verdict": None, "reason": "Для сектора не задана оценка"}
    max_wind, max_gust = sector.get("max_wind_mps"), sector.get("max_gust_mps")
    if max_wind is not None and (not isinstance(max_wind, (int, float)) or max_wind < 0):
        return {"status": "invalid_profile", "verdict": None, "reason": "Некорректный предел ветра"}
    if max_gust is not None and (not isinstance(max_gust, (int, float)) or max_gust < 0):
        return {"status": "invalid_profile", "verdict": None, "reason": "Некорректный предел порывов"}
    if max_gust is not None and gust is None:
        return {"status": "missing_forecast", "verdict": None, "reason": "Нет прогноза порывов"}
    if (max_wind is not None and wind > max_wind) or (max_gust is not None and gust > max_gust):
        verdict = "unsuitable"
    return {
        "status": "estimated",
        "verdict": verdict,
        "sector_index": index,
        "profile_version": profile.get("version"),
        "reason": sector.get("note", "Экспертная настройка ветрового сектора"),
        "source": "manual_profile_plus_forecast",
    }
