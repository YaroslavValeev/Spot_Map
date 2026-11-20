"""SpotMap Map API + minimal map UI — Sprint 01."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .booking_redirect import get_active_link, hash_ip, record_click
from .config import embed_frame_ancestors, settings
from .db import get_connection
from .map_queries import (
    fetch_map_points,
    fetch_staging_approx_points,
    fetch_staging_stats,
    merge_map_and_staging_rows,
    rows_to_geojson,
)
from .geocode_staging import run_address_geocode
from .moderation import (
    apply_region_centroids,
    list_candidates,
    promote_candidate_with_geo,
    save_approx_points,
)
from .public_places import fetch_public_place
from .weather import attach_water_observation, forecast_point, wind_layer_status
from .wind_eval import evaluate_spot_rideability

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


class ApproxPointIn(BaseModel):
    candidate_id: str
    latitude: float
    longitude: float
    query: str = ""
    precision: str = "address"
    provider: str = "yandex_js_geocode"


class ApproxCacheBody(BaseModel):
    points: list[ApproxPointIn] = Field(default_factory=list, max_length=200)


def _require_moderation_token(token: str | None) -> None:
    expected = (settings.moderation_token or "").strip()
    if not expected:
        raise HTTPException(
            status_code=403,
            detail="moderation writes disabled: set MODERATION_TOKEN in .env",
        )
    if not token or token.strip() != expected:
        raise HTTPException(status_code=401, detail="invalid moderation token")


@app.get("/v1/config/public")
def public_config() -> dict:
    """Non-secret UI config. Maps key is referrer-restricted in Yandex cabinet."""
    return {
        "map_provider": "yandex",
        "yandex_maps_api_key": settings.yandex_maps_api_key or "",
        "map_lang": "ru_RU",
        "default_center": [61.524, 105.318],
        "default_zoom": 3,
        "attribution": "Яндекс.Карты",
        "embed_hosts": ["mywave", "fvls"],
        "spot_score_ui": "pending",
        "weather": {
            "open_meteo_enabled": settings.weather_open_meteo_enabled,
            "wind_layer": wind_layer_status(),
        },
        "club_manage": {
            "moderator_telegram": "@MyWave23",
            "moderator_email": "y.valeev@gmail.com",
        },
    }


class ClubManageRequestBody(BaseModel):
    spot_id: str
    contact_email: str | None = None
    contact_telegram: str | None = None
    message: str | None = Field(default=None, max_length=2000)


@app.get("/v1/public/places/{place_id}")
def public_place(
    place_id: str,
    entity_type: str = Query(default="spot", description="spot | cable_installation"),
):
    """Passport-lite for club card. SpotScore always pending until formula evidence exists."""
    try:
        with get_connection() as conn:
            return fetch_public_place(conn, place_id=place_id, entity_type=entity_type)
    except KeyError:
        raise HTTPException(status_code=404, detail="place not found or not published") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc


@app.get("/v1/weather/point")
def weather_point(
    lat: float = Query(...),
    lon: float = Query(...),
    spot_id: str | None = Query(default=None),
):
    """Normalized air/wind forecast. Water only if measured observation exists."""
    try:
        payload = forecast_point(lat, lon)
        if spot_id:
            with get_connection() as conn:
                payload = attach_water_observation(conn, spot_id, payload)
                payload["rideability"] = evaluate_spot_rideability(
                    conn, spot_id=spot_id, forecast=payload
                )
        else:
            payload["rideability"] = {
                "status": "not_configured",
                "label": "Не оценено",
                "reason": "Нужен spot_id и утверждённый WindProfile",
            }
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/go/{link_id}")
def booking_go(
    link_id: str,
    request: Request,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    embed_host: str | None = None,
):
    """302 to verified club booking URL. Records outbound_booking_click only."""
    try:
        with get_connection() as conn:
            link = get_active_link(conn, link_id)
            if not link:
                raise HTTPException(status_code=404, detail="booking link not found")
            client = request.client.host if request.client else None
            record_click(
                conn,
                link=link,
                referrer=request.headers.get("referer"),
                user_agent=request.headers.get("user-agent"),
                embed_host=embed_host,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                ip_hash=hash_ip(client, settings.booking_click_ip_salt),
            )
            conn.commit()
            return RedirectResponse(url=link["target_url"], status_code=302)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"redirect unavailable: {type(exc).__name__}",
        ) from exc


@app.post("/v1/club/manage-request")
def club_manage_request(body: ClubManageRequestBody):
    """Queue claim/manage request for moderator — no auto-grant."""
    if not body.contact_email and not body.contact_telegram:
        raise HTTPException(status_code=400, detail="укажите email или telegram")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM spots WHERE id = %s::uuid AND publication_status = 'published'",
                    (body.spot_id,),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="spot not found")
                cur.execute(
                    """
                    INSERT INTO club_management_requests (
                      spot_id, contact_email, contact_telegram, message
                    ) VALUES (%s::uuid, %s, %s, %s)
                    RETURNING id::text, status
                    """,
                    (
                        body.spot_id,
                        (body.contact_email or "").strip() or None,
                        (body.contact_telegram or "").strip() or None,
                        (body.message or "").strip() or None,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return {
            "id": row[0],
            "status": row[1],
            "next": "Модератор свяжется: @MyWave23 / y.valeev@gmail.com",
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"request failed: {type(exc).__name__}",
        ) from exc


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
        description="Legacy single filter alias (wakesurf, wakeboard_cable, ...).",
    ),
    disciplines: str | None = Query(
        default=None,
        description="Comma-separated: waterski,wakesurf_skim,wakeboard,cable_ring,cable_reverse,cable_pool",
    ),
    include_staging: bool = Query(
        default=True,
        description="Include staging approximate geocoded pins (not verified).",
    ),
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Verified published pins + optional staging approximate preview."""
    from .disciplines import SLUGS

    min_lng = min_lat = max_lng = max_lat = None
    if bbox:
        parts = [p.strip() for p in bbox.split(",")]
        if len(parts) != 4:
            raise HTTPException(status_code=400, detail="bbox must be minLng,minLat,maxLng,maxLat")
        try:
            min_lng, min_lat, max_lng, max_lat = (float(p) for p in parts)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="bbox values must be numbers") from exc

    legacy_ok = {
        "wakesurf",
        "wakeskim",
        "wakeboard_cable",
        "wakeboard_boat",
        "wakeskate_cable",
        "waterski_boat",
        "waterski_cable",
        *SLUGS,
    }
    if discipline and discipline not in legacy_ok:
        raise HTTPException(status_code=400, detail="unknown discipline slug")

    discipline_list: list[str] = []
    if disciplines:
        discipline_list = [p.strip() for p in disciplines.split(",") if p.strip()]
        bad = [d for d in discipline_list if d not in SLUGS]
        if bad:
            raise HTTPException(status_code=400, detail=f"unknown disciplines: {bad}")

    try:
        with get_connection() as conn:
            rows = fetch_map_points(
                conn,
                min_lng=min_lng,
                min_lat=min_lat,
                max_lng=max_lng,
                max_lat=max_lat,
                discipline=discipline,
                disciplines=discipline_list or None,
                limit=limit,
            )
            if include_staging:
                staging_rows = fetch_staging_approx_points(
                    conn,
                    min_lng=min_lng,
                    min_lat=min_lat,
                    max_lng=max_lng,
                    max_lat=max_lat,
                    discipline=discipline,
                    disciplines=discipline_list or None,
                    limit=limit,
                )
                rows = merge_map_and_staging_rows(rows, staging_rows)
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


