#!/usr/bin/env python3
"""Refreshes tests/contracts/life-operations.json from the Life engine's own contract (its api/openapi.json).

The skills call the Life engine's tools by name and build its batches by hand, so a renamed or removed operation breaks them silently
(goals_* became intentions_* and nothing here noticed). tests/test_life_contract.py checks the skills against this snapshot; run this
whenever the engine's contract changes and the test tells you what to fix.

    python3 tools/sync_life_contract.py [path/to/life-engine/api/openapi.json]

The snapshot holds only each operation's input schema, with references resolved, so it stays small.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The Life engine checkout is inside the plugin repo, beside it, or beside its parent (a standalone checkout).
CANDIDATES = (ROOT.parents[1] / "life-engine", ROOT.parents[2] / "life-engine", ROOT.parent / "life-engine")
DEFAULT = next(
    (p / "api" / "openapi.json" for p in CANDIDATES if (p / "api" / "openapi.json").is_file()),
    CANDIDATES[0] / "api" / "openapi.json",
)
OUT = ROOT / "tests" / "contracts" / "life-operations.json"


def resolve(node, components, seen=()):
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            if name in seen:
                return {}
            return resolve(components[name], components, seen + (name,))
        return {k: resolve(v, components, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve(v, components, seen) for v in node]
    return node


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    spec = json.loads(source.read_text())
    components = spec.get("components", {}).get("schemas", {})
    operations = {}
    for methods in spec["paths"].values():
        for operation in methods.values():
            if not isinstance(operation, dict) or "operationId" not in operation:
                continue
            body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            operations[operation["operationId"]] = resolve(body, components)
    rev = ""
    try:
        rev = subprocess.run(["git", "-C", str(source.parent.parent), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        pass
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": f"life-engine {rev}".strip(), "operations": dict(sorted(operations.items()))}, indent=1, sort_keys=True) + "\n")
    print(f"{len(operations)} operations from life-engine {rev} -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
