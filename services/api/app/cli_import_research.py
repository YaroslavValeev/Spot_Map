"""CLI: python -m app.cli_import_research --xlsx PATH"""

from __future__ import annotations

import argparse
from pathlib import Path

from .db import get_connection
from .import_research_xlsx import import_research_xlsx

DEFAULT_XLSX = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "imports"
    / "SpotMap_Research_Moscow_MO_2026-11-14"
    / "SpotMap_Research_Moscow_MO_2026-11-14.xlsx"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import research xlsx into staging")
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    args = parser.parse_args()
    if not args.xlsx.is_file():
        raise SystemExit(f"xlsx not found: {args.xlsx}")

    try:
        import openpyxl  # noqa: F401
    except ImportError as exc:
        raise SystemExit("openpyxl required: pip install openpyxl") from exc

    with get_connection() as conn:
        stats = import_research_xlsx(conn, args.xlsx, progress=True)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