@app.post("/v1/staging/approx-cache")
def staging_approx_cache(body: ApproxCacheBody):
    """Store browser/JS geocoder approximate points. Never sets verified/published."""
    if not body.points:
        return {"saved": 0, "skipped": 0}
    try:
        with get_connection() as conn:
            return save_approx_points(
                conn,
                [p.model_dump() for p in body.points],
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc


@app.post("/v1/staging/approx-from-regions")
def staging_approx_from_regions(force: bool = Query(default=False)):
    """Fallback: map staging rows to known RF region centroids (approximate only)."""
    try:
        with get_connection() as conn:
            return apply_region_centroids(conn, force=force)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {type(exc).__name__}",
        ) from exc


@app.post("/v1/staging/approx-geocode-addresses")
def staging_approx_geocode_addresses(
    force: bool = Query(default=True),
    provider: str = Query(default="nominatim"),
):
    """Geocode staging by street address (RU). Long-running; approximate only."""
    if provider not in {"nominatim", "yandex"}:
        raise HTTPException(status_code=400, detail="provider must be nominatim|yandex")
    try:
        with get_connection() as conn:
            return run_address_geocode(
                conn,
                provider=provider,
                force=force,
                limit=200,
                sleep_s=1.1 if provider == "nominatim" else 0.2,
                yandex_api_key=(settings.yandex_maps_api_key or "").strip(),
                progress=False,
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"geocode failed: {type(exc).__name__}",
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


@app.get("/embed")
def embed_ui(host: str = Query(default="mywave")):
    """Embeddable map UI (iframe). No moderator queue."""
    embed = STATIC_DIR / "embed.html"
    if not embed.is_file():
        raise HTTPException(status_code=404, detail="embed UI not built")
    theme = host if host in {"mywave", "fvls"} else "mywave"
    response = FileResponse(embed)
    response.headers["Content-Security-Policy"] = (
        f"frame-ancestors {embed_frame_ancestors()};"
    )
    # Hint for static JS theme (also readable from query by the page itself).
    response.headers["X-SpotMap-Embed-Host"] = theme
    return response


@app.middleware("http")
async def embed_cors_headers(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path.startswith("/v1/public/") or request.url.path.startswith("/v1/map/"):
        origin = request.headers.get("origin")
        allowed = {
            h.strip().lower()
            for h in (settings.embed_allowed_hosts or "").split(",")
            if h.strip()
        }
        if origin:
            # Reflect only allowlisted origins (scheme://host[:port]).
            try:
                from urllib.parse import urlparse

                host = (urlparse(origin).hostname or "").lower()
                if host in allowed or host.endswith(".mywavewake.ru"):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Vary"] = "Origin"
            except Exception:  # noqa: BLE001
                pass
    return response


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
