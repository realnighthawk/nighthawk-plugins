#!/usr/bin/env python3
"""Point oh-my-pi's catalog at a release: every plugin in .omp-plugin/marketplace.json is installed from the repository at TAG, not from whatever main
holds. The catalog itself is still read from main, so a release is the moment a change reaches a user; until then main can move freely.

    scripts/pin-release.py v0.6.0
"""
import json
import pathlib
import re
import sys

URL = "https://github.com/realnighthawk/nighthawk-plugins.git"
CATALOG = pathlib.Path(__file__).resolve().parent.parent / ".omp-plugin" / "marketplace.json"


def pin(catalog: dict, tag: str) -> dict:
    for plugin in catalog["plugins"]:
        source = plugin["source"]
        path = source["path"] if isinstance(source, dict) else source.removeprefix("./")
        plugin["source"] = {"source": "git-subdir", "url": URL, "path": path, "ref": tag}
    return catalog


if __name__ == "__main__":
    if len(sys.argv) != 2 or not re.fullmatch(r"v\d+\.\d+\.\d+", sys.argv[1]):
        sys.exit("usage: pin-release.py vMAJOR.MINOR.PATCH")
    catalog = pin(json.loads(CATALOG.read_text()), sys.argv[1])
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n")
