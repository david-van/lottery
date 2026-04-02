"""Normalized CSV reader and writer with schema enforcement."""

import csv
from typing import List, Optional

from src.config import ensure_data_dir
from src.models import NORMALIZED_FIELDS, NormalizedOddsRow


class SchemaError(Exception):
    """Raised when CSV schema doesn't match the expected normalized fields."""


def write_normalized_csv(rows: List[NormalizedOddsRow], path) -> None:
    """Write normalized odds rows to CSV with explicit column order."""
    ensure_data_dir()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=NORMALIZED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_normalized_csv(path, *, match_id: Optional[int] = None) -> List[dict]:
    """Read normalized CSV back as list of dicts.

    Validates that all required columns exist.
    Optionally filter by match_id.
    """
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Validate schema
        if reader.fieldnames is None:
            raise SchemaError("CSV file is empty or has no headers")
        missing = set(NORMALIZED_FIELDS) - set(reader.fieldnames)
        if missing:
            raise SchemaError(f"Missing required columns: {sorted(missing)}")

        rows = list(reader)

    if match_id is not None:
        rows = [r for r in rows if str(r.get("match_id")) == str(match_id)]

    return rows
