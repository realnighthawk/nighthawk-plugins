#!/bin/sh
# Make a release: the omp catalog is pointed at the new tag, the tag is made and pushed, and the GitHub release is created. Run from a clean main.
#   scripts/release.sh v0.6.0
# What people and sandboxes install is what the latest release holds (see scripts/pin-release.py); nothing on main reaches them before this.
set -eu
tag=${1:?usage: scripts/release.sh vMAJOR.MINOR.PATCH}
cd "$(dirname "$0")/.."
[ "$(git rev-parse --abbrev-ref HEAD)" = main ] || { echo "release from main" >&2; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "commit or stash your changes first" >&2; exit 1; }
git fetch -q origin && [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "main is not the same as origin/main" >&2; exit 1; }
make check
python3 scripts/pin-release.py "$tag"
git commit -qam "release $tag: the omp catalog installs from $tag"
git tag -a "$tag" -m "$tag"
git push -q origin main "$tag"
gh release create "$tag" --generate-notes --title "$tag"
