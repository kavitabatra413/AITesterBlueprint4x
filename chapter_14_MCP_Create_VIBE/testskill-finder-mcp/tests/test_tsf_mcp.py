from pathlib import Path

import pytest
from fastmcp import Client

from tsf_mcp.catalog import load_catalog, resolve_skill_file
from tsf_mcp.search import search
from tsf_mcp.server import create_server


SKILLS = Path(__file__).resolve().parents[1] / "skills"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SKILLS)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Playwright API", "pw-api-tester"),
        ("test case creator", "test-case-writer"),
        ("test plan creator", "test-plan-generator"),
        ("test strategy", "test-strategy-designer"),
        ("k6 load test", "k6-load-test-generator"),
        ("deepeval", "deepeval-test-writer"),
    ],
)
def test_golden_searches(catalog, query, expected):
    results = search(catalog, query)
    assert results
    assert results[0][0].name == expected


def test_catalog_integrity_and_upstream_provenance(catalog):
    assert len(catalog.skills) == 100
    assert len(catalog.by_name) == 100
    assert sum(skill.source == "upstream" for skill in catalog.skills) == 36


def test_file_resolution_blocks_path_traversal(catalog):
    skill = catalog.get("test-plan-generator")
    assert resolve_skill_file(skill, "references/test-plan-template.md").is_file()
    with pytest.raises(ValueError, match="inside"):
        resolve_skill_file(skill, "..\\..\\secret.txt")


@pytest.mark.asyncio
async def test_mcp_tools_resources_and_all_skill_prompts(tmp_path):
    server = create_server(SKILLS, allow_write=False)
    async with Client(server) as client:
        tools = {item.name for item in await client.list_tools()}
        assert len(tools) == 13
        assert {
            "list_categories", "list_skills", "get_catalog_stats", "search_skills",
            "find_skill_for_task", "get_skill", "get_skill_file", "get_related_skills",
            "compare_skills", "suggest_skill_chain", "get_stlc_pipeline", "export_skill",
            "validate_skills",
        } == tools
        result = await client.call_tool("search_skills", {"query": "Playwright API"})
        assert not result.is_error
        assert result.structured_content["results"][0]["name"] == "pw-api-tester"
        assert len(await client.list_prompts()) == 103
        resources = await client.list_resources()
        assert {str(item.uri) for item in resources} == {
            "skills://catalog", "skills://catalog.md", "skills://categories",
            "skills://stlc-pipeline", "skills://stats",
        }
        assert len(await client.list_resource_templates()) == 2


@pytest.mark.asyncio
async def test_skill_detail_file_export_and_write_gating():
    server = create_server(SKILLS, allow_write=False)
    async with Client(server) as client:
        detail = await client.call_tool("get_skill", {"name": "test-plan-generator"})
        assert not detail.is_error
        assert detail.structured_content["found"]
        assert "human review" in (
            detail.structured_content["workflow"] + detail.structured_content["output_shape"]
        ).casefold()
        assert "create_skill" not in {item.name for item in await client.list_tools()}
        file = await client.call_tool("get_skill_file", {
            "name": "test-plan-generator", "file_path": "references/test-plan-template.md",
        })
        assert not file.is_error
        assert "Test Plan" in file.structured_content["content"]

        calls = [
            ("list_categories", {}),
            ("list_skills", {"category": "Playwright", "limit": 2}),
            ("get_catalog_stats", {}),
            ("find_skill_for_task", {"task": "test Playwright API"}),
            ("get_related_skills", {"name": "pw-api-tester", "limit": 3}),
            ("compare_skills", {"names": ["pw-api-tester", "api-test-designer"]}),
            ("suggest_skill_chain", {"goal": "plan tests and report bugs", "limit": 5}),
            ("get_stlc_pipeline", {}),
            ("export_skill", {"name": "test-plan-generator", "format": "copilot_prompt"}),
            ("validate_skills", {"name": "test-plan-generator"}),
        ]
        for tool_name, arguments in calls:
            result = await client.call_tool(tool_name, arguments)
            assert not result.is_error, f"{tool_name}: {result}"

        prompt = await client.get_prompt("test-plan-generator", {"task": "Plan this release"})
        assert "Plan this release" in str(prompt.messages)

    writable = create_server(SKILLS, allow_write=True)
    async with Client(writable) as client:
        assert len(await client.list_tools()) == 15
        result = await client.call_tool("create_skill", {
            "name": "sample-new-skill",
            "description": "Use when a QA user asks for a sample skill.",
            "category": "Playwright",
            "kind": "framework",
            "workflow": "1. Inspect inputs.",
            "output_shape": "A concise report.",
            "guardrails": "- Do not invent evidence.",
            "dry_run": True,
        })
        assert not result.is_error
        assert result.structured_content["dry_run"] is True
