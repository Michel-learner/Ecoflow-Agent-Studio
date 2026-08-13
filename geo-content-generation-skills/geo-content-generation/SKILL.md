---
name: geo-content-generation
description: Generate source-grounded Generative Engine Optimization (GEO) content packages, including answer-first articles, FAQ assets, claim-to-evidence mappings, citations, and Schema.org JSON-LD. Use when creating or auditing AI-search-friendly product pages, buying guides, help-center answers, FAQs, or knowledge modules from product facts and market evidence, especially when outputs must be traceable and function-call validated.
---

# GEO Content Generation

Create publishable website content that search engines and generative systems can discover, understand, and quote. Optimize for answer quality and verifiability; never promise rankings, citations, traffic, or recommendation lift.

## Required inputs

Collect or request:

- Content brief: target question, audience, market, language, content type, and channel.
- Product facts: stable IDs, exact values, market scope, limitations, and source URLs or record IDs.
- Market evidence: stable IDs, excerpt, source, URL, tier, market, date, validity rule, and confirmation status.
- Optional brand voice, legal constraints, competitor facts, FAQ count, and length.

Do not invent missing product specifications, prices, certifications, statistics, testimonials, expert quotes, or competitor claims. Mark a gap and continue with a narrower supported answer.

## Workflow

1. Read [references/geo-method.md](references/geo-method.md) for content and evidence rules.
2. If the host supports function calling, read [references/function-calling.md](references/function-calling.md). Load tool definitions from `scripts/geo_tools.py --print-tools`.
3. Call `select_eligible_evidence` before drafting. Use only returned eligible records for market claims. Treat unconfirmed, wrong-market, expired, or low-tier records as research leads, not citations.
4. Plan one direct answer and a small set of independently extractable sections. Assign a stable ID to every externally verifiable claim.
5. Draft in Answer-Expand-Substantiate order. Keep every quantitative or comparative statement within the scope and limitations of its source.
6. Call `validate_claims` with the draft claim ledger, eligible evidence, and product facts. Revise or remove every unsupported claim.
7. Call `build_jsonld` to create `Article`, `Product`, and/or `FAQPage` markup from provided facts only. Include only FAQ questions and answers visible in the page copy.
8. Assemble the output contract below, then call `validate_geo_package`. Return `blocked` when any error remains; never disguise a blocked package as publishable.

## Output contract

Return one JSON object unless the user asks for another format:

```json
{
  "metadata": {
    "title": "",
    "target_question": "",
    "market": "",
    "language": "",
    "content_type": "",
    "generated_at": "ISO-8601"
  },
  "content_markdown": "",
  "faq": [{"question": "", "answer": ""}],
  "claims": [
    {
      "claim_id": "CLM-001",
      "text": "",
      "position": "section heading or anchor",
      "evidence_ids": [],
      "product_fact_ids": []
    }
  ],
  "citations": [
    {"ref_id": "", "title": "", "publisher": "", "url": "", "published_at": ""}
  ],
  "jsonld": [],
  "gaps": [],
  "validation": {"status": "pass|blocked", "errors": [], "warnings": []}
}
```

Keep market evidence IDs and product fact IDs separate. A product fact can support a specification but not an external market trend. A market source can support context but not an undocumented product capability.

## Publication rules

- Publish only when `validate_geo_package.status` is `pass`.
- Link citations to original sources where possible; do not cite search-result snippets as final evidence.
- Preserve material limitations and regional differences near the related claim.
- Label first-party product sources and user-generated anecdotes accurately.
- Treat Schema.org markup as machine-readable parity with visible content, not hidden keyword storage.
- Report incomplete evidence plainly. A useful partial answer is better than fabricated completeness.

## Resource routing

- Read [references/geo-method.md](references/geo-method.md) for detailed writing, source, and schema decisions.
- Read [references/function-calling.md](references/function-calling.md) when integrating an OpenAI-compatible tool loop or invoking tools from the CLI.
- Run `python scripts/geo_tools.py --self-test` after changing the function schemas or validation logic.
