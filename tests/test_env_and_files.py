"""TEAM/CONTRIBUTING presence + .env discipline tests."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_team_md_present():
    """Catches buggy variant: team submits without filling in TEAM.md."""
    team = REPO_ROOT / "TEAM.md"
    assert team.exists()
    text = team.read_text()
    assert "Backend lead" in text
    assert "Frontend lead" in text
    assert "Infra-Integration lead" in text


def test_contributing_md_present():
    """Catches buggy variant: team submits without the internal-PR
    workflow convention."""
    contrib = REPO_ROOT / "CONTRIBUTING.md"
    assert contrib.exists()
    text = contrib.read_text().lower()
    assert "internal pr" in text or "internal-pr" in text
    assert "teammate" in text or "approval" in text


def test_env_example_no_real_password():
    """Catches buggy variant: real credential committed."""
    env_path = REPO_ROOT / ".env.example"
    assert env_path.exists()
    text = env_path.read_text().lower()
    # Heuristic: include "change", "example", or "placeholder" somewhere.
    assert any(tok in text for tok in ("change", "example", "placeholder", "todo"))


def test_gitignore_excludes_env():
    """Catches buggy variant: .env shipped to GitHub."""
    gi = REPO_ROOT / ".gitignore"
    assert gi.exists()
    # Match a bare `.env` line (not `.env.example`).
    lines = [ln.strip() for ln in gi.read_text().splitlines()]
    assert ".env" in lines
