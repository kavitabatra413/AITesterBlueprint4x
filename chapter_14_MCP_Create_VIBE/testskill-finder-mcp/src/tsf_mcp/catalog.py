"""Read and validate the local SKILL.md catalog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

FRONTMATTER = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)
TRIGGER = re.compile(r'"([^"]{3,120})"')
STLC_ORDER = [
    "Requirement Analysis", "Test Planning", "Test Design",
    "Test Case Development", "Test Execution", "Defect Management", "Test Closure",
]


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    license: str
    metadata: dict[str, Any]
    category: str
    kind: str
    source: str
    path: PurePosixPath
    folder: Path
    content: str
    files: tuple[str, ...]
    triggers: tuple[str, ...]

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "kind": self.kind,
            "source": self.source,
            "license": self.license,
            "path": self.path.as_posix(),
            "files": list(self.files),
            "triggers": list(self.triggers),
        }


class SkillCatalog:
    def __init__(self, root: Path, skills: list[Skill], upstream: dict[str, Any]) -> None:
        self.root = root.resolve()
        self.skills = tuple(sorted(skills, key=lambda skill: skill.name))
        self.by_name = {skill.name: skill for skill in self.skills}
        self.upstream_manifest = upstream

    @property
    def categories(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for skill in self.skills:
            result.setdefault(skill.category, []).append(skill.name)
        return {category: sorted(names) for category, names in sorted(result.items(), key=_category_sort)}

    def get(self, name: str) -> Skill:
        skill = self.by_name.get(name)
        if skill is None:
            suggestions = sorted(self.by_name, key=lambda candidate: _edit_distance(name, candidate))[:3]
            raise KeyError(f"Unknown skill {name!r}. Did you mean: {', '.join(suggestions)}?")
        return skill

    def reload(self) -> "SkillCatalog":
        return load_catalog(self.root)


def _category_sort(item: tuple[str, list[str]]) -> tuple[int, str]:
    category = item[0]
    try:
        return (STLC_ORDER.index(category), category)
    except ValueError:
        return (len(STLC_ORDER), category.casefold())


def _edit_distance(left: str, right: str) -> int:
    row = list(range(len(right) + 1))
    for i, char_left in enumerate(left, 1):
        new = [i]
        for j, char_right in enumerate(right, 1):
            new.append(min(new[-1] + 1, row[j] + 1, row[j - 1] + (char_left != char_right)))
        row = new
    return row[-1]


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / ".upstream.json"
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"Invalid upstream manifest: {path}")
    return manifest


def _metadata(text: str, path: Path) -> dict[str, Any]:
    match = FRONTMATTER.match(text)
    if match is None:
        raise ValueError(f"Missing YAML frontmatter: {path}")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML frontmatter in {path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in frontmatter: {path}")
    return data


def load_catalog(root: Path) -> SkillCatalog:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Skills directory not found: {root}")
    manifest = _load_manifest(root)
    upstream_files = set(manifest.get("files", []))
    skills: list[Skill] = []
    names: set[str] = set()
    for path in sorted(root.rglob("SKILL.md")):
        relative = path.relative_to(root).as_posix()
        content = path.read_text(encoding="utf-8")
        data = _metadata(content, path)
        name, description = data.get("name"), data.get("description")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Missing skill name: {path}")
        if name in names:
            raise ValueError(f"Duplicate skill name {name!r}: {path}")
        names.add(name)
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Missing skill description: {path}")
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"Missing metadata mapping: {path}")
        has_phase = isinstance(metadata.get("stlc-phase"), str)
        has_pack = isinstance(metadata.get("pack"), str)
        if has_phase == has_pack:
            raise ValueError(f"Exactly one of metadata.stlc-phase or metadata.pack is required: {path}")
        category = metadata["stlc-phase"] if has_phase else str(metadata["pack"])
        kind = "stlc" if has_phase else "framework"
        folder = path.parent.resolve()
        support_files = tuple(
            candidate.relative_to(folder).as_posix()
            for candidate in sorted(folder.rglob("*"))
            if candidate.is_file() and candidate.name != "SKILL.md"
        )
        skills.append(
            Skill(
                name=name.strip(),
                description=description.strip(),
                license=str(data.get("license", "")),
                metadata=metadata,
                category=category,
                kind=kind,
                source="upstream" if relative in upstream_files else "local",
                path=PurePosixPath(relative),
                folder=folder,
                content=content,
                files=support_files,
                triggers=tuple(TRIGGER.findall(description)),
            )
        )
    if not skills:
        raise ValueError(f"No SKILL.md files found in {root}")
    return SkillCatalog(root, skills, manifest)


def resolve_skill_file(skill: Skill, relative_file: str) -> Path:
    relative_file = relative_file.replace("\\", "/")
    candidate_path = PurePosixPath(relative_file)
    if candidate_path.is_absolute() or any(part in {"..", ""} for part in candidate_path.parts):
        raise ValueError("File path must stay inside the selected skill folder")
    candidate = (skill.folder / Path(*candidate_path.parts)).resolve()
    if not candidate.is_relative_to(skill.folder) or not candidate.is_file():
        raise FileNotFoundError(f"Supporting skill file not found: {relative_file}")
    return candidate
