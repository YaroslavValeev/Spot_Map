"""SpotMap Map API + minimal map UI — Sprint 01."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .db import get_connection
from .map_queries import fetch_map_points, fetch_staging_stats, rows_to_geojson
from .moderation import list_candidates, promote_candidate_with_geo

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="SpotMap API",
    version="0.2.0-sprint01",
    description=(
        "Map API + moderator staging tools. "
        "Pins require publication_status=published and geo_status=verified."
    ),
)


class PromoteGeoBody(BaseModel):
    latitude: float = Field(..., description="Verified WGS84 latitude from human review")
    longitude: float = Field(..., description="Verified WGS84 longitude from human review")
    evidence_note: str = Field(
        ...,
        min_length=8,
        description="How/where coordinates were verified (URL, visit date, map source)",
    )
    publish: bool = Field(
        default=False,
        description="If true, spot becomes visible on public map immediately",
    )


def _require_moderation_token(token: str | None) -> None:
    expected = (settings.moderation_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="moderation writes disabled: set MODERATION_TOKEN in .env",
        )
    if not token or token.strip() != expected:
        raise HTTPException(status_code=401, detail="invalid moderation token")


@app.get("/health")
def health() -> dict:
    payload = {"status": "ok", "app_env": settings.app_env}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        payload["database"] = "up"
    except Exception as exc:  # noqa: BLE001
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


@app.get("/v1/staging/candidates")
def staging_candidates(
    kind: str | None = Query(default=None),
    geo_status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Staging queue for moderators/UI. Not public map pins."""
    if kind and kind not in {"spot_or_club", "cable_installation", "other"}:
        raise HTTPException(status_code=400, detail="unknown candidate kind")
    if geo_status and geo_status not in {"missing", "approximate", "verified", "disputed"}:
        raise HTTPException(status_code=400, detail="unknown geo_status")
    try:
        with get_connection() as conn:
            return list_candidates(
                conn,
                kind=kind,
                geo_status=geo_status,
                limit=limit,
                offset=offset,
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc


@app.post("/v1/moderation/candidates/{candidate_id}/promote-geo")
def promote_geo(
    candidate_id: str,
    body: PromoteGeoBody,
    x_spotmap_moderation_token: str | None = Header(default=None),
):
    """Attach human-verified coordinates. Does not invent lat/lng."""
    _require_moderation_token(x_spotmap_moderation_token)
    try:
        with get_connection() as conn:
            return promote_candidate_with_geo(
                conn,
                candidate_id=candidate_id,
                latitude=body.latitude,
                longitude=body.longitude,
                evidence_note=body.evidence_note,
                publish=body.publish,
            )
    except KeyError:
        raise HTTPException(status_code=404, detail="candidate not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc


@app.get("/")
def map_ui():
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="map UI not built")
    return FileResponse(index)


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
