"""Verified booking outbound redirects. Click ≠ confirmed booking."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlparse

_HTTPS_RE = re.compile(r"^https://", re.I)


def is_safe_target_url(url: str, *, https_only: bool = True) -> bool:
    raw = (url or "").strip()
    if not raw or raw.startswith("//") or "\\" in raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return False
    if https_only and parsed.scheme != "https":
        # Allow http only for known local/dev club sites already stored historically.
        # Production seed should prefer https; callers pass https_only=False for legacy http.
        return False
    if not parsed.netloc or parsed.username or parsed.password:
        return False
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1"} or host.endswith(".local"):
        return False
    return True


def hash_ip(ip: str | None, salt: str) -> str | None:
    if not ip:
        return None
    material = f"{salt}:{ip.strip()}".encode()
    return hashlib.sha256(material).hexdigest()[:32]


def ensure_booking_link(conn, *, spot_id: str, target_url: str, label: str = "Записаться у клуба") -> str | None:
    """Upsert active verified link; returns link id or None if URL unsafe."""
    url = (target_url or "").strip()
    # Prefer https; allow historical http club sites with flag.
    https_ok = is_safe_target_url(url, https_only=True)
    http_ok = is_safe_target_url(url, https_only=False) and url.lower().startswith("http://")
    if not https_ok and not http_ok:
        return None
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO verified_booking_links (spot_id, target_url, label, https_only, is_active)
            VALUES (%s::uuid, %s, %s, %s, true)
            ON CONFLICT (spot_id, target_url) DO UPDATE SET
              label = EXCLUDED.label,
              is_active = true,
              verified_at = now()
            RETURNING id::text
            """,
            (spot_id, url, label, https_ok),
        )
        row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return str(row.get("id"))
    return str(row[0])


def get_active_link(conn, link_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, spot_id::text, target_url, label, https_only, is_active
            FROM verified_booking_links
            WHERE id = %s::uuid AND is_active = true
            """,
            (link_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    if isinstance(row, dict):
        return {
            "id": str(row["id"]),
            "spot_id": str(row["spot_id"]),
            "target_url": row["target_url"],
            "label": row["label"],
            "https_only": row["https_only"],
            "is_active": row["is_active"],
        }
    cols = ["id", "spot_id", "target_url", "label", "https_only", "is_active"]
    return dict(zip(cols, row))


def record_click(
    conn,
    *,
    link: dict[str, Any],
    referrer: str | None,
    user_agent: str | None,
    embed_host: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    ip_hash: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO outbound_booking_clicks (
              booking_link_id, spot_id, referrer, user_agent, embed_host,
              utm_source, utm_medium, utm_campaign, ip_hash
            ) VALUES (
              %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                link["id"],
                link["spot_id"],
                (referrer or "")[:500] or None,
                (user_agent or "")[:400] or None,
                (embed_host or "")[:80] or None,
                (utm_source or "")[:80] or None,
                (utm_medium or "")[:80] or None,
                (utm_campaign or "")[:120] or None,
                ip_hash,
            ),
        )


def booking_go_href(link_id: str | None) -> str | None:
    if not link_id:
        return None
    return f"/go/{link_id}"
