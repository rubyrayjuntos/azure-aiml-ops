from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from lifecycle_policy import promotion_allows_artifact


def should_package(decision: dict) -> bool:
    return promotion_allows_artifact(decision)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-input", required=True)
    parser.add_argument("--decision-input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    decision = json.loads(
        (Path(args.decision_input) / "promotion-decision.json").read_text(
            encoding="utf-8"
        )
    )
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    packaged = should_package(decision)
    if packaged:
        shutil.copytree(Path(args.model_input), output / "model")
    (output / "package-info.json").write_text(
        json.dumps(
            {"packaged": packaged, "decision": decision}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
