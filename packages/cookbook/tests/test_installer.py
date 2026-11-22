"""The npx installer: copies skill directories, is idempotent and dry-run safe, and removes only what it installed."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(not NODE, reason="node is not installed")


def install(home: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NODE, str(ROOT / "bin" / "install.mjs"), "--home", str(home), *extra],
        capture_output=True, text=True,
    )


def test_the_installer_copies_a_complete_skill(tmp_path):
    out = install(tmp_path, "--skills", "travel-planner,manage-goals,view-builder")
    assert out.returncode == 0, out.stderr + out.stdout
    skill = tmp_path / ".agents" / "skills" / "travel-planner"
    assert (skill / "SKILL.md").read_text() == (ROOT / "skills" / "travel-planner" / "SKILL.md").read_text()
    assert (skill / "scripts" / "travelplan.py").is_file()
    # No client directory is touched: the client discovers ~/.agents/skills itself.
    assert not (tmp_path / ".claude").exists()


def test_dry_run_writes_nothing_and_a_second_install_is_safe(tmp_path):
    dry = install(tmp_path, "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert not (tmp_path / ".agents").exists()
    assert install(tmp_path).returncode == 0
    assert install(tmp_path).returncode == 0
    assert (tmp_path / ".agents" / "skills" / "manage-goals" / "SKILL.md").is_file()


def test_force_replaces_a_directory_this_package_did_not_install(tmp_path):
    target = tmp_path / ".agents" / "skills" / "travel-planner"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("an older copy\n")
    assert install(tmp_path, "--skills", "travel-planner").returncode == 0
    assert (target / "SKILL.md").read_text() == "an older copy\n"        # without --force it is left alone
    assert install(tmp_path, "--skills", "travel-planner", "--force").returncode == 0
    assert (target / "SKILL.md").read_text() == (ROOT / "skills" / "travel-planner" / "SKILL.md").read_text()


def test_uninstall_removes_only_what_this_package_installed(tmp_path):
    foreign = tmp_path / ".agents" / "skills" / "foreign"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("not ours\n")
    assert install(tmp_path).returncode == 0
    assert install(tmp_path, "--uninstall").returncode == 0
    assert not (tmp_path / ".agents" / "skills" / "travel-planner").exists()
    assert foreign.is_dir()
    assert not (tmp_path / ".agents" / ".nighthawk-skills.json").exists()


def test_uninstall_dry_run_changes_nothing(tmp_path):
    assert install(tmp_path, "--skills", "travel-planner").returncode == 0
    out = install(tmp_path, "--uninstall", "--dry-run")
    assert out.returncode == 0, out.stderr
    assert (tmp_path / ".agents" / "skills" / "travel-planner").is_dir()


def test_list_names_every_skill():
    out = install(Path("/nonexistent"), "--list")
    assert out.returncode == 0, out.stderr
    assert set(out.stdout.split()) == {"fpl-gameweek-planner", "manage-goals", "browser", "travel-planner", "view-builder", "workspace"}


def test_the_package_ships_only_skills():
    pkg = json.loads((ROOT / "package.json").read_text())
    assert pkg["files"] == [
        "bin/", "skills/*/SKILL.md", "skills/*/references/**", "skills/*/scripts/*.py", "skills/*/assets/**", "README.md",
    ]
    assert (ROOT / "skills" / "travel-planner" / "SKILL.md").is_file()
    assert not (ROOT / "Dockerfile").exists()
    assert not (ROOT / "generic").exists()


def test_an_unknown_skill_is_refused(tmp_path):
    out = install(tmp_path, "--skills", "nope")
    assert out.returncode == 1
    assert "unknown skill" in out.stderr
