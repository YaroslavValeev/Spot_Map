"""Load approved wind profiles and evaluate rideability — never invent a score."""

from __future__ import annotations

from typing import Any

from .spotmap_wind import suitability_for_hour


def not_configured_payload(reason: str = "Ветровой профиль не утверждён") -> dict[str, Any]:
    return {
        "status": "not_configured",
        "verdict": None,
        "label": "Не оценено",
        "reason": reason,
        "profile_version": None,
    }


def fetch_approved_profile(conn, *, spot_id: str, discipline_id: str | None = None) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        if discipline_id:
            cur.execute(
                """
                SELECT spot_id::text, discipline_id, approved, version, sectors, notes
                FROM wind_profiles
                WHERE spot_id = %s::uuid
                  AND discipline_id = %s
                  AND approved = true
                ORDER BY verified_at DESC NULLS LAST, updated_at DESC
                LIMIT 1
                """,
                (spot_id, discipline_id),
            )
        else:
            cur.execute(
                """
                SELECT spot_id::text, discipline_id, approved, version, sectors, notes
                FROM wind_profiles
                WHERE spot_id = %s::uuid AND approved = true
                ORDER BY verified_at DESC NULLS LAST, updated_at DESC
                LIMIT 1
                """,
                (spot_id,),
            )
        row = cur.fetchone()
    if not row:
        return None
    cols = ["spot_id", "discipline_id", "approved", "version", "sectors", "notes"]
    data = dict(zip(cols, row))
    sectors = data.get("sectors") or []
    if isinstance(sectors, str):
        import json

        sectors = json.loads(sectors)
    return {
        "spot_id": data["spot_id"],
        "discipline_id": data["discipline_id"],
        "approved": bool(data["approved"]),
        "version": data["version"],
        "sectors": sectors,
        "notes": data.get("notes"),
    }


def evaluate_spot_rideability(
    conn,
    *,
    spot_id: str,
    forecast: dict[str, Any] | None,
    discipline_id: str | None = None,
) -> dict[str, Any]:
    try:
        profile = fetch_approved_profile(conn, spot_id=spot_id, discipline_id=discipline_id)
    except Exception:  # noqa: BLE001 — migration may be pending
        return not_configured_payload("Таблица wind_profiles ещё не применена")
    if not profile:
        return not_configured_payload()
    forecast_hour = None
    if forecast and forecast.get("status") == "ok":
        forecast_hour = {
            "direction_from_deg": forecast.get("direction_from_deg"),
            "wind_mps": forecast.get("wind_mps"),
            "gust_mps": forecast.get("gust_mps"),
        }
    result = suitability_for_hour(profile, forecast_hour)
    label_map = {
        "excellent": "Отлично",
        "good": "Хорошо",
        "limited": "Ограничено",
        "unsuitable": "Не подходит",
    }
    verdict = result.get("verdict")
    return {
        **result,
        "label": label_map.get(verdict) if verdict else "Не оценено",
    }
