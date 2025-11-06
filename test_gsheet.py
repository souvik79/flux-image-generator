"""test_gsheet.py
Quick utility to verify that the service-account credentials can read a Google
Sheet.  Usage:

    python test_gsheet.py --creds <google_service.json> \
                          --sheet-id <sheet_id> [--worksheet Sheet1]

It prints the first ten rows (as dicts) so you can confirm access.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

import gspread


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:  # type: ignore[override]
    p = argparse.ArgumentParser(description="Test Google Sheets access via service account")
    p.add_argument("--creds", required=True, help="Path to service_account.json")
    p.add_argument("--sheet-id", required=True, help="Spreadsheet ID (the long string in the URL)")
    p.add_argument("--worksheet", default="Sheet1", help="Worksheet/tab name (default: Sheet1)")
    return p.parse_args(argv)


def fetch_rows(creds: Path, sheet_id: str, worksheet: str) -> List[Dict[str, str]]:
    gc = gspread.service_account(filename=str(creds))
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet)
    return ws.get_all_records()


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    rows = fetch_rows(Path(args.creds), args.sheet_id, args.worksheet)

    if not rows:
        print("Worksheet is empty or cannot be read.")
        return

    print(f"Successfully fetched {len(rows)} row(s). Showing first 10:\n")
    for row in rows[:10]:
        print(row)


if __name__ == "__main__":
    main()
