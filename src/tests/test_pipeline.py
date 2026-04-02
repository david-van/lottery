"""Comprehensive test suite for the minimal pipeline."""

import csv
import json
import os
import tempfile
from unittest.mock import MagicMock
from pathlib import Path

import pytest
import requests

from src.match_crawler import (
    parse_match_items,
    crawl_match_ids,
    MatchFetchError,
    fetch_match_list_page,
)
from src.odds_fetcher import (
    fetch_odds_for_matches,
    write_raw_csv,
    read_raw_csv,
    validate_odds_payload,
    RAW_CSV_FIELDS,
)
from src.odds_parser import normalize_odds, NormalizationError
from src.csv_io import write_normalized_csv, read_normalized_csv, SchemaError
from src.prompt_builder import build_match_data_prompt, enhance_prompt, PromptBuildError
from src.llm_client import (
    FakeLLMClient,
    parse_suggestions,
    ParseError,
)
from src.pipeline import run_pipeline, PipelineError
from src.models import NORMALIZED_FIELDS


# ---------------------------------------------------------------------------
# Fixtures: synthetic data only
# ---------------------------------------------------------------------------

SAMPLE_MATCH_LIST_RESPONSE = {
    "value": {
        "matchList": [
            {
                "matchDate": "2024-11-09",
                "isToday": 0,
                "subMatchList": [
                    {
                        "gmMatchId": 1027808,
                        "sectionsNo1": "1:0",
                        "homeAbbCnName": "狼队",
                        "awayAbbCnName": "南安普敦",
                    },
                    {
                        "gmMatchId": 1027807,
                        "sectionsNo1": "0:0",
                        "homeAbbCnName": "西汉姆联",
                        "awayAbbCnName": "埃弗顿",
                    },
                ],
            },
            {
                "matchDate": "2024-11-10",
                "isToday": 0,
                "subMatchList": [
                    {
                        "gmMatchId": 0,  # should be filtered out
                        "sectionsNo1": "",
                    },
                ],
            },
        ]
    }
}


def _make_odds_payload(home="测试主队", away="测试客队", league="测试联赛"):
    """Build a minimal valid odds detail response."""
    base_crs = {
        "s01s00": "10.0", "s02s00": "20.0", "s02s01": "12.0",
        "s03s00": "40.0", "s03s01": "25.0", "s03s02": "25.0",
        "s04s00": "100.0", "s04s01": "70.0", "s04s02": "70.0",
        "s05s00": "300.0", "s05s01": "250.0", "s05s02": "250.0",
        "s-1sh": "70.0",
        "s00s00": "15.0", "s01s01": "7.25", "s02s02": "11.5",
        "s03s03": "40.0", "s-1sd": "200.0",
        "s00s01": "8.25", "s00s02": "9.5", "s01s02": "7.25",
        "s00s03": "15.0", "s01s03": "13.0", "s02s03": "19.0",
        "s00s04": "30.0", "s01s04": "26.0", "s02s04": "40.0",
        "s00s05": "70.0", "s01s05": "60.0", "s02s05": "80.0",
        "s-1sa": "35.0",
        "updateDate": "2024-11-01", "updateTime": "12:00:00",
    }
    return {
        "value": {
            "oddsHistory": {
                "homeTeamAllName": home,
                "awayTeamAllName": away,
                "leagueAllName": league,
                "hadList": [
                    {"h": "3.45", "d": "3.55", "a": "1.76",
                     "updateDate": "2024-11-01", "updateTime": "10:00:00"},
                    {"h": "3.50", "d": "3.50", "a": "1.80",
                     "updateDate": "2024-11-01", "updateTime": "12:00:00"},
                ],
                "hhadList": [
                    {"h": "1.77", "d": "3.70", "a": "3.30",
                     "updateDate": "2024-11-01", "updateTime": "12:00:00"},
                ],
                "ttgList": [
                    {"s0": "15.0", "s1": "5.5", "s2": "3.85", "s3": "3.5",
                     "s4": "4.6", "s5": "8.25", "s6": "14.0", "s7": "20.0",
                     "updateDate": "2024-11-01", "updateTime": "12:00:00"},
                ],
                "hafuList": [
                    {"hh": "5.8", "hd": "15.0", "ha": "22.0",
                     "dh": "8.25", "dd": "5.85", "da": "4.8",
                     "ah": "32.0", "ad": "15.0", "aa": "2.69",
                     "updateDate": "2024-11-01", "updateTime": "12:00:00"},
                ],
                "crsList": [base_crs],
            },
            "matchResultList": [],
        }
    }


