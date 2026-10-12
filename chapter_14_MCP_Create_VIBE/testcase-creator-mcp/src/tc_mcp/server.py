"""FastMCP server exposing deterministic VWO test-case tools."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse

from tc_mcp.repository import (
    BROWSERS, CSV_FIELDS, DEVICES, MODULE_ALIASES, PRIORITIES, PRIORITY_ORDER,
    STAT_FIELDS, TEST_TYPES, TestCaseDraft, TestFilter, TestRepository,
    available_values, compact_row, count_by, parse_steps, validate_draft,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOCAL_DATA = PROJECT_ROOT / "data" / "vwo_5000_test_cases.csv"
PACKAGED_DATA = Path(__file__).resolve().parent / "data" / "vwo_5000_test_cases.csv"
DEFAULT_DATA = LOCAL_DATA if LOCAL_DATA.is_file() else PACKAGED_DATA
PRIORITY_WEIGHT = {"Highest": 40, "High": 30, "Medium": 20, "Low": 10}
STATUS_WEIGHT = {"Ready": 10, "Automated": 8, "Draft": 2}
TYPE_WEIGHT = {
    "Security": 6, "Functional": 6, "Negative": 5, "API": 5,
    "Regression": 4, "Boundary": 4, "Performance": 3, "UI/UX": 2,
    "Accessibility": 2,
}
FIELD_ALIASES = {
    "module": "Component", "priority": "Priority", "test_type": "Test Type",
    "status": "Status", "browser": "Browser", "device": "Device", "feature": "_feature",
}


def _profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(rows),
        "by_module": count_by(rows, "module"),
        "by_priority": count_by(rows, "priority"),
        "by_test_type": count_by(rows, "test_type"),
        "by_status": count_by(rows, "status"),
        "by_browser": count_by(rows, "browser"),
        "by_device": count_by(rows, "device"),
    }


def _rank(row: dict[str, Any]) -> int:
    return (
        PRIORITY_WEIGHT.get(row["Priority"], 0)
        + STATUS_WEIGHT.get(row["Status"], 0)
        + TYPE_WEIGHT.get(row["Test Type"], 0)
    )


def _rank_reason(row: dict[str, Any]) -> str:
    return (
        f"{row['Priority']} · {row['Status']} · {row['Test Type']} · "
        f"first pick for feature '{row['_feature']}'"
    )


def _full_row(row: dict[str, Any]) -> dict[str, Any]:
    result = {field: row[field] for field in CSV_FIELDS}
    result["steps_list"] = parse_steps(row["Steps"])
    result["feature"] = row["_feature"]
    return result


def _pick_diverse(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (-_rank(row), row["Issue Key"]))
    by_feature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ordered:
        by_feature[row["_feature"]].append(row)
    selected: list[dict[str, Any]] = []
    features = sorted(by_feature)
    while features and len(selected) < count:
        remaining = []
        for feature in features:
            candidates = by_feature[feature]
            if candidates and len(selected) < count:
                selected.append(candidates.pop(0))
            if candidates:
                remaining.append(feature)
        features = remaining
    return selected


def create_server(
    data_path: Path | None = None,
    overlay_path: Path | None = None,
    allow_write: bool | None = None,
) -> FastMCP:
    resolved_data = data_path or Path(os.environ.get("TC_MCP_DATA_PATH", DEFAULT_DATA))
    home_data = Path.home() / ".tc_mcp"
    default_overlay = (
        PROJECT_ROOT / "data" / "tc_additions.csv"
        if LOCAL_DATA.is_file() else home_data / "tc_additions.csv"
    )
    resolved_overlay = overlay_path or Path(os.environ.get("TC_MCP_OVERLAY_PATH", default_overlay))
    export_dir = Path(os.environ.get(
        "TC_MCP_EXPORT_DIR",
        PROJECT_ROOT / "exports" if LOCAL_DATA.is_file() else home_data / "exports",
    ))
    can_write = (
        os.environ.get("TC_MCP_ALLOW_WRITE", "false").casefold() == "true"
        if allow_write is None else allow_write
    )
    repository = TestRepository(resolved_data, resolved_overlay)
    mcp = FastMCP(
        "TestCreator MCP",
        instructions=(
            "Find, rank, plan, validate, and export test cases from the VWO test "
            "catalog. Source CSV data is read-only. Authoring tools are enabled "
            "only when writes are explicitly allowed."
        ),
    )

    @mcp.custom_route("/", methods=["GET"], include_in_schema=False)
    async def landing_page(_request: Request) -> HTMLResponse:
        """Explain the MCP endpoint to people who open the server in a browser."""
        return HTMLResponse(
            "<!doctype html><html><head><title>TestCreator MCP</title></head>"
            "<body><h1>TestCreator MCP</h1><p>This is an MCP server, not a web app.</p>"
            "<p>Connect an MCP client using Streamable HTTP at <code>/mcp</code>.</p>"
            "<p>For MCP Inspector, select Streamable HTTP and use "
            "<code>http://127.0.0.1:8000/mcp</code>.</p></body></html>"
        )

    @mcp.tool
    def list_modules(include_features: bool = True) -> dict[str, Any]:
        """Use to discover catalog modules; for matching tests, use search_test_cases."""
        rows = repository.all_rows()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["Component"]].append(row)
        modules = []
        for name in sorted(grouped):
            module_rows = grouped[name]
            item: dict[str, Any] = {
                "module": name, "total": len(module_rows),
                "live": sum(row["Status"] != "Deprecated" for row in module_rows),
                "by_priority": count_by(module_rows, "priority"),
            }
            if include_features:
                item["features"] = sorted({row["_feature"] for row in module_rows})
            modules.append(item)
        return {"count": len(modules), "modules": modules}

    @mcp.tool
    def get_filter_options() -> dict[str, Any]:
        """Use to learn valid filter values before querying the catalog."""
        return {
            **available_values(repository.all_rows()),
            "aliases": MODULE_ALIASES,
            "priority_order": ["Low", "Medium", "High", "Highest"],
        }

    @mcp.tool
    def get_test_stats(
        group_by: list[Literal["module", "priority", "test_type", "status", "browser", "device", "feature"]],
        filters: TestFilter | None = None,
    ) -> dict[str, Any]:
        """Use to summarize catalog coverage; for individual cases, use search_test_cases."""
        if not 1 <= len(group_by) <= 2:
            raise ValueError("group_by must contain one or two dimensions")
        rows = repository.filter_rows(filters)
        if len(group_by) == 1:
            return {"group_by": group_by, "total": len(rows), "counts": count_by(rows, group_by[0])}
        first, second = group_by
        matrix: dict[str, dict[str, int]] = {}
        for row in rows:
            outer = str(row[STAT_FIELDS[first]])
            inner = str(row[STAT_FIELDS[second]])
            matrix.setdefault(outer, {})
            matrix[outer][inner] = matrix[outer].get(inner, 0) + 1
        return {"group_by": group_by, "total": len(rows), "matrix": matrix}

    @mcp.tool
    def get_test_case(issue_keys: list[str]) -> dict[str, Any]:
        """Use for exact issue-key lookups; for discovery by criteria, use search_test_cases."""
        if not 1 <= len(issue_keys) <= 25:
            raise ValueError("issue_keys must contain between 1 and 25 keys")
        found, missing = repository.get_by_keys(issue_keys)
        return {"count": len(found), "test_cases": [_full_row(row) for row in found], "unknown_keys": missing}

    @mcp.tool
    def search_test_cases(
        filters: TestFilter | None = None,
        sort_by: Literal["priority", "key"] = "priority",
        limit: int = 20,
        offset: int = 0,
        detail: Literal["compact", "full"] = "compact",
    ) -> dict[str, Any]:
        """Use for filtered catalog searches; for ranked run order, use get_top_tests_for_module."""
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("limit must be 1..100 and offset must be nonnegative")
        rows = repository.filter_rows(filters)
        if sort_by == "priority":
            rows.sort(key=lambda row: (-PRIORITY_ORDER.get(row["Priority"], -1), row["Issue Key"]))
        else:
            rows.sort(key=lambda row: row["Issue Key"])
        page = rows[offset : offset + limit]
        if detail == "full" and len(page) > 25:
            raise ValueError("full detail is capped at 25 rows; lower limit")
        return {
            "total": len(rows), "offset": offset, "count": len(page),
            "results": [_full_row(row) if detail == "full" else compact_row(row) for row in page],
        }

    @mcp.tool
    def search_by_keyword(query: str, module: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Use for free-text scenario searches; for structured filters, use search_test_cases."""
        if not query.strip() or not 1 <= limit <= 100:
            raise ValueError("query is required and limit must be between 1 and 100")
        terms = [term.casefold() for term in query.split()]
        filters = TestFilter(module=module) if module else TestFilter()
        hits = []
        for row in repository.filter_rows(filters):
            fields = {
                "summary": row["Summary"], "description": row["Description"],
                "steps": row["Steps"], "expected_result": row["Expected Result"],
                "feature": row["_feature"],
            }
            matches = [name for name, text in fields.items() if all(t in text.casefold() for t in terms)]
            if matches:
                hits.append((len(matches), row, matches[0]))
        hits.sort(key=lambda result: (-result[0], -_rank(result[1]), result[1]["Issue Key"]))
        return {
            "query": query, "count": min(limit, len(hits)),
            "results": [{**compact_row(row), "matched_field": field} for _, row, field in hits[:limit]],
        }

    @mcp.tool
    def get_top_tests_for_module(
        module: str,
        count: int = 10,
        test_types: list[str] | None = None,
        browser: str | None = None,
        device: str | None = None,
        unique_scenarios: bool = True,
    ) -> dict[str, Any]:
        """Use for "what should I run first"; for an unranked result set, use search_test_cases."""
        if not 1 <= count <= 50:
            raise ValueError("count must be between 1 and 50")
        filters = TestFilter(
            module=module, test_type=test_types, browser=browser, device=device,
        )
        rows = repository.filter_rows(filters)
        if unique_scenarios:
            picked = _pick_diverse(rows, count)
        else:
            picked = sorted(rows, key=lambda row: (-_rank(row), row["Issue Key"]))[:count]
        return {
            "module": repository.resolve_module(module) or module,
            "count": len(picked),
            "results": [
                {**compact_row(row), "score": _rank(row), "rank_reason": _rank_reason(row)}
                for row in picked
            ],
        }

    @mcp.tool
    def get_similar_test_cases(issue_key: str, limit: int = 10) -> dict[str, Any]:
        """Use for near-match examples; for a direct key lookup, use get_test_case."""
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        found, missing = repository.get_by_keys([issue_key])
        if missing:
            raise ValueError(f"Unknown issue key: {issue_key}")
        source = found[0]
        candidates = []
        for row in repository.all_rows():
            if row["Issue Key"] == issue_key or row["Status"] == "Deprecated":
                continue
            differences = []
            for field, label in (("Test Type", "test_type"), ("Browser", "browser"), ("Device", "device")):
                if row[field] != source[field]:
                    differences.append(label)
            same_feature = row["_feature"].casefold() == source["_feature"].casefold()
            if same_feature or row["Component"] == source["Component"]:
                score = (10 if same_feature else 0) + (5 if row["Component"] == source["Component"] else 0)
                candidates.append((score, row, differences))
        candidates.sort(key=lambda entry: (-entry[0], entry[1]["Issue Key"]))
        return {
            "issue_key": issue_key,
            "results": [
                {**compact_row(row), "differs_in": differences}
                for _, row, differences in candidates[:limit]
            ],
        }

    @mcp.tool
    def build_test_suite(
        suite_type: Literal["smoke", "sanity", "regression"],
        modules: list[str] | Literal["all"] = "all",
        min_tests: int = 1,
        max_tests: int = 100,
        browsers: list[str] | None = None,
        devices: list[str] | None = None,
        include_drafts: bool = False,
    ) -> dict[str, Any]:
        """Use to build a run-ready suite; for tailored ranked cases, use get_top_tests_for_module."""
        if min_tests < 0 or max_tests < 1 or min_tests > max_tests:
            raise ValueError("require 0 <= min_tests <= max_tests and max_tests >= 1")
        types = {
            "smoke": ["Functional", "API", "Security"],
            "sanity": ["Functional", "Negative", "API"],
            "regression": None,
        }[suite_type]
        priorities = {
            "smoke": ["Highest"], "sanity": ["Highest", "High"], "regression": None,
        }[suite_type]
        filters = TestFilter(
            module=None if modules == "all" else modules,
            test_type=types,
            priority=priorities,
            status=None if include_drafts else ["Ready", "Automated"],
            browser=browsers,
            device=devices,
        )
        rows = repository.filter_rows(filters)
        preferred_browser = "Chrome 148"
        rows.sort(key=lambda row: (
            -_rank(row),
            row["Browser"] != preferred_browser,
            row["Device"] != "desktop",
            row["Issue Key"],
        ))
        if suite_type in {"smoke", "sanity"}:
            selected = _pick_diverse(rows, max_tests)
        else:
            selected = rows[:max_tests]
        relaxations = []
        if len(selected) < min_tests and suite_type != "regression":
            base_filters = filters.model_copy(update={"priority": None})
            broader = repository.filter_rows(base_filters)
            existing_keys = {row["Issue Key"] for row in selected}
            lower_priorities = [
                priority for priority in reversed(PRIORITIES)
                if priorities and priority not in priorities
                and PRIORITY_ORDER[priority] < min(PRIORITY_ORDER[value] for value in priorities)
            ]
            added = []
            for priority in lower_priorities:
                tier = [row for row in broader if row["Priority"] == priority and row["Issue Key"] not in existing_keys]
                tier.sort(key=lambda row: (-_rank(row), row["Issue Key"]))
                for row in tier:
                    added.append(row)
                    existing_keys.add(row["Issue Key"])
                    if len(selected) + len(added) >= min_tests:
                        break
                if len(selected) + len(added) >= min_tests:
                    break
            selected.extend(added[: max_tests - len(selected)])
            if added:
                relaxations.append(f"Added lower-priority tests ({', '.join(sorted({row['Priority'] for row in added}))}) to meet min_tests.")
            if len(selected) < min_tests:
                relaxations.append(f"Only {len(selected)} tests matched; requested min_tests={min_tests}.")
        makeup = _profile(selected)
        effort = sum(1 if row["Status"] == "Automated" else 10 for row in selected)
        return {
            "suite_type": suite_type, "count": len(selected),
            "test_cases": [compact_row(row) for row in selected],
            "makeup": makeup, "estimated_minutes": effort, "relaxations": relaxations,
        }

    @mcp.tool
    def get_browser_device_matrix(module: str | None = None, feature: str | None = None) -> dict[str, Any]:
        """Use to inspect browser/device coverage; for missing cells, use find_coverage_gaps."""
        rows = repository.filter_rows(TestFilter(module=module, feature=feature))
        matrix = {browser: {device: 0 for device in DEVICES} for browser in BROWSERS}
        for row in rows:
            matrix.setdefault(row["Browser"], {}).setdefault(row["Device"], 0)
            matrix[row["Browser"]][row["Device"]] += 1
        gaps = [
            {"browser": browser, "device": device}
            for browser, devices_map in matrix.items()
            for device, count in devices_map.items() if count == 0
        ]
        return {"total": len(rows), "matrix": matrix, "empty_cells": gaps}

    @mcp.tool
    def get_automation_candidates(
        module: str | None = None, min_priority: str = "High", limit: int = 20,
    ) -> dict[str, Any]:
        """Use to find ready manual tests worth automating; for all statuses, use search_test_cases."""
        if min_priority not in PRIORITIES or not 1 <= limit <= 100:
            raise ValueError("invalid priority or limit")
        rows = repository.filter_rows(TestFilter(
            module=module, min_priority=min_priority, status=["Ready"],
        ))
        rows.sort(key=lambda row: (-_rank(row), row["Issue Key"]))
        variants = Counter(
            row["Summary"] for row in repository.all_rows()
            if row["Status"] != "Deprecated"
        )
        return {
            "count": min(limit, len(rows)),
            "results": [
                {**compact_row(row), "score": _rank(row),
                 "reason": f"{row['Priority']} priority {row['Test Type']} test; {variants[row['Summary']]} browser/device variant(s)."}
                for row in rows[:limit]
            ],
        }

    @mcp.tool
    def estimate_execution_effort(
        issue_keys: list[str] | None = None,
        filters: TestFilter | None = None,
        minutes_manual: int = 10,
        minutes_automated: int = 1,
    ) -> dict[str, Any]:
        """Use to estimate run time; for selecting tests by filters, use search_test_cases first."""
        if minutes_manual < 0 or minutes_automated < 0:
            raise ValueError("execution minutes cannot be negative")
        if bool(issue_keys) == bool(filters):
            raise ValueError("provide exactly one of issue_keys or filters")
        if issue_keys:
            rows, missing = repository.get_by_keys(issue_keys)
            if missing:
                raise ValueError(f"Unknown issue keys: {missing}")
        else:
            rows = repository.filter_rows(filters)
        by_module: dict[str, dict[str, int]] = {}
        for row in rows:
            module = row["Component"]
            item = by_module.setdefault(module, {"tests": 0, "manual": 0, "automated": 0, "minutes": 0})
            automated = row["Status"] == "Automated"
            minutes = minutes_automated if automated else minutes_manual
            item["tests"] += 1
            item["automated" if automated else "manual"] += 1
            item["minutes"] += minutes
        return {
            "count": len(rows), "manual": sum(x["manual"] for x in by_module.values()),
            "automated": sum(x["automated"] for x in by_module.values()),
            "estimated_minutes": sum(x["minutes"] for x in by_module.values()),
            "by_module": by_module,
        }

    @mcp.tool
    def find_duplicate_tests(
        module: str | None = None, mode: Literal["exact", "same_scenario"] = "exact",
    ) -> dict[str, Any]:
        """Use to locate duplicate catalog rows; for scenario variants, use get_similar_test_cases."""
        rows = repository.filter_rows(TestFilter(module=module, include_deprecated=True))
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if mode == "exact":
                key = (row["Summary"], row["Browser"], row["Device"])
            else:
                key = (row["Summary"],)
            groups[key].append(row)
        duplicates = []
        for group in groups.values():
            if len(group) > 1:
                group.sort(key=lambda row: (row["Status"] == "Deprecated", row["Issue Key"]))
                duplicates.append({
                    "keeper": compact_row(group[0]),
                    "duplicates": [compact_row(row) for row in group[1:]],
                })
        return {"mode": mode, "groups": len(duplicates), "results": duplicates}

    @mcp.tool
    def find_coverage_gaps(module: str | None = None) -> dict[str, Any]:
        """Use to find feature/type and browser/device coverage gaps; for counts, use get_test_stats."""
        rows = repository.filter_rows(TestFilter(module=module))
        features = sorted({row["_feature"] for row in rows})
        feature_types = {(row["_feature"], row["Test Type"]) for row in rows}
        feature_priority = {(row["_feature"], row["Priority"]) for row in rows}
        gaps = [
            {"feature": feature, "test_type": test_type}
            for feature in features for test_type in TEST_TYPES
            if (feature, test_type) not in feature_types
        ]
        no_highest = [feature for feature in features if (feature, "Highest") not in feature_priority]
        no_security = [feature for feature in features if (feature, "Security") not in feature_types]
        no_accessibility = [feature for feature in features if (feature, "Accessibility") not in feature_types]
        return {
            "module": module, "features": len(features), "missing_feature_test_types": gaps,
            "features_without_highest": no_highest, "features_without_security": no_security,
            "features_without_accessibility": no_accessibility,
            "browser_device": get_browser_device_matrix(module=module)["empty_cells"],
        }

    @mcp.tool
    def validate_test_case(test_case: TestCaseDraft) -> dict[str, Any]:
        """Use to lint a test draft before saving; to add it after review, use add_test_cases."""
        return validate_draft(test_case)

    @mcp.tool
    def get_test_case_template(
        module: str, feature: str, test_type: str,
        browser: str = "Chrome 148", device: str = "desktop",
    ) -> dict[str, Any]:
        """Use to learn the VWO case shape; to query real examples, use search_test_cases."""
        sample_rows = repository.filter_rows(TestFilter(module=module, test_type=[test_type]))
        examples = [_full_row(row) for row in sample_rows[:3]]
        template = {
            "Issue Type": "Test", "Issue Key": "<assigned on save>",
            "Summary": f"[{repository.resolve_module(module) or module}] {test_type}: {feature}",
            "Description": f"As a QA engineer, verify {feature} in {module}.",
            "Priority": "Medium", "Component": repository.resolve_module(module) or module,
            "Labels": "", "Test Type": test_type, "Preconditions": "",
            "Steps": "1. ... | 2. ... | 3. ...",
            "Expected Result": "Describe an observable outcome.",
            "Browser": browser, "Device": device, "Status": "Draft",
        }
        return {
            "template": template, "examples": examples,
            "rules": {"steps_separator": " | ", "summary_format": "[Module] Type: feature", "draft_status": "Draft"},
        }

    if can_write:
        @mcp.tool
        def add_test_cases(test_cases: list[TestCaseDraft], dry_run: bool = True) -> dict[str, Any]:
            """Use only after the user approves drafts; for existing cases, use update_test_case."""
            if not 1 <= len(test_cases) <= 25:
                raise ValueError("test_cases must contain 1 to 25 drafts")
            validations = [validate_draft(draft) for draft in test_cases]
            invalid = [item for item in validations if not item["valid"]]
            if invalid:
                return {"saved": False, "validations": validations, "errors": invalid}
            if dry_run:
                return {"saved": False, "dry_run": True, "validations": validations, "drafts": [item.model_dump() for item in test_cases]}
            added = repository.add_cases(test_cases)
            return {"saved": True, "count": len(added), "test_cases": [compact_row(row) for row in added]}

        @mcp.tool
        def update_test_case(issue_key: str, changes: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
            """Use only after user approval to change an existing case; for new cases, use add_test_cases."""
            found, missing = repository.get_by_keys([issue_key])
            if missing:
                raise ValueError(f"Unknown issue key: {issue_key}")
            before = found[0]
            allowed = {"summary", "description", "priority", "component", "labels", "test_type", "preconditions", "steps", "expected_result", "browser", "device", "status"}
            if set(changes) - allowed:
                raise ValueError(f"Unsupported fields: {sorted(set(changes) - allowed)}")
            preview = {key: value for key, value in before.items() if not key.startswith("_")}
            aliases = {
                "summary": "Summary", "description": "Description", "priority": "Priority",
                "component": "Component", "labels": "Labels", "test_type": "Test Type",
                "preconditions": "Preconditions", "steps": "Steps", "expected_result": "Expected Result",
                "browser": "Browser", "device": "Device", "status": "Status",
            }
            preview.update({aliases[key]: value for key, value in changes.items()})
            if dry_run:
                return {"saved": False, "dry_run": True, "before": _full_row(before), "after": preview}
            old, new = repository.update_case(issue_key, changes)
            return {"saved": True, "before": _full_row(old), "after": _full_row(new)}

    @mcp.tool
    def export_test_cases(
        issue_keys: list[str] | None = None,
        filters: TestFilter | None = None,
        format: Literal["csv", "jira_csv", "markdown", "json"] = "json",
    ) -> dict[str, Any]:
        """Use to export a selected set; for Gherkin or code, use convert_to_gherkin or generate_automation_stub."""
        if bool(issue_keys) == bool(filters):
            raise ValueError("provide exactly one of issue_keys or filters")
        if issue_keys:
            rows, missing = repository.get_by_keys(issue_keys)
            if missing:
                raise ValueError(f"Unknown issue keys: {missing}")
        else:
            rows = repository.filter_rows(filters)
        if len(rows) > 5000:
            raise ValueError("export is capped at 5000 rows per request")
        records = [{field: row[field] for field in CSV_FIELDS} for row in rows]
        if format == "json":
            content = json.dumps(records, ensure_ascii=False, indent=2)
        elif format == "markdown":
            content = "| Key | Summary | Priority | Type | Status |\n|---|---|---|---|---|\n" + "\n".join(
                f"| {row['Issue Key']} | {row['Summary']} | {row['Priority']} | {row['Test Type']} | {row['Status']} |"
                for row in rows
            )
        else:
            handle = io.StringIO()
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(records)
            content = handle.getvalue()
        if len(rows) > 50:
            extension = "csv" if format in {"csv", "jira_csv"} else format
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            file_path = export_dir / f"test-cases-{timestamp}.{extension}"
            file_path.write_text(content, encoding="utf-8", newline="")
            return {
                "format": format, "count": len(rows),
                "file_path": str(file_path.resolve()),
            }
        return {"format": format, "count": len(rows), "content": content}

    @mcp.tool
    def convert_to_gherkin(issue_keys: list[str]) -> dict[str, Any]:
        """Use to convert selected cases to Gherkin; for raw rows, use export_test_cases."""
        if not 1 <= len(issue_keys) <= 10:
            raise ValueError("issue_keys must contain 1 to 10 keys")
        rows, missing = repository.get_by_keys(issue_keys)
        if missing:
            raise ValueError(f"Unknown issue keys: {missing}")
        chunks = []
        for row in rows:
            steps = parse_steps(row["Steps"])
            lines = [
                f"  Scenario: {row['Summary']}",
                f"    Given {row['Preconditions'] or 'the user is ready to test'}",
            ]
            for index, step in enumerate(steps):
                keyword = "When" if index == 0 else "And"
                lines.append(f"    {keyword} {step}")
            lines.append(f"    Then {row['Expected Result']}")
            chunks.append(f"Feature: {row['Component']}\n\n" + "\n".join(lines))
        return {"count": len(rows), "gherkin": "\n\n".join(chunks)}

    @mcp.tool
    def generate_automation_stub(
        issue_key: str, framework: Literal["pytest_playwright", "playwright_ts"],
    ) -> dict[str, Any]:
        """Use for a runnable-structure draft; for Gherkin export, use convert_to_gherkin."""
        found, missing = repository.get_by_keys([issue_key])
        if missing:
            raise ValueError(f"Unknown issue key: {issue_key}")
        row = found[0]
        if framework == "playwright_ts":
            code = (
                "import { test, expect } from '@playwright/test';\n\n"
                f"test('{row['Summary']}', async ({{ page }}) => {{\n"
                f"  // Preconditions: {row['Preconditions']}\n"
                + "".join(f"  // Step: {step}\n" for step in parse_steps(row["Steps"]))
                + f"  // Expected: {row['Expected Result']}\n"
                "});\n"
            )
        else:
            code = (
                "import pytest\n\n"
                f"def test_{issue_key.lower().replace('-', '_')}(page):\n"
                f"    \"\"\"{row['Summary']}\"\"\"\n"
                f"    # Preconditions: {row['Preconditions']}\n"
                + "".join(f"    # Step: {step}\n" for step in parse_steps(row["Steps"]))
                + f"    # Expected: {row['Expected Result']}\n"
            )
        return {"issue_key": issue_key, "framework": framework, "code": code}

    @mcp.resource("tc://schema")
    def schema_resource() -> str:
        """CSV column names, allowed values and formats."""
        return json.dumps({
            "columns": CSV_FIELDS, "priorities": PRIORITIES, "test_types": TEST_TYPES,
            "browsers": BROWSERS, "devices": DEVICES,
            "summary_format": "[Module] Type: feature action",
            "steps_format": "1. step | 2. step | 3. step",
        }, indent=2)

    @mcp.resource("tc://modules")
    def modules_resource() -> str:
        """Modules and feature names in the catalog."""
        return json.dumps(list_modules(), indent=2)

    @mcp.resource("tc://stats/summary")
    def stats_resource() -> str:
        """Overall live test catalog statistics."""
        return json.dumps(_profile(repository.filter_rows()), indent=2)

    @mcp.resource("tc://test/{issue_key}")
    def test_case_resource(issue_key: str) -> str:
        """A complete catalog test case addressed by issue key."""
        result = get_test_case([issue_key])
        if result["unknown_keys"]:
            raise ValueError(f"Unknown issue key: {issue_key}")
        return json.dumps(result["test_cases"][0], indent=2)

    @mcp.prompt
    def generate_test_cases(requirement: str, module: str, count: int = 5) -> str:
        """Draft test cases from a requirement using the catalog's format."""
        example = get_test_case_template(module, requirement, "Functional")
        return (
            f"Draft {count} test cases for the requirement below. Follow the VWO "
            f"schema, include positive and negative cases, and keep all output as "
            f"drafts for human review.\n\nRequirement: {requirement}\n\n"
            f"Template and examples:\n{json.dumps(example, indent=2)}"
        )

    @mcp.prompt
    def plan_release_run(modules: str = "all", suite_type: str = "regression") -> str:
        """Prepare a release test run proposal and explain its coverage."""
        return (
            f"Create a {suite_type} test run for modules={modules}. Use "
            "build_test_suite, review its makeup and estimated effort, and explain "
            "coverage risks and any assumptions before requesting human approval."
        )

    @mcp.prompt
    def review_module_coverage(module: str) -> str:
        """Review a module's coverage using the catalog's actual data."""
        return (
            f"Review coverage for {module}. Use find_coverage_gaps and "
            "get_browser_device_matrix, then report observed gaps without "
            "inventing tests or treating missing data as covered."
        )

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="TestCreator MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default=os.getenv("TC_MCP_TRANSPORT", "stdio"))
    parser.add_argument("--host", default=os.getenv("TC_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("TC_MCP_PORT", "8000")))
    parser.add_argument("--allow-write", action="store_true")
    parser.add_argument("--data-path", type=Path)
    parser.add_argument("--overlay-path", type=Path)
    args = parser.parse_args()
    mcp = create_server(args.data_path, args.overlay_path, args.allow_write or None)
    kwargs: dict[str, Any] = {}
    if args.transport != "stdio":
        if args.host not in {"127.0.0.1", "localhost", "::1"}:
            parser.error("This local server binds to loopback only; use a separately authenticated deployment for remote access.")
        kwargs.update(host=args.host, port=args.port)
        if args.transport == "http":
            kwargs["stateless_http"] = True
    mcp.run(transport=args.transport, **kwargs)


if __name__ == "__main__":
    main()
