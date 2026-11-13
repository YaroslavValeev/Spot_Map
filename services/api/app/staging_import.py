"""Safe staging CSV import: candidates only, never auto-publish, idempotent dedupe."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = value.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


ALLOWED_CANDIDATE_KINDS = frozenset({"spot_or_club", "cable_installation", "other"})
ALLOWED_GEO_STATUSES = frozenset({"missing", "approximate", "verified", "disputed"})
ALLOWED_OPERATION_STATUSES = frozenset(
    {
        "open",
        "seasonal_closed",
        "temporarily_closed",
        "permanently_closed",
        "planned",
        "unknown",
    }
)

# Raw staging vocab → schema CHECK values (never invent verified geo).
GEO_STATUS_ALIASES = {
    "requires_verification": "missing",
    "needs_verification": "missing",
    "unverified": "missing",
    "pending": "missing",
    "unknown": "missing",
    "none": "missing",
    "": "missing",
}
CANDIDATE_KIND_ALIASES = {
    "unclassified": "other",
    "unknown": "other",
    "spot": "spot_or_club",
    "club": "spot_or_club",
    "cable": "cable_installation",
    "installation": "cable_installation",
    "": "spot_or_club",
}


def normalize_candidate_kind(value: str | None, *, default: str = "spot_or_club") -> str:
    raw = (value or default).strip().lower()
    mapped = CANDIDATE_KIND_ALIASES.get(raw, raw)
    if mapped not in ALLOWED_CANDIDATE_KINDS:
        return "other"
    return mapped


def normalize_geo_status(value: str | None) -> str:
    raw = (value or "missing").strip().lower()
    mapped = GEO_STATUS_ALIASES.get(raw, raw)
    if mapped not in ALLOWED_GEO_STATUSES:
        # Never promote unknown labels to verified.
        return "missing"
    return mapped


def normalize_operation_status(value: str | None) -> str:
    raw = (value or "unknown").strip().lower()
    if raw not in ALLOWED_OPERATION_STATUSES:
        return "unknown"
    return raw


def candidate_fingerprint(
    *,
    legacy_row_id: str | None,
    raw_name: str,
    raw_region: str | None,
    candidate_kind: str,
) -> str:
    """Stable fingerprint for idempotent import. Prefer legacy_row_id when present."""
    if legacy_row_id and legacy_row_id.strip():
        base = f"legacy:{candidate_kind}:{legacy_row_id.strip()}"
    else:
        base = "|".join(
            [
                candidate_kind,
                normalize_text(raw_name),
                normalize_text(raw_region),
            ]
        )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StagingRow:
    legacy_row_id: str | None
    fingerprint: str
    raw_name: str
    raw_region: str | None
    raw_address: str | None
    raw_segment: str | None
    raw_category: str | None
    raw_disciplines: str | None
    candidate_kind: str
    official_or_public_website: str | None
    public_telegram_url: str | None
    source_url: str | None
    source_snapshot: str | None
    source_sha256: str | None
    geo_status: str
    operation_status: str

    def as_db_params(self) -> dict[str, Any]:
        return {
            "legacy_row_id": self.legacy_row_id,
            "fingerprint": self.fingerprint,
            "raw_name": self.raw_name,
            "raw_region": self.raw_region,
            "raw_address": self.raw_address,
            "raw_segment": self.raw_segment,
            "raw_category": self.raw_category,
            "raw_disciplines": self.raw_disciplines,
            "candidate_kind": self.candidate_kind,
            "official_or_public_website": self.official_or_public_website,
            "public_telegram_url": self.public_telegram_url,
            "source_url": self.source_url,
            "source_snapshot": self.source_snapshot,
            "source_sha256": self.source_sha256,
            "geo_status": self.geo_status or "missing",
            "operation_status": self.operation_status or "unknown",
            "publication_status": "draft",
        }


def _get(row: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        if key in row and row[key] is not None and str(row[key]).strip() != "":
            return str(row[key]).strip()
    return None


def parse_spot_candidate_row(row: dict[str, str]) -> StagingRow | None:
    raw_name = _get(row, "raw_name", "name")
    if not raw_name:
        return None
    kind = normalize_candidate_kind(_get(row, "candidate_kind"), default="spot_or_club")
    legacy = _get(row, "legacy_row_id")
    region = _get(row, "raw_region")
    fp = candidate_fingerprint(
        legacy_row_id=legacy,
        raw_name=raw_name,
        raw_region=region,
        candidate_kind=kind,
    )
    return StagingRow(
        legacy_row_id=legacy,
        fingerprint=fp,
        raw_name=raw_name,
        raw_region=region,
        raw_address=_get(row, "raw_address", "address_from_source"),
        raw_segment=_get(row, "raw_segment"),
        raw_category=_get(row, "raw_category"),
        raw_disciplines=_get(row, "raw_disciplines", "sport_terms_from_source"),
        candidate_kind=kind,
        official_or_public_website=_get(row, "official_or_public_website"),
        public_telegram_url=_get(row, "public_telegram_url"),
        source_url=_get(row, "source_url"),
        source_snapshot=_get(row, "source_snapshot"),
        source_sha256=_get(row, "source_sha256"),
        geo_status=normalize_geo_status(_get(row, "geo_status", "map_geo_status")),
        operation_status=normalize_operation_status(_get(row, "operation_status")),
    )


def parse_cable_candidate_row(row: dict[str, str]) -> StagingRow | None:
    raw_name = _get(row, "name", "raw_name")
    if not raw_name:
        return None
    legacy = _get(row, "legacy_row_id")
    region = None
    kind = "cable_installation"
    fp = candidate_fingerprint(
        legacy_row_id=legacy,
        raw_name=raw_name,
        raw_region=region,
        candidate_kind=kind,
    )
    return StagingRow(
        legacy_row_id=legacy,
        fingerprint=fp,
        raw_name=raw_name,
        raw_region=region,
        raw_address=_get(row, "address_from_source", "raw_address"),
        raw_segment=None,
        raw_category=None,
        raw_disciplines=_get(row, "sport_terms_from_source", "raw_disciplines"),
        candidate_kind=kind,
        official_or_public_website=None,
        public_telegram_url=None,
        source_url=_get(row, "source_url"),
        source_snapshot=_get(row, "verification_action"),
        source_sha256=None,
        geo_status=normalize_geo_status(_get(row, "map_geo_status", "geo_status")),
        operation_status=normalize_operation_status(_get(row, "operation_status")),
    )


def load_staging_csv(path: Path, *, kind: str = "auto") -> list[StagingRow]:
    """Load candidates from CSV. kind: auto|spots|cable."""
    rows: list[StagingRow] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        if kind == "auto":
            if "candidate_installations_quantity" in fieldnames or (
                "name" in fieldnames and "raw_name" not in fieldnames
            ):
                kind = "cable"
            else:
                kind = "spots"
        parser = parse_cable_candidate_row if kind == "cable" else parse_spot_candidate_row
        for raw in reader:
            parsed = parser(raw)
            if parsed is not None:
                rows.append(parsed)
    return rows


def dedupe_rows(rows: Iterable[StagingRow]) -> tuple[list[StagingRow], int]:
    """Keep first occurrence per fingerprint. Returns (unique_rows, duplicate_count)."""
    seen: set[str] = set()
    unique: list[StagingRow] = []
    dupes = 0
    for row in rows:
        if row.fingerprint in seen:
            dupes += 1
            continue
        seen.add(row.fingerprint)
        unique.append(row)
    return unique, dupes


UPSERT_SQL = """
INSERT INTO staging_candidates (
  legacy_row_id, fingerprint, raw_name, raw_region, raw_address, raw_segment,
  raw_category, raw_disciplines, candidate_kind, official_or_public_website,
  public_telegram_url, source_url, source_snapshot, source_sha256,
  geo_status, operation_status, publication_status
) VALUES (
  %(legacy_row_id)s, %(fingerprint)s, %(raw_name)s, %(raw_region)s, %(raw_address)s,
  %(raw_segment)s, %(raw_category)s, %(raw_disciplines)s, %(candidate_kind)s,
  %(official_or_public_website)s, %(public_telegram_url)s, %(source_url)s,
  %(source_snapshot)s, %(source_sha256)s, %(geo_status)s, %(operation_status)s,
  %(publication_status)s
)
ON CONFLICT (fingerprint) DO UPDATE SET
  raw_name = EXCLUDED.raw_name,
  raw_region = EXCLUDED.raw_region,
  raw_address = EXCLUDED.raw_address,
  raw_disciplines = EXCLUDED.raw_disciplines,
  source_url = EXCLUDED.source_url,
  geo_status = EXCLUDED.geo_status,
  operation_status = EXCLUDED.operation_status,
  updated_at = now()
-- publication_status is intentionally NOT updated: never auto-publish
RETURNING (xmax = 0) AS inserted
"""


def import_rows_to_db(conn, rows: list[StagingRow]) -> dict[str, int]:
    """Upsert candidates. Never sets publication_status to published."""
    unique, in_file_dupes = dedupe_rows(rows)
    inserted = 0
    updated = 0
    with conn.cursor() as cur:
        for row in unique:
            cur.execute(UPSERT_SQL, row.as_db_params())
            was_inserted = cur.fetchone()[0]
            if was_inserted:
                inserted += 1
            else:
                updated += 1
    conn.commit()
    return {
        "parsed": len(rows),
        "in_file_duplicates": in_file_dupes,
        "upserted": len(unique),
        "inserted": inserted,
        "updated": updated,
        "published": 0,
    }