SAMPLE_ODDS_PAYLOAD = _make_odds_payload()


def _make_valid_llm_response(money=200):
    return (
        f"分析完成。\n"
        f"%%【玩法1(非让球胜)，购买金额：{money // 4}元】，"
        f"【玩法2(非让球平)，购买金额：{money // 4}元】，"
        f"【玩法3(非让球负)，购买金额：{money // 4}元】，"
        f"【玩法20(0:0)，购买金额：{money // 4}元】%%\n"
    )


# ---------------------------------------------------------------------------
# Task 2: Match list fetch client tests
# ---------------------------------------------------------------------------

class TestMatchCrawler:
    def test_parse_match_items_valid(self):
        items = parse_match_items(SAMPLE_MATCH_LIST_RESPONSE, "11817", "72")
        assert len(items) == 2
        assert items[0]["match_id"] == 1027808
        assert items[0]["match_date"] == "2024-11-09"
        assert items[0]["sections_no_1"] == "1:0"
        assert items[0]["season_id"] == "11817"
        assert items[0]["league_id"] == "72"
        assert items[1]["match_id"] == 1027807

    def test_parse_filters_zero_id(self):
        items = parse_match_items(SAMPLE_MATCH_LIST_RESPONSE, "11817", "72")
        ids = [i["match_id"] for i in items]
        assert 0 not in ids

    def test_crawl_with_mocked_session(self):
        from datetime import datetime
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_MATCH_LIST_RESPONSE
        mock_session.get.return_value = mock_resp

        items = crawl_match_ids(
            datetime(2024, 11, 9), datetime(2024, 11, 11),
            "11817", "72", session=mock_session
        )
        assert len(items) == 2
        mock_session.get.assert_called_once()

    def test_fetch_500_raises(self):
        from datetime import datetime
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_session.get.return_value = mock_resp

        with pytest.raises(MatchFetchError, match="HTTP 500"):
            fetch_match_list_page(
                datetime(2024, 11, 9), datetime(2024, 11, 11),
                "11817", "72", session=mock_session
            )

    def test_fetch_timeout_raises(self):
        from datetime import datetime
        mock_session = MagicMock(spec=requests.Session)
        mock_session.get.side_effect = requests.Timeout("timed out")

        with pytest.raises(MatchFetchError, match="HTTP request failed"):
            fetch_match_list_page(
                datetime(2024, 11, 9), datetime(2024, 11, 11),
                "11817", "72", session=mock_session
            )


# ---------------------------------------------------------------------------
# Task 3: Odds fetch and raw CSV writer tests
# ---------------------------------------------------------------------------

