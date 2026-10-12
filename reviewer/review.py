#!/usr/bin/env python3
"""Send reduced plan + app context + ADRs to an LLM; return a validated review."""
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get(
    "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
)
MODEL = os.environ["LLM_MODEL"]

SEVERITIES = {"critical", "high", "medium", "low", "info"}
VERDICTS = {"ok", "needs_attention", "high_risk"}
FINDING_KEYS = (
    "severity",
    "resource",
    "issue",
    "why_it_matters_for_this_app",
    "suggested_fix",
)

SYSTEM_PROMPT = """You review Terraform pull requests for ONE specific application.
You receive APP CONTEXT, ADRs (decisions already made) and a CHANGE SET (a reduced terraform plan).

Rules:
- Report only findings that matter for THIS app, using its sensitive data, which components are
  internet-facing vs internal-only, and its review priorities. Do not write a generic best-practice audit.
- Flag any change that contradicts an ADR and set adr_reference to that ADR's filename.
- Values shown as "<redacted>" are hidden secrets, not problems. Attributes that are absent are
  computed at apply time, not missing.
- Judge only what is in the change set. Never invent resources.
- Severity: critical = data exposure or leaked credentials; high = security or data-protection weakness;
  medium = least-privilege or cost problem; low = minor; info = notable but acceptable.
- If nothing matters, return an empty findings list and verdict "ok".

Return ONLY one JSON object, no prose, no markdown fences:
{"summary": str, "verdict": "ok"|"needs_attention"|"high_risk",
 "findings": [{"severity": str, "resource": "<terraform address>", "issue": str,
               "why_it_matters_for_this_app": str, "suggested_fix": str, "adr_reference": optional str}]}"""


def call_llm(messages):
    """The only provider-specific function. Returns the model's text reply."""
    body = json.dumps(
        {"model": MODEL, "messages": messages, "temperature": 0.1, "max_tokens": 8000}
    ).encode()  # room for thinking models
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['LLM_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.load(resp)["choices"][0]["message"]["content"]
    except (
        urllib.error.HTTPError
    ) as e:  # show the provider's message, not just the code
        raise RuntimeError(f"LLM HTTP {e.code}: {e.read().decode()[:300]}") from None


def parse(text):
    """Models sometimes wrap JSON in prose or fences, so take the outermost braces."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return json.loads(text[start : end + 1])


def validate(result):
    """Reject replies that don't match the schema the formatter will rely on."""
    if (
        not isinstance(result.get("summary"), str)
        or result.get("verdict") not in VERDICTS
    ):
        raise ValueError("bad summary or verdict")
    for f in result.get("findings", []):
        if any(k not in f for k in FINDING_KEYS) or f["severity"] not in SEVERITIES:
            raise ValueError(f"bad finding: {f}")


def review(app_context, adrs, change_set, attempts=2):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"APP CONTEXT:\n{app_context}\n\nADRs:\n{adrs}\n\nCHANGE SET:\n{change_set}",
        },
    ]
    last = None
    for _ in range(attempts):  # one retry if the model returns malformed JSON
        try:
            result = parse(call_llm(messages))
            validate(result)
            result.setdefault("findings", [])
            return result
        except ValueError as e:  # JSONDecodeError is a ValueError too
            last = e
    raise RuntimeError(f"model returned an invalid review: {last}")


if __name__ == "__main__":
    reduced_path, context_path, adr_dir = sys.argv[1:4]
    change_set = json.dumps(
        json.loads(Path(reduced_path).read_text()), separators=(",", ":")
    )  # compact JSON saves tokens
    adrs = (
        "\n\n".join(
            f"--- {p.name} ---\n{p.read_text()}"
            for p in sorted(Path(adr_dir).glob("*.md"))
        )
        or "(none)"
    )
    print(
        json.dumps(review(Path(context_path).read_text(), adrs, change_set), indent=2)
    )
