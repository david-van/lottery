"""Odds normalization parser — converts raw API payloads to flat named dicts."""

import json
from src.models import NormalizedOddsRow


class NormalizationError(Exception):
    """Raised when a raw payload cannot be normalized."""


def _latest_entry(entries: list) -> dict:
    """Pick the latest entry by (updateDate, updateTime)."""
    return max(entries, key=lambda x: (x.get("updateDate", ""), x.get("updateTime", "")))


def normalize_odds(raw_row: dict) -> NormalizedOddsRow:
    """Normalize a raw CSV row (with payload_json) into a NormalizedOddsRow.

    Returns None-like behavior via exception for invalid records.
    Raises NormalizationError if the payload is missing required data.
    """
    if raw_row.get("fetch_status") != "ok":
        raise NormalizationError(
            f"Cannot normalize match {raw_row.get('match_id')}: "
            f"fetch_status={raw_row.get('fetch_status')}, "
            f"error={raw_row.get('error_detail')}"
        )

    try:
        data = json.loads(raw_row["payload_json"])
    except (json.JSONDecodeError, KeyError) as e:
        raise NormalizationError(f"Invalid payload JSON for match {raw_row.get('match_id')}: {e}") from e

    odds_history = data.get("value", {}).get("oddsHistory")
    if not odds_history:
        raise NormalizationError(f"No oddsHistory for match {raw_row.get('match_id')}")

    required_lists = ["hadList", "hhadList", "ttgList", "hafuList", "crsList"]
    for key in required_lists:
        if not odds_history.get(key):
            raise NormalizationError(f"Missing {key} for match {raw_row.get('match_id')}")

    # Extract latest entries
    had = _latest_entry(odds_history["hadList"])
    hhad = _latest_entry(odds_history["hhadList"])
    ttg = _latest_entry(odds_history["ttgList"])
    hafu = _latest_entry(odds_history["hafuList"])
    crs = _latest_entry(odds_history["crsList"])

    # Meta
    home_team = odds_history.get("homeTeamAllName", "")
    away_team = odds_history.get("awayTeamAllName", "")
    league_name = odds_history.get("leagueAllName", "")

    return {
        "match_id": raw_row.get("match_id", ""),
        "match_date": raw_row.get("match_date", ""),
        "home_team": home_team,
        "away_team": away_team,
        "league_name": league_name,
        # HAD
        "had_h": str(had["h"]),
        "had_d": str(had["d"]),
        "had_a": str(had["a"]),
        # HHAD
        "hhad_h": str(hhad["h"]),
        "hhad_d": str(hhad["d"]),
        "hhad_a": str(hhad["a"]),
        # TTG
        "ttg_s0": str(ttg["s0"]),
        "ttg_s1": str(ttg["s1"]),
        "ttg_s2": str(ttg["s2"]),
        "ttg_s3": str(ttg["s3"]),
        "ttg_s4": str(ttg["s4"]),
        "ttg_s5": str(ttg["s5"]),
        "ttg_s6": str(ttg["s6"]),
        "ttg_s7": str(ttg["s7"]),
        # CRS — home wins
        "crs_1_0": str(crs["s01s00"]),
        "crs_2_0": str(crs["s02s00"]),
        "crs_2_1": str(crs["s02s01"]),
        "crs_3_0": str(crs["s03s00"]),
        "crs_3_1": str(crs["s03s01"]),
        "crs_3_2": str(crs["s03s02"]),
        "crs_4_0": str(crs["s04s00"]),
        "crs_4_1": str(crs["s04s01"]),
        "crs_4_2": str(crs["s04s02"]),
        "crs_5_0": str(crs["s05s00"]),
        "crs_5_1": str(crs["s05s01"]),
        "crs_5_2": str(crs["s05s02"]),
        "crs_win_other": str(crs["s-1sh"]),
        # CRS — draws
        "crs_0_0": str(crs["s00s00"]),
        "crs_1_1": str(crs["s01s01"]),
        "crs_2_2": str(crs["s02s02"]),
        "crs_3_3": str(crs["s03s03"]),
        "crs_draw_other": str(crs["s-1sd"]),
        # CRS — away wins
        "crs_0_1": str(crs["s00s01"]),
        "crs_0_2": str(crs["s00s02"]),
        "crs_1_2": str(crs["s01s02"]),
        "crs_0_3": str(crs["s00s03"]),
        "crs_1_3": str(crs["s01s03"]),
        "crs_2_3": str(crs["s02s03"]),
        "crs_0_4": str(crs["s00s04"]),
        "crs_1_4": str(crs["s01s04"]),
        "crs_2_4": str(crs["s02s04"]),
        "crs_0_5": str(crs["s00s05"]),
        "crs_1_5": str(crs["s01s05"]),
        "crs_2_5": str(crs["s02s05"]),
        "crs_lose_other": str(crs["s-1sa"]),
        # HAFU
        "hafu_hh": str(hafu["hh"]),
        "hafu_hd": str(hafu["hd"]),
        "hafu_ha": str(hafu["ha"]),
        "hafu_dh": str(hafu["dh"]),
        "hafu_dd": str(hafu["dd"]),
        "hafu_da": str(hafu["da"]),
        "hafu_ah": str(hafu["ah"]),
        "hafu_ad": str(hafu["ad"]),
        "hafu_aa": str(hafu["aa"]),
    }
