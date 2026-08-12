from __future__ import annotations


def promotion_allows_artifact(decision: dict) -> bool:
    return decision.get("promote") is True
