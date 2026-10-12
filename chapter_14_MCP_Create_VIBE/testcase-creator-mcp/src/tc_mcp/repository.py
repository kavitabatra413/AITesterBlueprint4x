"""Load, normalize, filter, and safely overlay VWO test cases."""

from __future__ import annotations

import csv
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from threading import RLock
from typing import Any, Literal

from pydantic import BaseModel, Field


CSV_FIELDS = [
    "Issue Type", "Issue Key", "Summary", "Description", "Priority", "Component",
    "Labels", "Test Type", "Preconditions", "Steps", "Expected Result", "Browser",
    "Device", "Status",
]
PRIORITY_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Highest": 3}
PRIORITIES = list(PRIORITY_ORDER)
TEST_TYPES = [
    "Functional", "Negative", "UI/UX", "API", "Boundary", "Regression",
    "Security", "Accessibility", "Performance",
]
BROWSERS = ["Chrome 148", "Firefox 147", "Safari 19", "Edge 148"]
DEVICES = ["desktop", "mobile (Android)", "mobile (iOS)", "tablet"]
STAT_FIELDS = {
    "module": "Component", "priority": "Priority", "test_type": "Test Type",
    "status": "Status", "browser": "Browser", "device": "Device", "feature": "_feature",
}
MODULE_ALIASES = {
    "ab": "A/B Testing", "ab testing": "A/B Testing", "a/b": "A/B Testing",
    "a/b testing": "A/B Testing", "billing": "Account & Billing",
    "sdk": "SDK / Server-Side API", "server side api": "SDK / Server-Side API",
    "account": "Account & Billing", "heatmap": "Heatmaps",
}
SUMMARY_PATTERN = re.compile(r"^\[(?P<module>.+?)\]\s+(?P<type>[^:]+):\s*(?P<feature>.+)$")


class TestFilter(BaseModel):
    """Shared filters for catalog querying."""

    __test__ = False
    module: str | list[str] | None = None
    feature: str | None = None
    priority: list[str] | None = None
    min_priority: str | None = None
    max_priority: str | None = None
    test_type: list[str] | None = None
    browser: str | list[str] | None = None
    device: str | list[str] | None = None
    status: list[str] | None = None
    label: str | None = None
    include_deprecated: bool = False
    include_duplicates: bool = True


class TestCaseDraft(BaseModel):
    """Fields needed to add a test case to the overlay."""

    __test__ = False
    summary: str
    description: str = ""
    priority: str = "Medium"
    component: str
    labels: str | list[str] = ""
    test_type: str
    preconditions: str = ""
    steps: str | list[str]
    expected_result: str
    browser: str = "Chrome 148"
    device: str = "desktop"
    status: str = "Draft"


def _csv_bool(value: Any) -> bool:
    return str(value).strip().casefold() in {"true", "1", "yes"}


def _as_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    return list(value)


def _priority_in_range(value: str, minimum: str | None, maximum: str | None) -> bool:
    rank = PRIORITY_ORDER.get(value)
    return (
        rank is not None
        and (minimum is None or rank >= PRIORITY_ORDER.get(minimum, 0))
        and (maximum is None or rank <= PRIORITY_ORDER.get(maximum, 3))
    )


def normalize_row(source: dict[str, Any]) -> dict[str, Any]:
    row = {field: str(source.get(field, "") or "").strip() for field in CSV_FIELDS}
    match = SUMMARY_PATTERN.match(row["Summary"])
    row["_feature"] = match.group("feature").strip() if match else row["Summary"]
    row["_summary_module"] = match.group("module").strip() if match else ""
    if row["Component"].casefold() in {"a", "a/b", "ab"}:
        row["Component"] = "A/B Testing"
    labels = []
    for label in row["Labels"].split():
        if label not in labels:
            labels.append(label)
    row["Labels"] = " ".join(labels)
    if row["Test Type"]:
        label_name = re.sub(r"[^a-z0-9]+", "-", row["Component"].casefold()).strip("-")
        type_label = re.sub(r"[^a-z0-9]+", "-", row["Test Type"].casefold()).strip("-")
        labels = [label for label in row["Labels"].split() if label != "a"]
        if label_name not in labels:
            labels.append(label_name)
        if type_label not in labels:
            labels.append(type_label)
        row["Labels"] = " ".join(labels)
    return row


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue_key": row["Issue Key"], "summary": row["Summary"],
        "module": row["Component"], "feature": row["_feature"],
        "priority": row["Priority"], "test_type": row["Test Type"],
        "status": row["Status"], "browser": row["Browser"], "device": row["Device"],
    }


