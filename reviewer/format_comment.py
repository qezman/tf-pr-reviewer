#!/usr/bin/env python3
"""Render the review JSON as a markdown PR comment."""
import json
import sys

MARKER = "<!-- tf-review -->"  # lets the poster find its earlier comment
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
VERDICT_TEXT = {
    "ok": "no issues found",
    "needs_attention": "needs attention",
    "high_risk": "high risk",
}


def render(review):
    findings = sorted(
        review.get("findings", []), key=lambda f: SEVERITY_ORDER.index(f["severity"])
    )
    out = [
        MARKER,
        f"## Terraform review: {VERDICT_TEXT[review['verdict']]}",
        "",
        review["summary"],
        "",
    ]
    for f in findings:
        out += [
            f"**[{f['severity']}]** `{f['resource']}`",
            "",
            f"- Issue: {f['issue']}",
            f"- Why it matters here: {f['why_it_matters_for_this_app']}",
            f"- Fix: {f['suggested_fix']}",
        ]
        if f.get("adr_reference"):
            out.append(f"- Conflicts with: `{f['adr_reference']}`")
        out.append("")
    out.append("_Automated review (LLM). Advisory only, it never blocks a merge._")
    return "\n".join(out)


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        print(render(json.load(fh)))