class TestOddsFetcher:
    def test_validate_odds_payload_valid(self):
        assert validate_odds_payload(SAMPLE_ODDS_PAYLOAD) is True

    def test_validate_odds_payload_missing_section(self):
        bad = json.loads(json.dumps(SAMPLE_ODDS_PAYLOAD))
        bad["value"]["oddsHistory"]["crsList"] = []
        assert validate_odds_payload(bad) is False

    def test_validate_odds_payload_no_history(self):
        assert validate_odds_payload({"value": {"oddsHistory": None}}) is False

    def test_fetch_odds_for_matches_success(self):
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_ODDS_PAYLOAD
        mock_session.get.return_value = mock_resp

        items = [
            {"match_id": 100, "match_date": "2024-01-01"},
            {"match_id": 200, "match_date": "2024-01-02"},
        ]
        rows = fetch_odds_for_matches(items, session=mock_session)
        assert len(rows) == 2
        assert all(r["fetch_status"] == "ok" for r in rows)
        assert rows[0]["match_id"] == 100

    def test_fetch_odds_missing_data_marked(self):
        bad_payload = {"value": {"oddsHistory": {
            "homeTeamAllName": "A", "awayTeamAllName": "B",
            "hadList": [], "hhadList": [], "ttgList": [], "hafuList": [], "crsList": [],
        }}}
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = bad_payload
        mock_session.get.return_value = mock_resp

        rows = fetch_odds_for_matches(
            [{"match_id": 999, "match_date": "2024-01-01"}],
            session=mock_session,
        )
        assert rows[0]["fetch_status"] == "missing_data"

    def test_raw_csv_round_trip(self):
        rows = [
            {"match_id": 1, "match_date": "2024-01-01", "fetch_status": "ok",
             "error_detail": "", "payload_json": '{"test": true}'},
            {"match_id": 2, "match_date": "2024-01-02", "fetch_status": "error",
             "error_detail": "timeout", "payload_json": ""},
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name
        try:
            write_raw_csv(rows, path)
            loaded = read_raw_csv(path)
            assert len(loaded) == 2
            assert loaded[0]["match_id"] == "1"  # CSV reads as strings
            assert loaded[0]["fetch_status"] == "ok"
            assert loaded[1]["fetch_status"] == "error"
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Task 4: Normalized odds parser tests
# ---------------------------------------------------------------------------

class TestOddsParser:
    def test_normalize_complete_payload(self):
        raw_row = {
            "match_id": 100,
            "match_date": "2024-01-01",
            "fetch_status": "ok",
            "error_detail": "",
            "payload_json": json.dumps(SAMPLE_ODDS_PAYLOAD),
        }
        result = normalize_odds(raw_row)
        assert result["home_team"] == "测试主队"
        assert result["away_team"] == "测试客队"
        assert result["league_name"] == "测试联赛"
        # Verify latest HAD entry was picked (12:00 > 10:00)
        assert result["had_h"] == "3.50"
        assert result["had_d"] == "3.50"
        assert result["had_a"] == "1.80"
        # HHAD
        assert result["hhad_h"] == "1.77"
        # TTG
        assert result["ttg_s0"] == "15.0"
        # CRS
        assert result["crs_1_0"] == "10.0"
        assert result["crs_win_other"] == "70.0"
        assert result["crs_lose_other"] == "35.0"
        # HAFU
        assert result["hafu_hh"] == "5.8"
        assert result["hafu_aa"] == "2.69"

    def test_normalize_missing_section_raises(self):
        bad_payload = json.loads(json.dumps(SAMPLE_ODDS_PAYLOAD))
        bad_payload["value"]["oddsHistory"]["crsList"] = []
        raw_row = {
            "match_id": 100,
            "match_date": "2024-01-01",
            "fetch_status": "ok",
            "error_detail": "",
            "payload_json": json.dumps(bad_payload),
        }
        with pytest.raises(NormalizationError, match="Missing crsList"):
            normalize_odds(raw_row)

    def test_normalize_non_ok_status_raises(self):
        raw_row = {
            "match_id": 100,
            "match_date": "2024-01-01",
            "fetch_status": "error",
            "error_detail": "timeout",
            "payload_json": "",
        }
        with pytest.raises(NormalizationError, match="fetch_status=error"):
            normalize_odds(raw_row)

    def test_normalize_latest_entry_deterministic(self):
        payload = json.loads(json.dumps(SAMPLE_ODDS_PAYLOAD))
        # Add older entry to HAD list
        payload["value"]["oddsHistory"]["hadList"].insert(0, {
            "h": "1.00", "d": "1.00", "a": "1.00",
            "updateDate": "2024-10-01", "updateTime": "08:00:00",
        })
        raw_row = {
            "match_id": 100, "match_date": "2024-01-01",
            "fetch_status": "ok", "error_detail": "",
            "payload_json": json.dumps(payload),
        }
        result = normalize_odds(raw_row)
        # Should still pick the latest (2024-11-01 12:00)
        assert result["had_h"] == "3.50"


# ---------------------------------------------------------------------------
# Task 5: Normalized CSV IO tests
# ---------------------------------------------------------------------------

class TestNormalizedCsvIO:
    def _make_row(self):
        raw = {
            "match_id": 100, "match_date": "2024-01-01",
            "fetch_status": "ok", "error_detail": "",
            "payload_json": json.dumps(SAMPLE_ODDS_PAYLOAD),
        }
        return normalize_odds(raw)

    def test_round_trip(self):
        row = self._make_row()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            write_normalized_csv([row], path)
            loaded = read_normalized_csv(path)
            assert len(loaded) == 1
            assert loaded[0]["home_team"] == row["home_team"]
            assert loaded[0]["had_h"] == row["had_h"]
            assert loaded[0]["crs_1_0"] == row["crs_1_0"]
        finally:
            os.unlink(path)

    def test_schema_drift_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w",
                                          newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["match_id", "bad_column"])
            writer.writerow(["100", "x"])
            path = f.name
        try:
            with pytest.raises(SchemaError, match="Missing required columns"):
                read_normalized_csv(path)
        finally:
            os.unlink(path)

    def test_filter_by_match_id(self):
        row1 = self._make_row()
        row2 = self._make_row()
        row2["match_id"] = 200
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            write_normalized_csv([row1, row2], path)
            loaded = read_normalized_csv(path, match_id=200)
            assert len(loaded) == 1
            assert loaded[0]["match_id"] == "200"
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Task 6: Prompt builder tests
# ---------------------------------------------------------------------------

