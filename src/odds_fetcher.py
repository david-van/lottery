"""Odds detail fetch client and raw CSV writer."""

import csv
import json
from typing import List, Optional

import requests

from src.config import ODDS_DETAIL_API, DEFAULT_USER_AGENT, HTTP_TIMEOUT, ensure_data_dir
from src.models import RawOddsRow


class OddsFetchError(Exception):
    """Raised when an odds detail API request fails."""


def fetch_odds_detail(
    match_id: int,
    *,
    session: Optional[requests.Session] = None,
) -> dict:
    """Fetch odds detail for a single match. Returns parsed JSON dict."""
    s = session or requests.Session()
    params = {"clientCode": 3001, "matchId": match_id}
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        resp = s.get(ODDS_DETAIL_API, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        raise OddsFetchError(f"HTTP request failed for match {match_id}: {e}") from e

    if resp.status_code != 200:
        raise OddsFetchError(f"HTTP {resp.status_code} for match {match_id}")

    try:
        return resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise OddsFetchError(f"Invalid JSON for match {match_id}: {e}") from e


def validate_odds_payload(data: dict) -> bool:
    """Check if the odds payload has all required odds sections."""
    odds_history = data.get("value", {}).get("oddsHistory")
    if not odds_history:
        return False
    for key in ("hadList", "hhadList", "ttgList", "hafuList", "crsList"):
        if not odds_history.get(key):
            return False
    return True


def fetch_odds_for_matches(
    match_items: List[dict],
    *,
    session: Optional[requests.Session] = None,
) -> List[RawOddsRow]:
    """Fetch odds for a list of match items. Returns raw rows for CSV.

    Never silently drops matches — records failures explicitly.
    """
    rows = []
    for item in match_items:
        match_id = item["match_id"]
        match_date = item.get("match_date", "")
        try:
            data = fetch_odds_detail(match_id, session=session)
        except OddsFetchError as e:
            rows.append({
                "match_id": match_id,
                "match_date": match_date,
                "fetch_status": "error",
                "error_detail": str(e),
                "payload_json": "",
            })
            continue

        if not validate_odds_payload(data):
            rows.append({
                "match_id": match_id,
                "match_date": match_date,
                "fetch_status": "missing_data",
                "error_detail": "one or more odds sections empty",
                "payload_json": json.dumps(data, ensure_ascii=False),
            })
            continue

        rows.append({
            "match_id": match_id,
            "match_date": match_date,
            "fetch_status": "ok",
            "error_detail": "",
            "payload_json": json.dumps(data, ensure_ascii=False),
        })
    return rows


RAW_CSV_FIELDS = ["match_id", "match_date", "fetch_status", "error_detail", "payload_json"]


def write_raw_csv(rows: List[RawOddsRow], path) -> None:
    """Write raw odds rows to CSV."""
    ensure_data_dir()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def read_raw_csv(path) -> List[dict]:
    """Read raw CSV back as list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