class TestRepository:
    __test__ = False

    def __init__(self, data_path: Path, overlay_path: Path) -> None:
        self.data_path = data_path.resolve()
        self.overlay_path = overlay_path.resolve()
        self._lock = RLock()
        self._signature: tuple[int, int] | None = None
        self._base: list[dict[str, Any]] = []
        self._overlay: dict[str, dict[str, Any]] = {}
        self.refresh()

    def refresh(self) -> None:
        with self._lock:
            if not self.data_path.is_file():
                raise FileNotFoundError(f"Test case CSV not found: {self.data_path}")
            with self.data_path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                missing = set(CSV_FIELDS) - set(reader.fieldnames or [])
                if missing:
                    raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
                self._base = [normalize_row(row) for row in reader]
            self._overlay = {}
            if self.overlay_path.exists():
                with self.overlay_path.open(encoding="utf-8-sig", newline="") as handle:
                    self._overlay = {
                        row["Issue Key"]: normalize_row(row)
                        for row in csv.DictReader(handle)
                        if row.get("Issue Key")
                    }
            data_stat = self.data_path.stat()
            overlay_mtime = self.overlay_path.stat().st_mtime_ns if self.overlay_path.exists() else 0
            self._signature = (data_stat.st_mtime_ns, overlay_mtime)

    def _refresh_if_changed(self) -> None:
        try:
            data_stat = self.data_path.stat()
            overlay_mtime = self.overlay_path.stat().st_mtime_ns if self.overlay_path.exists() else 0
        except OSError:
            self.refresh()
            return
        if self._signature != (data_stat.st_mtime_ns, overlay_mtime):
            self.refresh()

    def all_rows(self) -> list[dict[str, Any]]:
        self._refresh_if_changed()
        with self._lock:
            rows = {row["Issue Key"]: dict(row) for row in self._base}
            rows.update({key: dict(row) for key, row in self._overlay.items()})
            return list(rows.values())

    def resolve_module(self, value: str) -> str | None:
        cleaned = value.strip()
        modules = {row["Component"] for row in self.all_rows()}
        lookup = {module.casefold(): module for module in modules}
        alias = MODULE_ALIASES.get(cleaned.casefold(), cleaned)
        return lookup.get(alias.casefold())

    def filter_rows(self, filters: TestFilter | None = None) -> list[dict[str, Any]]:
        filters = filters or TestFilter()
        rows = self.all_rows()
        modules = _as_list(filters.module)
        resolved_modules = {self.resolve_module(module) or module for module in modules or []}
        wanted_priority = set(filters.priority or [])
        wanted_types = {value.casefold() for value in filters.test_type or []}
        wanted_status = {value.casefold() for value in filters.status or []}
        wanted_browsers = {value.casefold() for value in _as_list(filters.browser) or []}
        wanted_devices = {value.casefold() for value in _as_list(filters.device) or []}
        result = []
        for row in rows:
            if modules and row["Component"] not in resolved_modules:
                continue
            if filters.feature and filters.feature.casefold() not in row["_feature"].casefold():
                continue
            if wanted_priority and row["Priority"] not in wanted_priority:
                continue
            if (filters.min_priority or filters.max_priority) and not _priority_in_range(
                row["Priority"], filters.min_priority, filters.max_priority
            ):
                continue
            if wanted_types and row["Test Type"].casefold() not in wanted_types:
                continue
            if wanted_status and row["Status"].casefold() not in wanted_status:
                continue
            if wanted_browsers and row["Browser"].casefold() not in wanted_browsers:
                continue
            if wanted_devices and row["Device"].casefold() not in wanted_devices:
                continue
            if filters.label and filters.label.casefold() not in row["Labels"].casefold():
                continue
            if not filters.include_deprecated and row["Status"].casefold() == "deprecated":
                continue
            result.append(row)
        if not filters.include_duplicates:
            seen: set[tuple[str, str, str]] = set()
            unique = []
            for row in result:
                key = (row["Summary"], row["Browser"], row["Device"])
                if key not in seen:
                    seen.add(key)
                    unique.append(row)
            result = unique
        return result

    def get_by_keys(self, keys: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
        lookup = {row["Issue Key"].casefold(): row for row in self.all_rows()}
        found = [lookup[key.casefold()] for key in keys if key.casefold() in lookup]
        missing = [key for key in keys if key.casefold() not in lookup]
        return found, missing

    def save_overlay(self, changes: dict[str, dict[str, Any]]) -> None:
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            merged = dict(self._overlay)
            merged.update(changes)
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{self.overlay_path.name}.", suffix=".tmp", dir=self.overlay_path.parent
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                    writer.writeheader()
                    for key in sorted(merged):
                        writer.writerow({field: merged[key].get(field, "") for field in CSV_FIELDS})
                os.replace(temp_name, self.overlay_path)
            except Exception:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass
                raise
            self.refresh()

    def add_cases(self, drafts: list[TestCaseDraft]) -> list[dict[str, Any]]:
        rows = self.all_rows()
        next_number = max(
            [int(match.group(1)) for row in rows
             if (match := re.fullmatch(r"VWO-(\d+)", row["Issue Key"]))]
            + [6000]
        ) + 1
        additions = {}
        for draft in drafts:
            issue_key = f"VWO-{next_number}"
            next_number += 1
            source = {
                "Issue Type": "Test", "Issue Key": issue_key,
                "Summary": draft.summary, "Description": draft.description,
                "Priority": draft.priority, "Component": draft.component,
                "Labels": " ".join(draft.labels) if isinstance(draft.labels, list) else draft.labels,
                "Test Type": draft.test_type, "Preconditions": draft.preconditions,
                "Steps": " | ".join(draft.steps) if isinstance(draft.steps, list) else draft.steps,
                "Expected Result": draft.expected_result, "Browser": draft.browser,
                "Device": draft.device, "Status": draft.status,
            }
            additions[issue_key] = normalize_row(source)
        self.save_overlay(additions)
        return list(additions.values())

    def update_case(self, issue_key: str, changes: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        found, missing = self.get_by_keys([issue_key])
        if missing:
            raise ValueError(f"Unknown issue key: {issue_key}")
        before = found[0]
        aliases = {
            "summary": "Summary", "description": "Description", "priority": "Priority",
            "component": "Component", "labels": "Labels", "test_type": "Test Type",
            "preconditions": "Preconditions", "steps": "Steps",
            "expected_result": "Expected Result", "browser": "Browser",
            "device": "Device", "status": "Status",
        }
        unknown = set(changes) - set(aliases)
        if unknown:
            raise ValueError(f"Unsupported fields: {sorted(unknown)}")
        updated = {field: before.get(field, "") for field in CSV_FIELDS}
        for key, value in changes.items():
            field = aliases[key]
            if key == "steps" and isinstance(value, list):
                value = " | ".join(str(step) for step in value)
            elif key == "labels" and isinstance(value, list):
                value = " ".join(str(label) for label in value)
            updated[field] = str(value)
        updated = normalize_row(updated)
        self.save_overlay({issue_key: updated})
        return before, updated


def validate_draft(draft: TestCaseDraft) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if draft.priority not in PRIORITIES:
        errors.append(f"priority must be one of {PRIORITIES}")
    if draft.test_type not in TEST_TYPES:
        errors.append(f"test_type must be one of {TEST_TYPES}")
    if draft.browser not in BROWSERS:
        errors.append(f"browser must be one of {BROWSERS}")
    if draft.device not in DEVICES:
        errors.append(f"device must be one of {DEVICES}")
    if draft.status not in {"Ready", "Automated", "Draft", "Deprecated"}:
        errors.append("status must be Ready, Automated, Draft, or Deprecated")
    if not draft.summary.strip():
        errors.append("summary is required")
    if not draft.component.strip():
        errors.append("component is required")
    steps = draft.steps if isinstance(draft.steps, list) else draft.steps.split("|")
    if len([step for step in steps if str(step).strip()]) < 3:
        warnings.append("Fewer than 3 non-empty steps are provided.")
    if len(draft.expected_result.strip()) < 15 or draft.expected_result.casefold().startswith(
        ("works as expected", "should work", "it works")
    ):
        warnings.append("Expected result may be too generic; describe an observable outcome.")
    if not SUMMARY_PATTERN.match(draft.summary):
        warnings.append("Summary should follow '[Module] Type: feature action'.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    field = STAT_FIELDS[key]
    return dict(sorted(Counter(str(row[field]) for row in rows).items()))


def available_values(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    fields = {
        "priorities": "Priority", "test_types": "Test Type", "browsers": "Browser",
        "devices": "Device", "statuses": "Status", "modules": "Component",
    }
    return {key: sorted({row[field] for row in rows}) for key, field in fields.items()}


def parse_steps(value: str) -> list[str]:
    return [step.strip() for step in value.split("|") if step.strip()]
