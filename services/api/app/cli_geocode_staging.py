"""CLI wrapper for staging address geocode."""

from __future__ import annotations

import argparse
import sys

from .config import settings
from .db import get_connection
from .geocode_staging import run_address_geocode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geocode staging candidates (approximate only).")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--sleep", type=float, default=1.1)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--provider", choices=("auto", "nominatim", "yandex"), default="auto")
    args = parser.parse_args(argv)

    provider = "nominatim" if args.provider == "auto" else args.provider
    if provider == "yandex" and not (settings.yandex_maps_api_key or "").strip():
        print("ERROR: YANDEX_MAPS_API_KEY empty", file=sys.stderr)
        return 2

    with get_connection() as conn:
        stats = run_address_geocode(
            conn,
            provider=provider,
            force=args.force,
            limit=args.limit,
            sleep_s=args.sleep,
            yandex_api_key=(settings.yandex_maps_api_key or "").strip(),
            progress=True,
        )
    print(f"done {stats}")
    print("NOTE: approximate only; not verified/published.")
    return 0 if stats["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
