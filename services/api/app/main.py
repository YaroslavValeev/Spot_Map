"""SpotMap read-only Map API — Sprint 01 vertical slice."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .config import settings
from .db import get_connection
from .map_queries import fetch_map_points, fetch_staging_stats, rows_to_geojson

app = FastAPI(
    title="SpotMap API",
    version="0.1.0-sprint01",
    description="Read-only geo API. Pins require publication_status=published and geo_status=verified.",
)


@app.get("/health")
def health() -> dict:
    payload = {"status": "ok", "app_env": settings.app_env}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        payload["database"] = "up"
    except Exception as exc:  # noqa: BLE001 — surface connectivity for ops
        payload["status"] = "degraded"
        payload["database"] = "down"
        payload["database_error"] = type(exc).__name__
    return payload


@app.get("/v1/map/points")
def map_points(
    bbox: str | None = Query(
        default=None,
        description="minLng,minLat,maxLng,maxLat (WGS84). Optional.",
    ),
    discipline: str | None = Query(
        default=None,
        description="Optional filter: wakesurf | wakeboard_cable | ...",
    ),
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Public map pins only. Staging candidates never appear here."""
    min_lng = min_lat = max_lng = max_lat = None
    if bbox:
        parts = [p.strip() for p in bbox.split(",")]
        if len(parts) != 4:
            raise HTTPException(status_code=400, detail="bbox must be minLng,minLat,maxLng,maxLat")
        try:
            min_lng, min_lat, max_lng, max_lat = (float(p) for p in parts)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="bbox values must be numbers") from exc

    if discipline and discipline not in {
        "wakesurf",
        "wakeskim",
        "wakeboard_cable",
        "wakeboard_boat",
        "wakeskate_cable",
        "waterski_boat",
        "waterski_cable",
    }:
        raise HTTPException(status_code=400, detail="unknown discipline slug")

    try:
        with get_connection() as conn:
            rows = fetch_map_points(
                conn,
                min_lng=min_lng,
                min_lat=min_lat,
                max_lng=max_lng,
                max_lat=max_lat,
                discipline=discipline,
                limit=limit,
            )
            stats = fetch_staging_stats(conn)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc

    return rows_to_geojson(rows, meta=stats)


@app.get("/v1/staging/stats")
def staging_stats():
    """Moderator-oriented counters. No PII, no candidate names."""
    try:
        with get_connection() as conn:
            return fetch_staging_stats(conn)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc
