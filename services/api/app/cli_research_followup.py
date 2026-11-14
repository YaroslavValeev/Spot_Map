"""CLI: python -m app.cli_research_followup"""

from __future__ import annotations

import argparse
from pathlib import Path

from .db import get_connection
from .research_followup import (
    apply_corrections,
    flag_possible_duplicates,
    geocode_new_with_addresses,
)

DEFAULT_XLSX = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "imports"
    / "SpotMap_Research_Moscow_MO_2026-11-14"
    / "SpotMap_Research_Moscow_MO_2026-11-14.xlsx"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--skip-geocode", action="store_true")
    args = parser.parse_args()
    if not args.xlsx.is_file():
        raise SystemExit(f"missing {args.xlsx}")

    with get_connection() as conn:
        print(apply_corrections(conn, args.xlsx))
        print(flag_possible_duplicates(conn))
        if not args.skip_geocode:
            print(geocode_new_with_addresses(conn, progress=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
