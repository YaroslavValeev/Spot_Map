"""Import SpotMap research xlsx into staging (approximate only, never verified/published)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

PROVIDER = "research_moscow_mo_2026-11-14"

UPSERT_SQL = """
INSERT INTO staging_candidates (
  legacy_row_id, fingerprint, raw_name, raw_region, raw_address,
  raw_segment, raw_category, raw_disciplines, candidate_kind,
  official_or_public_website, source_url, source_snapshot, source_sha256,
  geo_status, operation_status, publication_status
) VALUES (
  %(legacy_row_id)s, %(fingerprint)s, %(raw_name)s, %(raw_region)s, %(raw_address)s,
  %(raw_segment)s, %(raw_category)s, %(raw_disciplines)s, %(candidate_kind)s,
  %(website)s, %(source_url)s, %(source_snapshot)s, %(source_sha256)s,
  %(geo_status)s, 'unknown', 'draft'
)
ON CONFLICT (fingerprint) DO UPDATE SET
  raw_name = EXCLUDED.raw_name,
  raw_region = EXCLUDED.raw_region,
  raw_address = EXCLUDED.raw_address,
  raw_disciplines = EXCLUDED.raw_disciplines,
  candidate_kind = EXCLUDED.candidate_kind,
  official_or_public_website = COALESCE(EXCLUDED.official_or_public_website, staging_candidates.official_or_public_website),
  source_url = COALESCE(EXCLUDED.source_url, staging_candidates.source_url),
  source_snapshot = EXCLUDED.source_snapshot,
  source_sha256 = EXCLUDED.source_sha256,
  geo_status = CASE
    WHEN staging_candidates.geo_status = 'verified' THEN staging_candidates.geo_status
    ELSE EXCLUDED.geo_status
  END,
  updated_at = now()
RETURNING id::text
"""

POINT_SQL = """
UPDATE staging_candidates
SET
  approx_point = ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
  approx_precision = %(precision)s,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE
    WHEN geo_status = 'verified' THEN geo_status
    ELSE 'approximate'
  END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""

CLEAR_SQL = """
UPDATE staging_candidates
SET
  approx_point = NULL,
  approx_precision = NULL,
  approx_geocode_query = %(query)s,
  approx_geocoded_at = now(),
  approx_geocode_provider = %(provider)s,
  geo_status = CASE
    WHEN geo_status = 'verified' THEN geo_status
    ELSE 'missing'
  END,
  updated_at = now()
WHERE id = %(id)s::uuid
  AND publication_status <> 'published'
"""

TAG_TO_KIND = {
    "CABLE_CIRCUIT": "cable_installation",
    "CABLE_REVERSE": "cable_installation",
    "CABLE_POOL": "cable_installation",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fingerprint(candidate_id: str, name: str) -> str:
    base = f"research:{candidate_id}:{name}".strip().lower()
    return _sha(base)


def _parse_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _candidate_kind(tags: str) -> str:
    parts = [p.strip().upper() for p in re.split(r"[;,|/]+", tags or "") if p.strip()]
    if any(p in TAG_TO_KIND for p in parts) and not any(
        p in {"WAKESURF", "WAKEBOARD_BOAT", "WATER_SKI"} for p in parts
    ):
        return "cable_installation"
    if parts and all(p.startswith("CABLE_") for p in parts):
        return "cable_installation"
    return "other"


def _precision(scope: str | None) -> str:
    s = (scope or "").lower()
    if "address" in s or "venue" in s or "official" in s:
        return "address"
    if "site" in s or "area" in s or "historical" in s:
        return "name_region"
    return "address"


def load_new_candidates(xlsx: Path) -> list[dict[str, Any]]:
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["Новые_кандидаты"]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c or "").strip() for c in rows[0]]
    out: list[dict[str, Any]] = []
    for raw in rows[1:]:
        if not raw or not raw[0]:
            continue
        item = {header[i]: raw[i] for i in range(min(len(header), len(raw)))}
        out.append(item)
    return out


def import_research_xlsx(conn, xlsx: Path, *, progress: bool = True) -> dict[str, Any]:
    rows = load_new_candidates(xlsx)
    inserted = updated_pts = cleared = skipped = 0

    for row in rows:
        cand_id = str(row.get("candidate_id") or "").strip()
        name = str(row.get("name") or "").strip()
        if not cand_id or not name:
            skipped += 1
            continue

        tags = str(row.get("discipline_tags") or "").strip()
        district = str(row.get("district") or "").strip() or None
        address = str(row.get("address_or_landmark") or "").strip() or None
        scope = str(row.get("coordinate_scope") or "").strip()
        evidence = str(row.get("evidence_level") or "").strip()
        status = str(row.get("research_status") or "").strip()
        note = str(row.get("note") or "").strip()
        src = str(row.get("primary_source_url") or "").strip() or None
        secondary = str(row.get("secondary_source_url") or "").strip() or None
        lat = _parse_float(row.get("latitude"))
        lng = _parse_float(row.get("longitude"))

        # Outside viewport / search-only without GPS stay in staging without map pin.
        map_ok = lat is not None and lng is not None and 41.0 <= lat <= 82.0 and 19.0 <= lng <= 180.0
        # Historical stadium: keep in staging with approx but mark via disciplines/note.
        snapshot = (
            f"research_status={status}; evidence={evidence}; scope={scope}; "
            f"match={row.get('match_existing')}; note={note}; secondary={secondary}"
        )[:2000]

        payload = {
            "legacy_row_id": cand_id,
            "fingerprint": _fingerprint(cand_id, name),
            "raw_name": name,
            "raw_region": district,
            "raw_address": address,
            "raw_segment": "research_2026-11-14",
            "raw_category": evidence or "research",
            "raw_disciplines": tags,
            "candidate_kind": _candidate_kind(tags),
            "website": secondary if secondary and secondary.startswith("http") else None,
            "source_url": src,
            "source_snapshot": snapshot,
            "source_sha256": _sha(snapshot),
            "geo_status": "approximate" if map_ok else "missing",
        }

        with conn.cursor() as cur:
            cur.execute(UPSERT_SQL, payload)
            sid = cur.fetchone()[0]
        conn.commit()
        inserted += 1

        if map_ok:
            with conn.cursor() as cur:
                cur.execute(
                    POINT_SQL,
                    {
                        "id": sid,
                        "lat": lat,
                        "lng": lng,
                        "precision": _precision(scope),
                        "query": f"research:{cand_id}:{scope or 'gps'}",
                        "provider": PROVIDER,
                    },
                )
            conn.commit()
            updated_pts += 1
            if progress:
                print(f"MAP {cand_id} {name}: {lat},{lng} [{tags}]")
        else:
            with conn.cursor() as cur:
                cur.execute(
                    CLEAR_SQL,
                    {
                        "id": sid,
                        "query": f"research:{cand_id}:no_gps:{scope or 'missing'}",
                        "provider": PROVIDER,
                    },
                )
            conn.commit()
            cleared += 1
            if progress:
                print(f"QUEUE {cand_id} {name}: no GPS ({status})")

    return {
        "rows": len(rows),
        "upserted": inserted,
        "with_map_point": updated_pts,
        "queued_no_gps": cleared,
        "skipped": skipped,
        "provider": PROVIDER,
    }
