"""Deterministic, weighted keyword search for QA skills."""

from __future__ import annotations

import math
import re
from collections import Counter

from tsf_mcp.catalog import Skill, SkillCatalog

TOKEN = re.compile(r"[a-z0-9]+")
SYNONYMS = {
    "pw": {"playwright"}, "bug": {"defect", "issue"}, "bugs": {"bug", "defect", "issue"},
    "defects": {"defect", "bug"}, "creator": {"create", "writer", "generator", "generate"},
    "create": {"creator", "writer", "generator", "generate"},
    "writer": {"write", "create", "creator", "generator"},
    "generator": {"generate", "create", "creator", "writer"},
    "plan": {"planning", "planner"}, "planner": {"plan", "planning"},
    "strategy": {"strategist", "triage"}, "cases": {"case"},
    "testcase": {"test", "case"}, "testcases": {"test", "case"},
    "api": {"endpoint", "request", "contract"},
    "locator": {"selector"}, "selector": {"locator"},
    "k6": {"performance", "load"}, "deepeval": {"llm", "evaluation"},
}


def tokenize(text: str) -> list[str]:
    tokens = TOKEN.findall(text.casefold())
    normalized = []
    for token in tokens:
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("ing") and len(token) > 6:
            token = token[:-3]
        elif token.endswith("er") and len(token) > 5:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
            token = token[:-1]
        normalized.append(token)
    return normalized


def _expanded(word: str) -> set[str]:
    return {
        normalized
        for candidate in {word, *SYNONYMS.get(word, set())}
        for normalized in tokenize(candidate)
    }


def _corpus_text(skill: Skill) -> dict[str, str]:
    body = skill.content
    sections = {}
    for title, weight_field in [
        ("When to use", "when"), ("Workflow", "workflow"),
        ("Output shape", "output"), ("Guardrails", "guardrails"),
    ]:
        start = body.casefold().find(f"## {title}".casefold())
        if start < 0:
            sections[weight_field] = ""
            continue
        end = body.find("\n## ", start + 4)
        sections[weight_field] = body[start : end if end >= 0 else len(body)]
    return {
        "name": skill.name.replace("-", " "),
        "title": body.splitlines()[2].lstrip("# ").strip() if len(body.splitlines()) > 2 else "",
        "triggers": " ".join(skill.triggers),
        "category": skill.category + " " + str(skill.metadata.get("pack", "")),
        "description": skill.description,
        **sections,
        "body": body,
    }


def search(catalog: SkillCatalog, query: str, limit: int = 10) -> list[tuple[Skill, float, list[str]]]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    terms = tokenize(query)
    if not terms:
        raise ValueError("query must include searchable words")
    fields = {skill.name: _corpus_text(skill) for skill in catalog.skills}
    weights = {
        "name": 6.0, "title": 4.0, "triggers": 3.0, "category": 3.0,
        "description": 2.0, "when": 1.5, "workflow": 0.8, "output": 0.8,
        "guardrails": 0.6, "body": 0.5,
    }
    document_frequency = Counter()
    tokenized = {}
    for name, skill_fields in fields.items():
        tokens = {field: tokenize(text) for field, text in skill_fields.items()}
        tokenized[name] = tokens
        all_tokens = set(token for values in tokens.values() for token in values)
        document_frequency.update(all_tokens)
    total = max(1, len(catalog.skills))
    ranked = []
    for skill in catalog.skills:
        by_field = tokenized[skill.name]
        score = 0.0
        matched = []
        for term in terms:
            alternatives = _expanded(term)
            term_score = 0.0
            matched_field = ""
            idf = math.log(1 + total / (1 + max(document_frequency.get(item, 0) for item in alternatives)))
            for field, weight in weights.items():
                field_words = set(by_field[field])
                direct = term in field_words
                synonym = (alternatives - {term}).intersection(field_words)
                if direct or synonym:
                    candidate = weight * idf * (1.0 if direct else 0.6)
                    if candidate > term_score:
                        term_score, matched_field = candidate, field
            if term_score:
                score += term_score
                matched.append(matched_field)
        coverage = len(matched) / len(terms)
        if score and coverage:
            score *= coverage
            name_words = set(tokenize(skill.name.replace("-", " ")))
            if all(term in name_words for term in terms):
                score += 8.0
            elif all(_expanded(term).intersection(name_words) for term in terms):
                score += 3.0
            trigger_text = " ".join(skill.triggers).casefold()
            if query.casefold() in trigger_text:
                score += 5.0
            ranked.append((skill, score, matched))
    return sorted(ranked, key=lambda item: (-item[1], item[0].name))[:limit]


def best_for_task(catalog: SkillCatalog, task: str, limit: int = 5) -> list[tuple[Skill, float, list[str]]]:
    return search(catalog, task, limit)
