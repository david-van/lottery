"""Match list fetch client — rebuilds crawler_all_match_id.py as pure functions."""

import json
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from src.config import MATCH_LIST_API, DEFAULT_USER_AGENT, HTTP_TIMEOUT


class MatchFetchError(Exception):
    """Raised when the match list API request fails."""


def fetch_match_list_page(
    start_date: datetime,
    end_date: datetime,
    season_id: str,
    league_id: str,
    *,
    session: Optional[requests.Session] = None,
) -> dict:
    """Fetch one page of match list data from the sporttery API.

    Returns parsed JSON dict. Raises MatchFetchError on failure.
    """
    s = session or requests.Session()
    params = {
        "seasonId": season_id,
        "uniformLeagueId": league_id,
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    try:
        resp = s.get(MATCH_LIST_API, headers=headers, params=params, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        raise MatchFetchError(f"HTTP request failed: {e}") from e

    if resp.status_code != 200:
        raise MatchFetchError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        return resp.json()
    except (json.JSONDecodeError, ValueError) as e:
        raise MatchFetchError(f"Invalid JSON response: {e}") from e


def parse_match_items(data: dict, season_id: str, league_id: str) -> List[dict]:
    """Parse the API response into a list of match-item dicts.

    Returns list of dicts with keys: match_id, match_date, sections_no_1, league_id, season_id.
    """
    results = []
    match_list = data.get("value", {}).get("matchList", [])
    for sub_match in match_list:
        match_date = sub_match.get("matchDate", "")
        for k, matches in sub_match.items():
            if k in ("matchDate", "isToday"):
                continue
            if not isinstance(matches, list):
                continue
            for detail in matches:
                gm_id = detail.get("gmMatchId", 0)
                if gm_id != 0:
                    results.append({
                        "match_id": gm_id,
                        "match_date": match_date,
                        "sections_no_1": detail.get("sectionsNo1", ""),
                        "league_id": league_id,
                        "season_id": season_id,
                    })
    return results


def crawl_match_ids(
    start_date: datetime,
    end_date: datetime,
    season_id: str,
    league_id: str,
    *,
    session: Optional[requests.Session] = None,
) -> List[dict]:
    """Crawl match IDs over a date range using 7-day rolling windows.

    Returns flat list of match-item dicts.
    """
    all_items = []
    current = start_date
    while current < end_date:
        range_end = min(current + timedelta(days=6), end_date)
        data = fetch_match_list_page(current, range_end, season_id, league_id, session=session)
        items = parse_match_items(data, season_id, league_id)
        all_items.extend(items)
        current += timedelta(days=7)
    return all_items


def crawl_multi_league_match_ids(
    start_date: datetime,
    end_date: datetime,
    leagues: dict,
    *,
    session: Optional[requests.Session] = None,
) -> List[dict]:
    """Crawl match IDs for multiple leagues.

    leagues: dict of {name: {"season_id": str, "league_id": str}}
    """
    all_items = []
    current = start_date
    while current < end_date:
        for league_name, info in leagues.items():
            range_end = min(current + timedelta(days=6), end_date)
            data = fetch_match_list_page(
                current, range_end, info["season_id"], info["league_id"], session=session
            )
            items = parse_match_items(data, info["season_id"], info["league_id"])
            all_items.extend(items)
        current += timedelta(days=7)
    return all_items
