"""CLI: python -m app.cli_apply_owner_registry --csv PATH"""

from __future__ import annotations

import argparse
from pathlib import Path

from .apply_owner_registry import apply_owner_corrections, apply_owner_registry
from .db import get_connection

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = (
    ROOT
    / "data"
    / "imports"
    / "SpotMap_86_Locations_Final_2026-11-14"
    / "SpotMap_86_Registry_2026-11-14"
    / "data"
    / "staging"
    / "SpotMap_Master_86_2026-11-14.csv"
)
DEFAULT_CORRECTIONS = ROOT / "data" / "imports" / "owner_corrections_2026-11-14.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply owner research registry to staging")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--corrections", type=Path, default=DEFAULT_CORRECTIONS)
    args = parser.parse_args()
    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")

    with get_connection() as conn:
        stats = apply_owner_registry(conn, args.csv, progress=True)
        corr = apply_owner_corrections(conn, args.corrections, progress=True)
    print(stats)
    print(corr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
