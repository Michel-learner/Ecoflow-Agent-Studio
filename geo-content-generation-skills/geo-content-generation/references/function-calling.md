# Function Calling Integration

The bundled handler uses only the Python standard library. It exposes deterministic tools for evidence and output checks; the language model remains responsible for drafting.

## Available functions

| Function | Purpose |
|---|---|
| `select_eligible_evidence` | Filter evidence by tier, confirmation, market, and expiry |
| `validate_claims` | Verify claim IDs and evidence/product-fact references |
| `build_jsonld` | Build conservative Article, Product, and FAQPage JSON-LD |
| `validate_geo_package` | Apply the final publication gate |

Inspect the exact JSON Schemas:

```powershell
python scripts/geo_tools.py --print-tools
```

Invoke one function locally:

```powershell
python scripts/geo_tools.py --call select_eligible_evidence --arguments-file input.json
```

The handler prints a JSON result and returns a nonzero exit code only for malformed calls, not for a valid `blocked` validation result.

## OpenAI-compatible loop

Use `TOOLS` as the model's tool definitions. Dispatch every returned call by name and send the JSON result back as the tool output. Continue until the model returns a final content package.

```python
import json
from openai import OpenAI
from scripts.geo_tools import TOOLS, dispatch

client = OpenAI()
response = client.responses.create(
    model="YOUR_TOOL_CAPABLE_MODEL",
    input="Create a GEO answer from the supplied brief and evidence.",
    tools=TOOLS,
)

while True:
    calls = [item for item in response.output if item.type == "function_call"]
    if not calls:
        break
    outputs = []
    for call in calls:
        result = dispatch(call.name, json.loads(call.arguments))
        outputs.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": json.dumps(result, ensure_ascii=False),
        })
    response = client.responses.create(
        model="YOUR_TOOL_CAPABLE_MODEL",
        previous_response_id=response.id,
        input=outputs,
        tools=TOOLS,
    )

print(response.output_text)
```

Adapt the SDK loop to the host version in use. The stable integration boundary is `dispatch(function_name, arguments)`.

## Recommended call order

```text
select_eligible_evidence
  -> model drafts claims and content
  -> validate_claims
  -> model revises unsupported claims
  -> build_jsonld
  -> validate_geo_package
  -> publish only on pass
```

Do not expose a general web-search function unless the host can capture the original URL, publisher, excerpt, retrieval date, and confirmation state. Search results should enter the same evidence gate before use.
