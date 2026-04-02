"""Canonical record shapes as TypedDicts for type clarity."""

from typing import TypedDict, List


class MatchItem(TypedDict):
    """A single match from the match list API."""
    match_id: int
    match_date: str          # "YYYY-MM-DD"
    sections_no_1: str       # half-time score
    league_id: str
    season_id: str


class RawOddsRow(TypedDict):
    """One row in the raw CSV — preserves API payload as-is."""
    match_id: int
    match_date: str
    fetch_status: str        # "ok" | "missing_data" | "error"
    error_detail: str        # empty string if ok
    payload_json: str        # serialized JSON of the full odds response


class NormalizedOddsRow(TypedDict):
    """Flat dict with all named odds fields for one match."""
    match_id: int
    match_date: str
    home_team: str
    away_team: str
    league_name: str
    # HAD (non-handicap)
    had_h: str
    had_d: str
    had_a: str
    # HHAD (handicap)
    hhad_h: str
    hhad_d: str
    hhad_a: str
    # TTG (total goals) s0..s7
    ttg_s0: str
    ttg_s1: str
    ttg_s2: str
    ttg_s3: str
    ttg_s4: str
    ttg_s5: str
    ttg_s6: str
    ttg_s7: str
    # CRS (correct score) — home wins
    crs_1_0: str
    crs_2_0: str
    crs_2_1: str
    crs_3_0: str
    crs_3_1: str
    crs_3_2: str
    crs_4_0: str
    crs_4_1: str
    crs_4_2: str
    crs_5_0: str
    crs_5_1: str
    crs_5_2: str
    crs_win_other: str       # s-1sh
    # CRS — draws
    crs_0_0: str
    crs_1_1: str
    crs_2_2: str
    crs_3_3: str
    crs_draw_other: str      # s-1sd
    # CRS — away wins
    crs_0_1: str
    crs_0_2: str
    crs_1_2: str
    crs_0_3: str
    crs_1_3: str
    crs_2_3: str
    crs_0_4: str
    crs_1_4: str
    crs_2_4: str
    crs_0_5: str
    crs_1_5: str
    crs_2_5: str
    crs_lose_other: str      # s-1sa
    # HAFU (half/full result) — 9 combinations
    hafu_hh: str
    hafu_hd: str
    hafu_ha: str
    hafu_dh: str
    hafu_dd: str
    hafu_da: str
    hafu_ah: str
    hafu_ad: str
    hafu_aa: str


# Ordered field names for the normalized CSV schema
NORMALIZED_FIELDS: List[str] = list(NormalizedOddsRow.__annotations__.keys())


class Suggestion(TypedDict):
    """One parsed betting suggestion from LLM output."""
    play_content: str        # e.g. "非让球胜"
    amount: int              # yuan