class TestPromptBuilder:
    def _make_normalized_row(self):
        raw = {
            "match_id": 100, "match_date": "2024-01-01",
            "fetch_status": "ok", "error_detail": "",
            "payload_json": json.dumps(SAMPLE_ODDS_PAYLOAD),
        }
        return normalize_odds(raw)

    def test_build_match_data_prompt(self):
        row = self._make_normalized_row()
        prompt = build_match_data_prompt(row)
        assert "主球队1:测试主队" in prompt
        assert "客球队2:测试客队" in prompt
        assert "玩法1：非让球胜" in prompt
        assert "玩法54：负负" in prompt
        assert "玩法38：进球数：0" in prompt
        assert "玩法45：进球数：7+" in prompt

    def test_enhance_prompt_with_money(self):
        row = self._make_normalized_row()
        data_prompt = build_match_data_prompt(row)
        full = enhance_prompt(data_prompt, 200)
        assert "投注金额200元" in full
        assert "%%" in full
        assert "【玩法+序号" in full

    def test_missing_field_raises(self):
        row = {"home_team": "", "away_team": "B"}
        with pytest.raises(PromptBuildError, match="Missing required field"):
            build_match_data_prompt(row)


# ---------------------------------------------------------------------------
# Task 7: LLM abstraction and result parser tests
# ---------------------------------------------------------------------------

class TestLLMClient:
    def test_fake_provider_deterministic(self):
        response = _make_valid_llm_response(200)
        client = FakeLLMClient(response)
        result = client.chat("test prompt")
        assert "%%" in result

    def test_parse_suggestions_valid(self):
        response = _make_valid_llm_response(200)
        suggestions = parse_suggestions(response, 200)
        assert len(suggestions) == 4
        assert all(s["amount"] == 50 for s in suggestions)
        assert suggestions[0]["play_content"] == "非让球胜"

    def test_parse_no_markers_raises(self):
        with pytest.raises(ParseError, match="No %%"):
            parse_suggestions("no markers here", 200)

    def test_parse_wrong_total_raises(self):
        response = _make_valid_llm_response(200)
        with pytest.raises(ParseError, match="does not equal"):
            parse_suggestions(response, 999)

    def test_parse_no_entries_raises(self):
        with pytest.raises(ParseError, match="No valid bet entries"):
            parse_suggestions("%%nothing useful%%", 200)


