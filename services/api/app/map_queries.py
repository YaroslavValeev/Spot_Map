"""Map queries: verified published pins + optional staging approximate preview."""

from __future__ import annotations

from typing import Any

from .disciplines import (
    CABLE_SLUGS,
    DISCIPLINE_CATALOG,
    FILTER_ALIASES,
    count_disciplines,
    enrich_row_disciplines,
    expand_filter_selection,
    row_matches_discipline_filter,
)


# Spot + cable_installation from the same promote share identical coords/name.
# Map shows one pin: keep the installation (cable disciplines), hide parent spot.
# Discipline tags come from merged staging when available; never invent scores.
# Fallback to name/address so ring/reverse keywords in titles still classify.
MAP_POINTS_SQL_BASELINE = """
SELECT
  s.id::text AS id,
  'spot'::text AS entity_type,
  'verified'::text AS pin_kind,
  s.display_name AS name,
  s.operation_status,
  s.geo_status,
  NULL::text AS approx_precision,
  COALESCE(
    (
      SELECT sc.raw_disciplines
      FROM staging_candidates sc
      WHERE sc.publication_status = 'merged'
        AND lower(trim(sc.raw_name)) = lower(trim(s.display_name))
      ORDER BY sc.updated_at DESC NULLS LAST
      LIMIT 1
    ),
    s.display_name
  ) AS raw_disciplines,
  s.address_text AS raw_address,
  ST_Y(s.point::geometry) AS lat,
  ST_X(s.point::geometry) AS lng
FROM spots s
WHERE s.publication_status = 'published'
  AND s.geo_status = 'verified'
  AND s.point IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM cable_installations c
    WHERE c.spot_id = s.id
      AND c.publication_status = 'published'
      AND c.geo_status = 'verified'
      AND c.point IS NOT NULL
  )
  AND (
    %(min_lng)s::float8 IS NULL
    OR s.point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
UNION ALL
SELECT
  c.id::text AS id,
  'cable_installation'::text AS entity_type,
  'verified'::text AS pin_kind,
  c.name AS name,
  c.operation_status,
  c.geo_status,
  NULL::text AS approx_precision,
  COALESCE(
    (
      SELECT sc.raw_disciplines
      FROM staging_candidates sc
      WHERE sc.publication_status = 'merged'
        AND lower(trim(sc.raw_name)) = lower(trim(c.name))
      ORDER BY sc.updated_at DESC NULLS LAST
      LIMIT 1
    ),
    c.name || ' wakeboard cable'
  ) AS raw_disciplines,
  (
    SELECT s.address_text
    FROM spots s
    WHERE s.id = c.spot_id
  ) AS raw_address,
  ST_Y(c.point::geometry) AS lat,
  ST_X(c.point::geometry) AS lng
FROM cable_installations c
WHERE c.publication_status = 'published'
  AND c.geo_status = 'verified'
  AND c.point IS NOT NULL
  AND (
    %(min_lng)s::float8 IS NULL
    OR c.point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
ORDER BY 4
LIMIT %(limit)s
"""

STAGING_APPROX_SQL = """
SELECT
  sc.id::text AS id,
  sc.candidate_kind AS entity_type,
  'staging_approximate'::text AS pin_kind,
  sc.raw_name AS name,
  sc.operation_status,
  sc.geo_status,
  sc.approx_precision,
  sc.raw_disciplines,
  sc.raw_address,
  ST_Y(sc.approx_point::geometry) AS lat,
  ST_X(sc.approx_point::geometry) AS lng
FROM staging_candidates sc
WHERE sc.approx_point IS NOT NULL
  -- draft/pending only: hidden/merged must not reappear as map preview.
  AND sc.publication_status IN ('draft', 'pending')
  -- Closed venues must not reappear via staging preview.
  AND sc.operation_status <> 'permanently_closed'
  -- Region-centroid jitter is not a real place; hide from map layer.
  AND coalesce(sc.approx_geocode_provider, '') <> 'region_centroid_v1'
  AND (
    %(min_lng)s::float8 IS NULL
    OR sc.approx_point && ST_MakeEnvelope(%(min_lng)s, %(min_lat)s, %(max_lng)s, %(max_lat)s, 4326)::geography
  )
ORDER BY sc.raw_name
LIMIT %(limit)s
"""


