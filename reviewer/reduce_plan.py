#!/usr/bin/env python3
"""Reduce `terraform show -json` output to a compact, secret-free change set."""
import json
import sys

REDACTED = "<redacted>"
NOISE_KEYS = {"tags_all"}  # duplicates `tags`, adds no review value


def strip_sensitive(value, mask):
    """Replace anything Terraform flagged as sensitive.
    `mask` mirrors the shape of `value`: True = sensitive, dict/list = recurse."""
    if mask is True:
        return REDACTED
    if isinstance(value, dict) and isinstance(mask, dict):
        return {k: strip_sensitive(v, mask.get(k)) for k, v in value.items()}
    if isinstance(value, list) and isinstance(mask, list):
        return [
            strip_sensitive(v, mask[i] if i < len(mask) else None)
            for i, v in enumerate(value)
        ]
    return value


def compact(attrs):
    """Drop nulls, empty values and noise so only meaningful attributes remain."""
    if not attrs:
        return {}
    return {
        k: v
        for k, v in attrs.items()
        if k not in NOISE_KEYS and v not in (None, "", [], {})
    }


def diff(before, after):
    """For updates, keep only attributes whose value changed."""
    before, after = before or {}, after or {}
    return {
        k: {"before": before.get(k), "after": after.get(k)}
        for k in set(before) | set(after)
        if k not in NOISE_KEYS and before.get(k) != after.get(k)
    }


def reduce_plan(plan):
    changes = []
    for rc in plan.get("resource_changes", []):
        ch = rc["change"]
        actions = ch["actions"]
        if actions == ["no-op"]:  # nothing changed, nothing to review
            continue
        # Strip secrets FIRST, before anything else touches the values
        before = strip_sensitive(ch.get("before"), ch.get("before_sensitive"))
        after = strip_sensitive(ch.get("after"), ch.get("after_sensitive"))
        if actions == ["create"]:
            attrs = compact(after)
        elif actions == ["delete"]:
            attrs = compact(before)
        else: 
            attrs = diff(before, after)
        changes.append(
            {
                "resource": rc["address"],
                "type": rc["type"],
                "action": "+".join(actions),
                "attributes": attrs,
            }
        )
    summary = {}
    for c in changes:
        summary[c["action"]] = summary.get(c["action"], 0) + 1
    return {"summary": summary, "changes": changes}


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        print(json.dumps(reduce_plan(json.load(f)), indent=2))
