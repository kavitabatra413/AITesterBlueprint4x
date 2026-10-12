from pathlib import Path

import pytest
from fastmcp import Client

from tc_mcp.repository import TestCaseDraft, TestFilter, TestRepository, validate_draft
from tc_mcp.server import create_server


CHAPTER = Path(__file__).resolve().parents[2]
DATA = CHAPTER / "data" / "vwo_5000_test_cases.csv"


def test_repository_loads_expected_dataset_and_normalizes_labels(tmp_path):
    repository = TestRepository(DATA, tmp_path / "overlay.csv")
    rows = repository.all_rows()

    assert len(rows) == 5000
    assert len({row["Issue Key"] for row in rows}) == 5000
    assert len({row["Component"] for row in rows}) == 17
    assert all(row["Labels"].split().count("regression") <= 1 for row in rows)


def test_shared_filter_supports_alias_priority_and_live_status(tmp_path):
    repository = TestRepository(DATA, tmp_path / "overlay.csv")
    rows = repository.filter_rows(
        TestFilter(module="ab testing", min_priority="High", test_type=["Functional"])
    )
    assert rows
    assert all(row["Component"] == "A/B Testing" for row in rows)
    assert all(row["Priority"] in {"High", "Highest"} for row in rows)
    assert all(row["Status"] != "Deprecated" for row in rows)


def test_overlay_add_and_update_preserve_source_csv(tmp_path):
    overlay = tmp_path / "overlay.csv"
    repository = TestRepository(DATA, overlay)
    original_count = len(repository.all_rows())
    draft = TestCaseDraft(
        summary="[Reports] Functional: verify report creation",
        component="Reports", test_type="Functional",
        steps=["open reports", "create report", "verify result"],
        expected_result="The new report appears in the reports list.",
    )
    added = repository.add_cases([draft])[0]
    assert added["Issue Key"] == "VWO-6001"
    assert len(repository.all_rows()) == original_count + 1

    before, after = repository.update_case(added["Issue Key"], {"priority": "High"})
    assert before["Priority"] == "Medium"
    assert after["Priority"] == "High"
    assert len(repository.all_rows()) == original_count + 1
    assert repository.data_path == DATA.resolve()


def test_draft_validation_reports_bad_enums_and_weak_steps():
    result = validate_draft(TestCaseDraft(
        summary="weak summary", component="Reports", test_type="Unknown",
        priority="urgent", steps="one | two", expected_result="works as expected",
    ))
    assert not result["valid"]
    assert len(result["errors"]) >= 2
    assert result["warnings"]


@pytest.mark.asyncio
async def test_mcp_exposes_expected_read_only_surface_and_examples(tmp_path):
    server = create_server(DATA, tmp_path / "overlay.csv", allow_write=False)
    async with Client(server) as client:
        tools = {item.name for item in await client.list_tools()}
        assert len(tools) == 19
        assert {
            "list_modules", "get_filter_options", "get_test_stats", "get_test_case",
            "search_test_cases", "search_by_keyword", "get_top_tests_for_module",
            "get_similar_test_cases", "build_test_suite", "get_browser_device_matrix",
            "get_automation_candidates", "estimate_execution_effort",
            "find_duplicate_tests", "find_coverage_gaps", "validate_test_case",
            "get_test_case_template", "export_test_cases", "convert_to_gherkin",
            "generate_automation_stub",
        } == tools

        searched = await client.call_tool("search_test_cases", {"filters": {"module": "Reports"}, "limit": 3})
        assert not searched.is_error
        assert searched.structured_content["count"] == 3

        top = await client.call_tool("get_top_tests_for_module", {"module": "Reports", "count": 5})
        assert not top.is_error
        assert top.structured_content["count"] == 5

        prompts = {item.name for item in await client.list_prompts()}
        assert prompts == {"generate_test_cases", "plan_release_run", "review_module_coverage"}
        resources = await client.list_resources()
        assert {str(item.uri) for item in resources} >= {
            "tc://schema", "tc://modules", "tc://stats/summary",
        }
        assert len(await client.list_resource_templates()) == 1

        smoke_calls = [
            ("get_filter_options", {}),
            ("get_test_stats", {"group_by": ["module"]}),
            ("get_test_case", {"issue_keys": ["VWO-1001"]}),
            ("search_by_keyword", {"query": "data collection"}),
            ("get_similar_test_cases", {"issue_key": "VWO-1001", "limit": 3}),
            ("build_test_suite", {"suite_type": "smoke", "modules": "all", "max_tests": 5}),
            ("get_browser_device_matrix", {"module": "Reports"}),
            ("get_automation_candidates", {"module": "Reports", "limit": 2}),
            ("estimate_execution_effort", {"filters": {"module": "Reports"}}),
            ("find_duplicate_tests", {"mode": "exact"}),
            ("find_coverage_gaps", {"module": "Reports"}),
            ("get_test_case_template", {"module": "Reports", "feature": "report", "test_type": "Functional"}),
            ("export_test_cases", {"issue_keys": ["VWO-1001"], "format": "json"}),
            ("convert_to_gherkin", {"issue_keys": ["VWO-1001"]}),
            ("generate_automation_stub", {"issue_key": "VWO-1001", "framework": "playwright_ts"}),
        ]
        for name, arguments in smoke_calls:
            result = await client.call_tool(name, arguments)
            assert not result.is_error, f"{name}: {result}"


@pytest.mark.asyncio
async def test_write_tools_are_gated_and_dry_run_by_default(tmp_path):
    read_server = create_server(DATA, tmp_path / "readonly.csv", allow_write=False)
    async with Client(read_server) as client:
        assert "add_test_cases" not in {item.name for item in await client.list_tools()}

    write_server = create_server(DATA, tmp_path / "writable.csv", allow_write=True)
    async with Client(write_server) as client:
        assert len(await client.list_tools()) == 21
        assert {"add_test_cases", "update_test_case"} <= {item.name for item in await client.list_tools()}
        result = await client.call_tool("add_test_cases", {
            "test_cases": [{
                "summary": "[Reports] Functional: verify report creation",
                "component": "Reports", "test_type": "Functional",
                "steps": ["open reports", "create report", "verify result"],
                "expected_result": "The report is displayed in the reports list.",
            }],
        })
        assert not result.is_error
        assert result.structured_content["dry_run"] is True