def _normalize_selected(discipline: str | None, disciplines: list[str] | None) -> set[str]:
    selected: set[str] = set()
    if disciplines:
        selected.update(d for d in disciplines if d)
    if discipline:
        # Legacy + ADR-006 aliases.
        if discipline in {"wakesurf", "wakeskim"}:
            selected.add("wakesurf_skim")
        elif discipline == "wakeboard_boat":
            selected.add("wakeboard_boat")
        elif discipline == "wakeboard_cable":
            selected.update(CABLE_SLUGS)
            selected.add("wakeboard_cable")
        elif discipline in {"waterski_boat", "waterski_cable"}:
            selected.add("waterski")
        else:
            selected.add(discipline)
    return expand_filter_selection(selected)


def suppress_staging_near_verified(
    verified_rows: list[dict[str, Any]],
    staging_rows: list[dict[str, Any]],
    *,
    max_meters: float = 80.0,
) -> list[dict[str, Any]]:
    """Hide staging approx pins that sit on top of an already published verified pin."""
    # Rough degrees→meters at Moscow latitude (~55.7N).
    lat_m = 111_320.0
    lng_m = 62_500.0
    kept: list[dict[str, Any]] = []
    for st in staging_rows:
        slat = float(st["lat"])
        slng = float(st["lng"])
        too_close = False
        for vr in verified_rows:
            dlat = (slat - float(vr["lat"])) * lat_m
            dlng = (slng - float(vr["lng"])) * lng_m
            if (dlat * dlat + dlng * dlng) ** 0.5 <= max_meters:
                too_close = True
                break
        if not too_close:
            kept.append(st)
    return kept


def merge_map_and_staging_rows(
    verified_rows: list[dict[str, Any]],
    staging_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return verified_rows + suppress_staging_near_verified(verified_rows, staging_rows)


def fetch_map_points(
    conn,
    *,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    discipline: str | None = None,
    disciplines: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    params = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "limit": limit,
    }
    with conn.cursor() as cur:
        cur.execute(MAP_POINTS_SQL_BASELINE, params)
        cols = [d.name for d in cur.description]
        rows = [enrich_row_disciplines(dict(zip(cols, row))) for row in cur.fetchall()]
    selected = _normalize_selected(discipline, disciplines)
    return [r for r in rows if row_matches_discipline_filter(r, selected)]


def fetch_staging_approx_points(
    conn,
    *,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    discipline: str | None = None,
    disciplines: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    params = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "limit": limit,
    }
    with conn.cursor() as cur:
        cur.execute(STAGING_APPROX_SQL, params)
        cols = [d.name for d in cur.description]
        rows = [enrich_row_disciplines(dict(zip(cols, row))) for row in cur.fetchall()]
    selected = _normalize_selected(discipline, disciplines)
    return [r for r in rows if row_matches_discipline_filter(r, selected)]


def fetch_staging_stats(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              count(*)::int AS total,
              count(*) FILTER (WHERE geo_status = 'missing')::int AS geo_missing,
              count(*) FILTER (WHERE geo_status = 'approximate')::int AS geo_approximate,
              count(*) FILTER (WHERE approx_point IS NOT NULL)::int AS with_approx_point,
              count(*) FILTER (WHERE candidate_kind = 'cable_installation')::int AS cable_candidates
            FROM staging_candidates
            """
        )
        total, geo_missing, geo_approx, with_point, cable = cur.fetchone()
    return {
        "staging_total": total,
        "staging_geo_missing": geo_missing,
        "staging_geo_approximate": geo_approx,
        "staging_with_approx_point": with_point,
        "staging_cable_candidates": cable,
        "map_pins_policy": "verified_published_plus_optional_staging_approximate",
    }


def rows_to_geojson(rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    features = []
    verified = 0
    staging = 0
    for row in rows:
        pin_kind = row.get("pin_kind") or "verified"
        if pin_kind == "staging_approximate":
            staging += 1
        else:
            verified += 1
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["lng"]), float(row["lat"])],
                },
                "properties": {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "pin_kind": pin_kind,
                    "name": row["name"],
                    "address": row.get("raw_address") or None,
                    "operation_status": row["operation_status"],
                    "geo_status": row["geo_status"],
                    "approx_precision": row.get("approx_precision"),
                    "disciplines": row.get("disciplines") or [],
                    "primary_discipline": row.get("primary_discipline"),
                    "discipline_color": row.get("discipline_color"),
                    "discipline_symbol": row.get("discipline_symbol"),
                    "discipline_label": row.get("discipline_label"),
                },
            }
        )
    empty_reason = None
    if not features:
        empty_reason = "no_points"
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            **meta,
            "feature_count": len(features),
            "verified_count": verified,
            "staging_approx_count": staging,
            "empty_reason": empty_reason,
            "discipline_catalog": DISCIPLINE_CATALOG,
            "discipline_counts": count_disciplines(rows),
            "filter_aliases": {k: sorted(v) for k, v in FILTER_ALIASES.items()},
        },
    }
