"""Pipeline entrypoint — orchestrates the full fetch → CSV → prompt → LLM → parse flow."""

import logging
from typing import List, Optional

import requests

from src.config import RAW_CSV_PATH, NORMALIZED_CSV_PATH, ensure_data_dir
from src.odds_fetcher import fetch_odds_for_matches, write_raw_csv, read_raw_csv
from src.odds_parser import normalize_odds, NormalizationError
from src.csv_io import write_normalized_csv, read_normalized_csv
from src.prompt_builder import build_match_data_prompt, enhance_prompt
from src.llm_client import LLMClient, parse_suggestions

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when the pipeline fails at any stage."""


def run_pipeline(
    match_items: List[dict],
    llm_client: LLMClient,
    money: int = 200,
    *,
    session: Optional[requests.Session] = None,
    raw_csv_path=None,
    normalized_csv_path=None,
) -> List[dict]:
    """Run the full pipeline for a list of match items.

    Returns list of dicts, each with match info and parsed suggestions.

    Stages:
      1. Fetch odds for all matches
      2. Write raw CSV
      3. Normalize odds
      4. Write normalized CSV
      5. Read normalized CSV
      6. Build prompt per match
      7. Call LLM
      8. Parse suggestions
    """
    raw_path = raw_csv_path or RAW_CSV_PATH
    norm_path = normalized_csv_path or NORMALIZED_CSV_PATH
    ensure_data_dir()

    # Stage 1-2: Fetch odds and write raw CSV
    logger.info("Fetching odds for %d matches", len(match_items))
    raw_rows = fetch_odds_for_matches(match_items, session=session)
    write_raw_csv(raw_rows, raw_path)
    logger.info("Raw CSV written to %s", raw_path)

    # Stage 3: Normalize
    normalized_rows = []
    for raw_row in raw_rows:
        try:
            norm = normalize_odds(raw_row)
            normalized_rows.append(norm)
        except NormalizationError as e:
            logger.warning("Skipping match %s: %s", raw_row.get("match_id"), e)

    if not normalized_rows:
        raise PipelineError("No matches could be normalized — pipeline aborted")

    # Stage 4: Write normalized CSV
    write_normalized_csv(normalized_rows, norm_path)
    logger.info("Normalized CSV written to %s with %d rows", norm_path, len(normalized_rows))

    # Stage 5: Read back normalized CSV (proves round-trip)
    loaded_rows = read_normalized_csv(norm_path)

    # Stage 6-8: Prompt → LLM → Parse per match
    results = []
    for row in loaded_rows:
        bet_data = build_match_data_prompt(row)
        prompt = enhance_prompt(bet_data, money)
        logger.info("Calling LLM for match %s (%s vs %s)",
                     row["match_id"], row["home_team"], row["away_team"])

        response_text = llm_client.chat(prompt)
        suggestions = parse_suggestions(response_text, money)

        results.append({
            "match_id": row["match_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "suggestions": suggestions,
        })

    return results
