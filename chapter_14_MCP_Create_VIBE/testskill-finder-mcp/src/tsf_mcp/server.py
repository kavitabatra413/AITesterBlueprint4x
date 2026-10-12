"""FastMCP server for discovering, inspecting, and applying QA skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import base64
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Literal
from urllib.parse import quote

import httpx
import yaml
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse

from tsf_mcp.catalog import STLC_ORDER, Skill, SkillCatalog, load_catalog, resolve_skill_file
from tsf_mcp.search import best_for_task, search


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SKILLS = PROJECT_ROOT / "skills"
PACKAGED_SKILLS = Path(__file__).resolve().parent / "skills"
DEFAULT_SKILLS = LOCAL_SKILLS if LOCAL_SKILLS.is_dir() else PACKAGED_SKILLS
REPO_OWNER = "PramodDutta"
REPO_NAME = "skillmasterclass"
UPSTREAM_PATH = "skillmasterclass/skills"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _section(content: str, header: str) -> str:
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip().casefold().startswith(f"## {header}".casefold()):
            section = []
            for candidate in lines[index + 1 :]:
                if candidate.startswith("## "):
                    break
                section.append(candidate)
            return "\n".join(section).strip()
    return ""


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _safe_skill_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"..", ""} for part in path.parts):
        raise ValueError("Invalid skill path")
    return path


def _skill_result(skill: Skill) -> dict[str, Any]:
    return {
        **skill.summary(),
        "when_to_use": _section(skill.content, "When to use"),
        "workflow": _section(skill.content, "Workflow"),
        "output_shape": _section(skill.content, "Output shape"),
        "guardrails": _section(skill.content, "Guardrails"),
    }


def _catalog_markdown(catalog: SkillCatalog) -> str:
    lines = ["# QA Skill Catalog", "", f"{len(catalog.skills)} skills in the local source-of-truth folder.", ""]
    for category, names in catalog.categories.items():
        lines.extend([f"## {category} ({len(names)})", ""])
        for name in names:
            skill = catalog.by_name[name]
            lines.append(f"- **{name}** — {skill.description}")
        lines.append("")
    return "\n".join(lines)


def _stlc_pipeline(catalog: SkillCatalog) -> dict[str, Any]:
    phases = []
    for index, phase in enumerate(STLC_ORDER):
        phases.append({
            "order": index + 1, "phase": phase,
            "skills": [skill.summary() for skill in catalog.skills if skill.category == phase],
            "next_phase": STLC_ORDER[index + 1] if index + 1 < len(STLC_ORDER) else None,
        })
    packs: dict[str, list[str]] = {}
    for skill in catalog.skills:
        if skill.kind == "framework":
            packs.setdefault(skill.category, []).append(skill.name)
    return {"phases": phases, "framework_packs": packs}


def _source_counts(catalog: SkillCatalog) -> dict[str, int]:
    return {source: sum(skill.source == source for skill in catalog.skills) for source in ("upstream", "local")}


def _validate_skill_text(name: str, description: str, category: str, kind: str, content: str) -> list[str]:
    errors = []
    if not SLUG.fullmatch(name):
        errors.append("name must be a lowercase hyphenated slug")
    if not description.strip() or "use when" not in description.casefold():
        errors.append("description must be non-empty and include 'Use when' trigger phrases")
    if not category.strip():
        errors.append("category is required")
    if kind not in {"stlc", "framework"}:
        errors.append("kind must be 'stlc' or 'framework'")
    try:
        frontmatter_match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", content, re.DOTALL)
        if not frontmatter_match:
            errors.append("YAML frontmatter is missing")
        else:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            if not isinstance(frontmatter, dict) or frontmatter.get("name") != name:
                errors.append("frontmatter name must match the skill id")
            metadata = frontmatter.get("metadata") if isinstance(frontmatter, dict) else None
            if not isinstance(metadata, dict):
                errors.append("frontmatter metadata mapping is required")
            elif ("stlc-phase" in metadata) == ("pack" in metadata):
                errors.append("frontmatter metadata must contain exactly one of stlc-phase or pack")
    except yaml.YAMLError as error:
        errors.append(f"invalid frontmatter YAML: {error}")
    for heading in ("When to use", "Workflow", "Output shape", "Guardrails"):
        if f"## {heading}".casefold() not in content.casefold():
            errors.append(f"missing required section: {heading}")
    return errors


def create_server(skills_dir: Path | None = None, allow_write: bool | None = None) -> FastMCP:
    root = (skills_dir or Path(os.environ.get("TSF_SKILLS_DIR", DEFAULT_SKILLS))).resolve()
    allow_mutations = (
        os.environ.get("TSF_ALLOW_WRITE", "false").casefold() == "true"
        if allow_write is None else allow_write
    )
    catalog = load_catalog(root)
    mcp = FastMCP(
        "TestSkill Finder",
        instructions=(
            "Find QA skills from the local skills source of truth. Search by task or "
            "keyword, inspect the skill instructions and supporting files, then follow "
            "its workflow and human-review guardrails."
        ),
    )

    @mcp.custom_route("/", methods=["GET"], include_in_schema=False)
    async def landing_page(_request: Request) -> HTMLResponse:
        """Explain the MCP endpoint to people who open the server in a browser."""
        return HTMLResponse(
            "<!doctype html><html><head><title>TestSkill Finder MCP</title></head>"
            "<body><h1>TestSkill Finder MCP</h1><p>This is an MCP server, not a web app.</p>"
            "<p>Connect an MCP client using Streamable HTTP at <code>/mcp</code>.</p>"
            "<p>For MCP Inspector, select Streamable HTTP and use "
            "<code>http://127.0.0.1:8110/mcp</code>.</p></body></html>"
        )

    def current_catalog() -> SkillCatalog:
        nonlocal catalog
        catalog = load_catalog(root)
        return catalog

    @mcp.tool
    def list_categories() -> dict[str, Any]:
        """Use to browse available lifecycle phases and framework packs."""
        active = current_catalog()
        return {
            "total_skills": len(active.skills),
            "categories": [
                {"name": category, "count": len(names), "skills": names}
                for category, names in active.categories.items()
            ],
        }

    @mcp.tool
    def list_skills(
        category: str | None = None,
        kind: Literal["stlc", "framework"] | None = None,
        source: Literal["upstream", "local"] | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Use to browse/filter skills; for natural-language matching, use search_skills."""
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("limit must be 1..100 and offset nonnegative")
        active = current_catalog()
        items = list(active.skills)
        if category:
            items = [skill for skill in items if skill.category.casefold() == category.casefold()]
        if kind:
            items = [skill for skill in items if skill.kind == kind]
        if source:
            items = [skill for skill in items if skill.source == source]
        if query:
            tokens = query.casefold().split()
            items = [
                skill for skill in items
                if all(token in (skill.name + " " + skill.description).casefold() for token in tokens)
            ]
        return {
            "total": len(items), "offset": offset,
            "skills": [skill.summary() for skill in items[offset : offset + limit]],
        }

    @mcp.tool
    def get_catalog_stats() -> dict[str, Any]:
        """Use to see total skills and counts by type, category, and source."""
        active = current_catalog()
        by_kind = {kind: sum(skill.kind == kind for skill in active.skills) for kind in ("stlc", "framework")}
        return {
            "total": len(active.skills),
            "by_kind": by_kind,
            "by_category": {category: len(names) for category, names in active.categories.items()},
            "by_source": _source_counts(active),
            "upstream": {
                "repository": active.upstream_manifest.get("repo"),
                "ref": active.upstream_manifest.get("ref"),
                "commit": active.upstream_manifest.get("commit"),
                "synced_at": active.upstream_manifest.get("synced_at"),
            },
        }

    @mcp.tool
    def search_skills(query: str, limit: int = 10, category: str | None = None) -> dict[str, Any]:
        """Use for keyword searches like "Playwright API" or "test plan creator"."""
        active = current_catalog()
        results = search(active, query, limit=50)
        if category:
            results = [item for item in results if item[0].category.casefold() == category.casefold()]
        results = results[:limit]
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        return {
            "query": query, "count": len(results),
            "results": [
                {**skill.summary(), "score": round(score, 3), "matched_fields": sorted(set(fields))}
                for skill, score, fields in results
            ],
        }

    @mcp.tool
    def find_skill_for_task(task: str, limit: int = 5) -> dict[str, Any]:
        """Use when the user describes a QA task and needs the best matching skills."""
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        active = current_catalog()
        matches = best_for_task(active, task, limit)
        return {
            "task": task, "count": len(matches),
            "recommendations": [
                {
                    **skill.summary(), "score": round(score, 3),
                    "reason": f"Matched {', '.join(sorted(set(fields)))}; triggers: {', '.join(skill.triggers[:3])}",
                }
                for skill, score, fields in matches
            ],
        }

    @mcp.tool
    def get_skill(name: str) -> dict[str, Any]:
        """Use to read one skill's workflow, output shape, guardrails, and supporting files."""
        active = current_catalog()
        try:
            skill = active.get(name)
        except KeyError as error:
            return {"found": False, "error": str(error)}
        return {"found": True, **_skill_result(skill)}

    @mcp.tool
    def get_skill_file(name: str, file_path: str) -> dict[str, Any]:
        """Use to read an allowed reference/template/script attached to a skill."""
        skill = current_catalog().get(name)
        path = resolve_skill_file(skill, file_path)
        content = path.read_text(encoding="utf-8")
        if len(content.encode("utf-8")) > 1_000_000:
            raise ValueError("Supporting file exceeds the 1 MB read limit")
        return {"skill": name, "path": file_path, "content": content}

    @mcp.tool
    def get_related_skills(name: str, limit: int = 10) -> dict[str, Any]:
        """Use to find lifecycle hand-offs, same-pack siblings, and similar skills."""
        if not 1 <= limit <= 30:
            raise ValueError("limit must be between 1 and 30")
        active = current_catalog()
        selected = active.get(name)
        related: dict[str, tuple[Skill, str, int]] = {}
        for skill in active.skills:
            if skill.name == name:
                continue
            relation = ""
            score = 0
            if skill.kind == selected.kind and skill.category == selected.category:
                relation, score = "same phase or pack", 4
            if skill.kind == "stlc" and selected.kind == "stlc":
                left = STLC_ORDER.index(selected.category) if selected.category in STLC_ORDER else -1
                right = STLC_ORDER.index(skill.category) if skill.category in STLC_ORDER else -1
                if abs(left - right) == 1:
                    relation, score = "adjacent STLC hand-off", 5
            if relation:
                related[skill.name] = (skill, relation, score)
        for skill, score, _ in search(active, selected.name + " " + selected.description, limit=30):
            if skill.name != name:
                existing = related.get(skill.name)
                if existing is None:
                    related[skill.name] = (skill, "similar keywords", round(score))
        results = sorted(related.values(), key=lambda item: (-item[2], item[0].name))[:limit]
        return {
            "skill": name,
            "related": [{"skill": item[0].summary(), "relationship": item[1], "score": item[2]} for item in results],
        }

    @mcp.tool
    def compare_skills(names: list[str]) -> dict[str, Any]:
        """Use to compare 2–5 candidate skills before selecting one."""
        if not 2 <= len(names) <= 5:
            raise ValueError("provide between 2 and 5 skill names")
        active = current_catalog()
        return {
            "skills": [
                {
                    **skill.summary(),
                    "when_to_use": _section(skill.content, "When to use"),
                    "workflow": _section(skill.content, "Workflow"),
                    "output_shape": _section(skill.content, "Output shape"),
                    "guardrails": _section(skill.content, "Guardrails"),
                }
                for skill in (active.get(name) for name in names)
            ],
        }

    @mcp.tool
    def suggest_skill_chain(goal: str, limit: int = 8) -> dict[str, Any]:
        """Use to build an ordered multi-skill workflow for a broad QA goal."""
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        active = current_catalog()
        matches = best_for_task(active, goal, limit)
        stlc_index = {phase: index for index, phase in enumerate(STLC_ORDER)}
        matches.sort(key=lambda item: (
            0 if item[0].kind == "stlc" else 1,
            stlc_index.get(item[0].category, 99), -item[1], item[0].name,
        ))
        return {
            "goal": goal,
            "chain": [
                {"step": index, "skill": skill.summary(), "score": round(score, 3)}
                for index, (skill, score, _) in enumerate(matches, 1)
            ],
            "note": "Review each skill's human-review gates before handing its output to the next step.",
        }

    @mcp.tool
    def get_stlc_pipeline() -> dict[str, Any]:
        """Use to inspect the seven lifecycle stages and skills in each stage."""
        return _stlc_pipeline(current_catalog())

    @mcp.tool
    def export_skill(
        name: str,
        format: Literal["claude_skill", "copilot_prompt", "cursor_rule", "markdown"] = "markdown",
    ) -> dict[str, Any]:
        """Use to export one skill as a compatible agent customization document."""
        skill = current_catalog().get(name)
        if format == "claude_skill":
            content = skill.content
            filename = "SKILL.md"
        elif format == "copilot_prompt":
            frontmatter = re.match(r"\A---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|\Z)", skill.content, re.DOTALL)
            body = skill.content[frontmatter.end():] if frontmatter else skill.content
            content = f"---\nmode: agent\n---\n\n{body}"
            filename = f"{skill.name}.prompt.md"
        elif format == "cursor_rule":
            frontmatter = re.match(r"\A---\s*\r?\n.*?\r?\n---\s*(?:\r?\n|\Z)", skill.content, re.DOTALL)
            body = skill.content[frontmatter.end():] if frontmatter else skill.content
            rule_metadata = yaml.safe_dump(
                {"description": skill.description, "globs": "**/*", "alwaysApply": False},
                sort_keys=False, allow_unicode=True,
            ).strip()
            content = f"---\n{rule_metadata}\n---\n\n{body}"
            filename = f"{skill.name}.mdc"
        else:
            content = skill.content
            filename = f"{skill.name}.md"
        return {"skill": name, "format": format, "filename": filename, "content": content}

    @mcp.tool
    def validate_skills(name: str | None = None) -> dict[str, Any]:
        """Use to validate one skill or the entire catalog against the house format."""
        active = current_catalog()
        selected = [active.get(name)] if name else list(active.skills)
        results = []
        for skill in selected:
            errors = _validate_skill_text(
                skill.name, skill.description, skill.category, skill.kind, skill.content
            )
            folder_name = skill.path.parent.name
            if folder_name != skill.name:
                errors.append(f"folder name {folder_name!r} does not match skill name")
            results.append({"name": skill.name, "valid": not errors, "errors": errors})
        return {
            "total": len(results), "valid": sum(item["valid"] for item in results),
            "invalid": sum(not item["valid"] for item in results), "results": results,
        }

    if allow_mutations:
        @mcp.tool
        def create_skill(
            name: str,
            description: str,
            category: str,
            kind: Literal["stlc", "framework"],
            workflow: str,
            output_shape: str,
            guardrails: str,
            dry_run: bool = True,
        ) -> dict[str, Any]:
            """Create a new local skill; defaults to preview-only and writes only after explicit approval."""
            active = current_catalog()
            if name in active.by_name:
                raise ValueError(f"Skill already exists: {name}")
            if kind == "stlc" and category not in STLC_ORDER:
                raise ValueError(f"category must be one of: {STLC_ORDER}")
            if not SLUG.fullmatch(name):
                raise ValueError("name must be a lowercase hyphenated slug")
            key = "stlc-phase" if kind == "stlc" else "pack"
            frontmatter = yaml.safe_dump(
                {
                    "name": name, "description": description, "license": "MIT",
                    "metadata": {"author": "local", key: category, "version": "1.0.0"},
                },
                sort_keys=False, allow_unicode=True,
            ).strip()
            content = (
                f"---\n{frontmatter}\n---\n\n"
                f"# {name.replace('-', ' ').title()}\n\n## When to use\n\n- {description}\n\n"
                f"## Workflow\n\n{workflow}\n\n## Output shape\n\n{output_shape}\n\n"
                f"## Guardrails\n\n{guardrails}\n"
            )
            errors = _validate_skill_text(name, description, category, kind, content)
            if errors:
                return {"created": False, "valid": False, "errors": errors}
            folder = (
                root / f"{STLC_ORDER.index(category) + 1:02d}-{_slug(category)}" / name
                if kind == "stlc"
                else root / "framework-packs" / f"{_slug(category)}-pack" / name
            )
            if dry_run:
                return {"created": False, "dry_run": True, "valid": True, "path": str(folder / "SKILL.md"), "content": content}
            folder.mkdir(parents=True, exist_ok=False)
            (folder / "SKILL.md").write_text(content, encoding="utf-8")
            return {"created": True, "path": str(folder / "SKILL.md")}

        @mcp.tool
        def sync_skills_from_github(ref: str = "main", dry_run: bool = True) -> dict[str, Any]:
            """Sync manifest-listed upstream files; local-authored skills are never overwritten."""
            active = current_catalog()
            manifest_path = root / ".upstream.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
            files = manifest.get("files", [])
            if not files:
                raise ValueError("No upstream file manifest exists; refusing an unbounded sync")
            token = os.environ.get("GITHUB_TOKEN")
            headers = {"Accept": "application/vnd.github+json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            plan = []
            with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
                for relative in files:
                    source_path = PurePosixPath(relative)
                    if source_path.is_absolute() or ".." in source_path.parts:
                        raise ValueError(f"Unsafe path in upstream manifest: {relative}")
                    target = (root / Path(*source_path.parts)).resolve()
                    if not target.is_relative_to(root):
                        raise ValueError(f"Upstream path escapes skills root: {relative}")
                    url_path = "/".join(quote(part, safe="-._") for part in source_path.parts)
                    url = (
                        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
                        f"{UPSTREAM_PATH}/{url_path}"
                    )
                    response = client.get(url, params={"ref": ref})
                    response.raise_for_status()
                    payload = response.json()
                    if payload.get("type") != "file":
                        continue
                    encoded = payload.get("content", "")
                    if payload.get("encoding") != "base64" or not encoded:
                        raise ValueError(f"GitHub did not return file content for {relative}")
                    content = base64.b64decode(encoded).decode("utf-8")
                    if len(content.encode("utf-8")) > 1_000_000:
                        raise ValueError(f"Upstream file exceeds 1 MB: {relative}")
                    plan.append((relative, target, content))
            if dry_run:
                return {"synced": False, "dry_run": True, "files": len(plan), "paths": [item[0] for item in plan]}
            for relative, target, content in plan:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            manifest.update({
                "repo": f"{REPO_OWNER}/{REPO_NAME}", "ref": ref,
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "files": [item[0] for item in plan],
            })
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            current_catalog()
            return {"synced": True, "files": len(plan), "commit": manifest.get("commit")}

    @mcp.resource("skills://catalog")
    def catalog_resource() -> str:
        """Machine-readable JSON catalog of skills and metadata."""
        active = current_catalog()
        return json.dumps(
            {"total": len(active.skills), "categories": active.categories,
             "skills": [skill.summary() for skill in active.skills]},
            ensure_ascii=False, indent=2,
        )

    @mcp.resource("skills://catalog.md")
    def catalog_markdown_resource() -> str:
        """Human-readable skill catalog grouped by lifecycle phase and pack."""
        return _catalog_markdown(current_catalog())

    @mcp.resource("skills://categories")
    def categories_resource() -> str:
        """Category and framework-pack counts."""
        active = current_catalog()
        return json.dumps({key: len(value) for key, value in active.categories.items()}, indent=2)

    @mcp.resource("skills://stlc-pipeline")
    def pipeline_resource() -> str:
        """Seven-stage software test lifecycle with contained skills."""
        return json.dumps(_stlc_pipeline(current_catalog()), indent=2)

    @mcp.resource("skills://stats")
    def stats_resource() -> str:
        """Totals by kind, category, and provenance."""
        active = current_catalog()
        return json.dumps({
            "total": len(active.skills),
            "by_kind": {kind: sum(skill.kind == kind for skill in active.skills) for kind in ("stlc", "framework")},
            "by_source": _source_counts(active),
            "by_category": {category: len(names) for category, names in active.categories.items()},
        }, indent=2)

    @mcp.resource("skill://{name}")
    def skill_resource(name: str) -> str:
        """Complete local SKILL.md file addressed by skill name."""
        return current_catalog().get(name).content

    @mcp.resource("skill://{name}/files/{file_path}")
    def skill_file_resource(name: str, file_path: str) -> str:
        """Supporting file inside a skill folder; traversal outside that folder is blocked."""
        skill = current_catalog().get(name)
        return resolve_skill_file(skill, file_path).read_text(encoding="utf-8")

    @mcp.prompt
    def use_skill(name: str, task: str) -> str:
        """Load a skill's instructions and apply them to a QA task."""
        skill = current_catalog().get(name)
        return f"Follow the skill below to complete the task. Preserve its guardrails and review gates.\n\nTask:\n{task}\n\n{skill.content}"

    @mcp.prompt
    def find_skill(query: str) -> str:
        """Guide skill discovery from the user's natural-language request."""
        return f"Find the best matching QA skill for: {query}\nCall search_skills, compare the top candidates, then call get_skill for the selected skill."

    @mcp.prompt
    def plan_with_skills(goal: str) -> str:
        """Plan an ordered chain of lifecycle skills for a broader QA goal."""
        return f"Plan the skill workflow for: {goal}\nCall suggest_skill_chain and explain hand-offs and required human-review gates."

    def make_skill_prompt(skill_name: str):
        def skill_prompt(task: str = "") -> str:
            selected = current_catalog().get(skill_name)
            return (
                f"Apply this skill to the task. Respect all instructions and guardrails.\n\n"
                f"Task:\n{task}\n\n{selected.content}"
            )
        skill_prompt.__name__ = f"use_{skill_name.replace('-', '_')}"
        skill_prompt.__doc__ = f"Use the {skill_name} skill with the supplied task."
        return skill_prompt

    for skill in catalog.skills:
        mcp.prompt(name=skill.name)(make_skill_prompt(skill.name))

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="TestSkill Finder MCP")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default=os.getenv("TSF_TRANSPORT", "stdio"))
    parser.add_argument("--host", default=os.getenv("TSF_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("TSF_PORT", "8110")))
    parser.add_argument("--skills-dir", type=Path)
    parser.add_argument("--allow-write", action="store_true")
    args = parser.parse_args()
    mcp = create_server(args.skills_dir, args.allow_write or None)
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