# ---------------------------------------------------------------------------
# Task 8: End-to-end pipeline tests
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_end_to_end_offline(self):
        """Full pipeline with mocked HTTP + fake LLM."""
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_ODDS_PAYLOAD
        mock_session.get.return_value = mock_resp

        money = 200
        llm_response = _make_valid_llm_response(money)
        fake_llm = FakeLLMClient(llm_response)

        match_items = [
            {"match_id": 100, "match_date": "2024-01-01"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "raw.csv")
            norm_path = os.path.join(tmpdir, "norm.csv")

            results = run_pipeline(
                match_items, fake_llm, money,
                session=mock_session,
                raw_csv_path=raw_path,
                normalized_csv_path=norm_path,
            )

            # Verify outputs
            assert len(results) == 1
            assert str(results[0]["match_id"]) == "100"
            assert results[0]["home_team"] == "测试主队"
            assert len(results[0]["suggestions"]) == 4
            assert sum(s["amount"] for s in results[0]["suggestions"]) == money

            # Verify CSV artifacts were created
            assert os.path.exists(raw_path)
            assert os.path.exists(norm_path)

            # Verify raw CSV content
            raw_rows = read_raw_csv(raw_path)
            assert len(raw_rows) == 1
            assert raw_rows[0]["fetch_status"] == "ok"

            # Verify normalized CSV content
            norm_rows = read_normalized_csv(norm_path)
            assert len(norm_rows) == 1

    def test_pipeline_fails_on_malformed_llm(self):
        """Pipeline aborts cleanly when LLM output is invalid."""
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_ODDS_PAYLOAD
        mock_session.get.return_value = mock_resp

        # LLM output missing %% markers
        fake_llm = FakeLLMClient("I have no structured output")

        match_items = [{"match_id": 100, "match_date": "2024-01-01"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ParseError, match="No %%"):
                run_pipeline(
                    match_items, fake_llm, 200,
                    session=mock_session,
                    raw_csv_path=os.path.join(tmpdir, "raw.csv"),
                    normalized_csv_path=os.path.join(tmpdir, "norm.csv"),
                )

    def test_pipeline_no_valid_matches(self):
        """Pipeline raises when all matches fail normalization."""
        mock_session = MagicMock(spec=requests.Session)
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "server error"
        mock_session.get.side_effect = requests.RequestException("fail")

        fake_llm = FakeLLMClient("unused")
        match_items = [{"match_id": 100, "match_date": "2024-01-01"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(PipelineError, match="No matches could be normalized"):
                run_pipeline(
                    match_items, fake_llm, 200,
                    session=mock_session,
                    raw_csv_path=os.path.join(tmpdir, "raw.csv"),
                    normalized_csv_path=os.path.join(tmpdir, "norm.csv"),
                )


# ---------------------------------------------------------------------------
# Guardrail: No forbidden imports
# ---------------------------------------------------------------------------

class TestGuardrails:
    def test_no_forbidden_imports(self):
        """Verify no flask/pymysql/apscheduler imports in src/."""
        import ast
        src_dir = Path(__file__).resolve().parent.parent
        forbidden = {"flask", "pymysql", "flask_apscheduler"}
        violations = []
        for py_file in src_dir.glob("**/*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in forbidden:
                            violations.append(f"{py_file}:{node.lineno} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in forbidden:
                        violations.append(f"{py_file}:{node.lineno} imports from {node.module}")
        assert violations == [], f"Forbidden imports found:\n" + "\n".join(violations)
