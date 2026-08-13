# GEO Method

## 1. Definition and boundary

GEO here means producing public web content that is easy for retrieval systems and generative engines to parse and cite. It is not a direct publishing channel to an AI platform. Do not claim that this workflow guarantees inclusion in an AI answer.

## 2. Evidence model

Use two separate evidence classes:

| Class | Supports | Does not support |
|---|---|---|
| Product fact | Specifications, compatibility, warranty, feature limitations | Market size, consumer preference, competitor performance |
| Market evidence | Events, regulations, trends, audience needs, third-party findings | Undocumented product capabilities |

Prefer original sources in this order: government/standards bodies and official manuals; first-party product pages and named research; reputable reporting or independent testing; user-generated content. UGC describes an individual's experience and must not be generalized without broader evidence.

An eligible citation must have a stable ID, identifiable publisher, direct URL or internal record ID, evidence excerpt, market scope, and confirmation status. Apply its `validity_rule`. When regional sources conflict, retain the regional distinction instead of averaging or selecting the larger value.

Never fabricate a named expert quote. Paraphrase a sourced position when quotation text cannot be verified.

## 3. Claim ledger

Create a ledger before finalizing copy. Register claims that a reasonable reader could verify externally, including numbers, dates, comparisons, certifications, superlatives, safety statements, availability, and performance outcomes.

Each claim needs:

- `claim_id`: unique within the package.
- `text`: the exact or faithful normalized claim.
- `position`: heading, paragraph anchor, or FAQ number.
- `evidence_ids`: supporting market evidence.
- `product_fact_ids`: supporting product facts.

Pure transitions and subjective framing need no claim entry. A source ID in a footer is insufficient unless the relevant claim maps to it.

## 4. Content structure

Use Answer-Expand-Substantiate:

1. Answer the target question in the first one or two sentences, with necessary qualification.
2. Explain selection criteria, use context, or reasoning under query-aligned H2/H3 headings.
3. Substantiate with scoped facts, comparisons, examples, and citations.

Favor short self-contained passages. Use tables only for genuine comparisons with equivalent definitions and markets. Avoid keyword repetition, empty superlatives, fake precision, and generic introductions.

FAQ questions should reflect real follow-up intent, not restate keywords. Keep answers concise and consistent with the main copy.

## 5. Schema rules

- `Article`: use for guides and editorial answers. Supply headline, date, author/publisher only when known.
- `Product`: use for a specific product. Supply identifiers, brand, description, offers, ratings, or reviews only when present and verifiable.
- `FAQPage`: include only visible questions with visible answers. Do not mark up promotional statements as FAQs.
- Do not use `HowTo` unless the page contains a real ordered procedure that users can complete.
- JSON-LD must not introduce claims absent from visible content.

Schema markup improves machine readability but does not guarantee rich results or AI citations.

## 6. Market and compliance checks

Localize units, voltage, plugs, warranty, certification, availability, price, terminology, and disclosure rules. Do not carry a US product value into EU, Japan, or China content unless the source explicitly covers that market.

Use comparison language only when the compared products, measurement conditions, time period, and source are explicit. Avoid "best", "leading", and similar claims unless a scoped source and methodology support them.

## 7. Quality gate

Block publication for:

- Missing support for a registered factual claim.
- Unconfirmed or disallowed evidence referenced by copy.
- Market mismatch or ignored source limitation.
- Fabricated quotation, statistic, certification, rating, price, or product property.
- FAQ JSON-LD that differs from visible FAQ content.
- Product JSON-LD containing unsupported offers, ratings, or reviews.

Warn, but do not necessarily block, for stale retrieval dates, weak title/query alignment, absent optional schema, or a thin FAQ set.
