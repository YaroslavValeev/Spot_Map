"""CLI: import local staging CSV into disposable PostGIS. Never publishes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .db import get_connection
from .staging_import import import_rows_to_db, load_staging_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import SpotMap staging candidates (draft only).")
    parser.add_argument("csv_path", type=Path, help="Path to local staging CSV (gitignored).")
    parser.add_argument(
        "--kind",
        choices=("auto", "spots", "cable"),
        default="auto",
        help="CSV flavor. auto detects cable vs spots.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and dedupe only; do not write to DB.",
    )
    args = parser.parse_args(argv)

    if not args.csv_path.is_file():
        print(f"ERROR: file not found: {args.csv_path}", file=sys.stderr)
        return 2

    rows = load_staging_csv(args.csv_path, kind=args.kind)
    print(f"parsed={len(rows)} kind={args.kind} file={args.csv_path}")
    if args.dry_run:
        from .staging_import import dedupe_rows

        unique, dupes = dedupe_rows(rows)
        print(f"dry_run unique={len(unique)} in_file_duplicates={dupes} published=0")
        return 0

    with get_connection() as conn:
        stats = import_rows_to_db(conn, rows)
    print(stats)
    print("NOTE: publication_status remains draft; map stays empty until geo verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
