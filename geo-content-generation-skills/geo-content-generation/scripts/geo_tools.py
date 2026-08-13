#!/usr/bin/env python3
"""Function-callable validation tools for source-grounded GEO content."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Any, Callable


MARKETS_GLOBAL = {"global", "all", "worldwide", "*"}
CONFIRMED_VALUES = {"confirmed", "approved", "verified", "已确认", "通过"}


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


RECORD_ARRAY = {"type": "array", "items": {"type": "object"}}

TOOLS = [
    {
        "type": "function",
        "name": "select_eligible_evidence",
        "description": "Filter evidence records by source tier, confirmation state, market scope, and expiry before drafting GEO content.",
        "parameters": _schema(
            {
                "evidence": RECORD_ARRAY,
                "target_market": {"type": "string"},
                "allowed_tiers": {"type": "array", "items": {"type": "string"}, "default": ["T1", "T2"]},
                "require_confirmed": {"type": "boolean", "default": True},
                "as_of": {"type": "string", "description": "ISO date used for expires_at checks."},
            },
            ["evidence", "target_market"],
        ),
    },
    {
        "type": "function",
        "name": "validate_claims",
        "description": "Validate claim IDs and claim-to-evidence/product-fact mappings without judging prose style.",
        "parameters": _schema(
            {
                "claims": RECORD_ARRAY,
                "eligible_evidence": RECORD_ARRAY,
                "product_facts": RECORD_ARRAY,
            },
            ["claims", "eligible_evidence", "product_facts"],
        ),
    },
    {
        "type": "function",
        "name": "build_jsonld",
        "description": "Build conservative Schema.org JSON-LD from supplied visible article, product, and FAQ fields without inferring missing values.",
        "parameters": _schema(
            {
                "article": {"type": "object"},
                "product": {"type": "object"},
                "faq": {"type": "array", "items": {"type": "object"}},
            },
            [],
        ),
    },
    {
        "type": "function",
        "name": "validate_geo_package",
        "description": "Apply the final GEO publication gate to content, claims, sources, FAQ, and JSON-LD.",
        "parameters": _schema(
            {
                "package": {"type": "object"},
                "eligible_evidence": RECORD_ARRAY,
                "product_facts": RECORD_ARRAY,
            },
            ["package", "eligible_evidence", "product_facts"],
        ),
    },
]


def _id(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _market_matches(record_market: Any, target_market: str) -> bool:
    if not record_market:
        return False
    target = target_market.strip().casefold()
    values = record_market if isinstance(record_market, list) else [record_market]
    normalized = " | ".join(str(value) for value in values).casefold()
    return target in normalized or any(token in normalized for token in MARKETS_GLOBAL)


def _confirmed(record: dict[str, Any]) -> bool:
    value = record.get("confirmed_status", record.get("status", ""))
    return str(value).strip().casefold() in {v.casefold() for v in CONFIRMED_VALUES}


def select_eligible_evidence(
    evidence: list[dict[str, Any]],
    target_market: str,
    allowed_tiers: list[str] | None = None,
    require_confirmed: bool = True,
    as_of: str | None = None,
) -> dict[str, Any]:
    allowed = {tier.upper() for tier in (allowed_tiers or ["T1", "T2"])}
    today = dt.date.fromisoformat(as_of) if as_of else dt.date.today()
    eligible, rejected = [], []

    for record in evidence:
        record_id = _id(record, "evidence_id", "fact_id", "id") or "<missing-id>"
        reasons: list[str] = []
        if str(record.get("source_tier", "")).upper() not in allowed:
            reasons.append("tier_not_allowed")
        if require_confirmed and not _confirmed(record):
            reasons.append("not_confirmed")
        if not _market_matches(record.get("market"), target_market):
            reasons.append("market_mismatch")
        expires_at = record.get("expires_at")
        if expires_at:
            try:
                if dt.date.fromisoformat(str(expires_at)[:10]) < today:
                    reasons.append("expired")
            except ValueError:
                reasons.append("invalid_expiry")
        if not record.get("source_ref") and not record.get("url"):
            reasons.append("missing_source_ref")
        if not record.get("evidence_excerpt") and not record.get("summary"):
            reasons.append("missing_excerpt")

        if reasons:
            rejected.append({"record_id": record_id, "reasons": reasons})
        else:
            eligible.append(record)

    return {
        "eligible": eligible,
        "rejected": rejected,
        "summary": {"eligible_count": len(eligible), "rejected_count": len(rejected)},
    }


def validate_claims(
    claims: list[dict[str, Any]],
    eligible_evidence: list[dict[str, Any]],
    product_facts: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_ids = {_id(item, "evidence_id", "id") for item in eligible_evidence}
    fact_ids = {_id(item, "fact_id", "product_fact_id", "id") for item in product_facts}
    evidence_ids.discard("")
    fact_ids.discard("")
    seen: set[str] = set()
    results, errors = [], []

    for index, claim in enumerate(claims):
        claim_id = _id(claim, "claim_id")
        claim_errors: list[str] = []
        if not claim_id:
            claim_errors.append("missing_claim_id")
        elif claim_id in seen:
            claim_errors.append("duplicate_claim_id")
        seen.add(claim_id)
        if not str(claim.get("text", "")).strip():
            claim_errors.append("missing_claim_text")
        refs = [str(value) for value in claim.get("evidence_ids", [])]
        facts = [str(value) for value in claim.get("product_fact_ids", [])]
        for ref in refs:
            if ref not in evidence_ids:
                claim_errors.append(f"invalid_evidence_ref:{ref}")
        for ref in facts:
            if ref not in fact_ids:
                claim_errors.append(f"invalid_product_fact_ref:{ref}")
        if not refs and not facts:
            claim_errors.append("unsupported_claim")
        status = "pass" if not claim_errors else "blocked"
        results.append({"index": index, "claim_id": claim_id, "status": status, "errors": claim_errors})
        errors.extend({"claim_id": claim_id or None, "issue": issue} for issue in claim_errors)

    return {"status": "pass" if not errors else "blocked", "claims": results, "errors": errors}


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items() if item not in (None, "", [], {})}
    if isinstance(value, list):
        return [_clean(item) for item in value if item not in (None, "", [], {})]
    return value


def build_jsonld(
    article: dict[str, Any] | None = None,
    product: dict[str, Any] | None = None,
    faq: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    graph: list[dict[str, Any]] = []
    article = article or {}
    product = product or {}
    faq = faq or []

    if article:
        node = {"@type": "Article"}
        for source, target in (("headline", "headline"), ("description", "description"), ("datePublished", "datePublished"), ("dateModified", "dateModified"), ("url", "mainEntityOfPage")):
            if article.get(source):
                node[target] = article[source]
        if article.get("author"):
            node["author"] = {"@type": "Person", "name": article["author"]}
        if article.get("publisher"):
            node["publisher"] = {"@type": "Organization", "name": article["publisher"]}
        graph.append(node)

    if product:
        node = {"@type": "Product"}
        allowed = ("name", "description", "sku", "mpn", "image", "url")
        node.update({key: product[key] for key in allowed if product.get(key)})
        if product.get("brand"):
            node["brand"] = {"@type": "Brand", "name": product["brand"]}
        if product.get("offers"):
            offers = dict(product["offers"])
            offers["@type"] = "Offer"
            node["offers"] = offers
        graph.append(node)

    questions = []
    for item in faq:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if question and answer:
            questions.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            })
    if questions:
        graph.append({"@type": "FAQPage", "mainEntity": questions})

    return {"jsonld": _clean({"@context": "https://schema.org", "@graph": graph}), "node_count": len(graph)}


def validate_geo_package(
    package: dict[str, Any],
    eligible_evidence: list[dict[str, Any]],
    product_facts: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    required = ("metadata", "content_markdown", "claims", "citations", "jsonld", "gaps")
    for field in required:
        if field not in package:
            errors.append({"code": "missing_field", "field": field})
    content = str(package.get("content_markdown", "")).strip()
    if not content:
        errors.append({"code": "empty_content", "field": "content_markdown"})

    claim_result = validate_claims(package.get("claims", []), eligible_evidence, product_facts)
    errors.extend({"code": "claim_validation", **item} for item in claim_result["errors"])

    citation_ids = {_id(item, "ref_id", "evidence_id", "fact_id", "id") for item in package.get("citations", [])}
    used_ids = {
        str(ref)
        for claim in package.get("claims", [])
        for ref in claim.get("evidence_ids", []) + claim.get("product_fact_ids", [])
    }
    for ref in sorted(used_ids - citation_ids):
        errors.append({"code": "missing_citation_entry", "ref_id": ref})

    faq = package.get("faq", [])
    jsonld = package.get("jsonld", [])
    nodes = jsonld.get("@graph", []) if isinstance(jsonld, dict) else jsonld
    faq_nodes = [node for node in nodes if isinstance(node, dict) and node.get("@type") == "FAQPage"]
    if faq:
        if not faq_nodes:
            warnings.append({"code": "faq_schema_missing"})
        else:
            visible = {(str(item.get("question", "")).strip(), str(item.get("answer", "")).strip()) for item in faq}
            marked = {
                (str(item.get("name", "")).strip(), str(item.get("acceptedAnswer", {}).get("text", "")).strip())
                for node in faq_nodes for item in node.get("mainEntity", [])
            }
            if visible != marked:
                errors.append({"code": "faq_schema_mismatch"})
    if not faq:
        warnings.append({"code": "faq_missing"})
    if not nodes:
        warnings.append({"code": "jsonld_empty"})

    return {
        "status": "pass" if not errors else "blocked",
        "errors": errors,
        "warnings": warnings,
        "summary": {"error_count": len(errors), "warning_count": len(warnings), "claim_count": len(package.get("claims", []))},
    }


FUNCTIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "select_eligible_evidence": select_eligible_evidence,
    "validate_claims": validate_claims,
    "build_jsonld": build_jsonld,
    "validate_geo_package": validate_geo_package,
}


def dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name not in FUNCTIONS:
        raise ValueError(f"Unknown function: {name}")
    if not isinstance(arguments, dict):
        raise TypeError("Function arguments must be a JSON object")
    return FUNCTIONS[name](**arguments)


def _self_test() -> dict[str, Any]:
    evidence = [{
        "evidence_id": "EV-001", "source_tier": "T1", "confirmed_status": "confirmed",
        "market": "US", "source_ref": "https://example.com/report", "evidence_excerpt": "Supported context.",
    }]
    facts = [{"fact_id": "PF-001", "market": "US", "source_ref": "https://example.com/product"}]
    selected = select_eligible_evidence(evidence, "US")
    assert len(selected["eligible"]) == 1
    claims = [{"claim_id": "CLM-001", "text": "Supported fact", "evidence_ids": ["EV-001"], "product_fact_ids": []}]
    assert validate_claims(claims, evidence, facts)["status"] == "pass"
    faq = [{"question": "What is it?", "answer": "A supported product."}]
    jsonld = build_jsonld(product={"name": "Example", "brand": "Brand"}, faq=faq)["jsonld"]
    package = {
        "metadata": {"market": "US"}, "content_markdown": "A supported answer.", "faq": faq,
        "claims": claims, "citations": [{"ref_id": "EV-001", "url": "https://example.com/report"}],
        "jsonld": jsonld, "gaps": [],
    }
    result = validate_geo_package(package, evidence, facts)
    assert result["status"] == "pass", result
    skill_file = __file__.replace("scripts\\geo_tools.py", "SKILL.md").replace("scripts/geo_tools.py", "SKILL.md")
    with open(skill_file, "r", encoding="utf-8") as handle:
        frontmatter = handle.read().split("---", 2)[1]
    assert "name: geo-content-generation" in frontmatter
    assert "description:" in frontmatter
    return {"status": "pass", "tests": 5}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-tools", action="store_true")
    parser.add_argument("--call", choices=sorted(FUNCTIONS))
    parser.add_argument("--arguments", help="Inline JSON object")
    parser.add_argument("--arguments-file", help="Path to a JSON arguments file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.print_tools:
            output = TOOLS
        elif args.self_test:
            output = _self_test()
        elif args.call:
            if args.arguments_file:
                with open(args.arguments_file, "r", encoding="utf-8-sig") as handle:
                    arguments = json.load(handle)
            elif args.arguments:
                arguments = json.loads(args.arguments)
            else:
                arguments = json.load(sys.stdin)
            output = dispatch(args.call, arguments)
        else:
            parser.error("choose --print-tools, --self-test, or --call")
            return 2
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
