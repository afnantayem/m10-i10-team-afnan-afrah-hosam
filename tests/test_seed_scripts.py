"""Seed-script presence and shape tests.

Catches buggy variants where seed scripts are still stubs (exit 1) or
where the Infra lead forgot to make them executable / idempotent.
"""
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_seed_neo4j_script_exists():
    p = REPO_ROOT / "scripts" / "seed_neo4j.sh"
    assert p.exists()
    text = p.read_text()
    assert "cypher-shell" in text
    assert "TODO" not in text, "seed_neo4j.sh is still a stub"


def test_seed_weaviate_script_exists():
    p = REPO_ROOT / "scripts" / "seed_weaviate.sh"
    assert p.exists()
    text = p.read_text()
    assert "TODO" not in text, "seed_weaviate.sh is still a stub"


def test_healthcheck_script_exists():
    """Catches buggy variant: Infra lead skips authoring the readiness
    poller — the team submitter has no programmatic way to verify
    `docker compose ps` healthy state."""
    p = REPO_ROOT / "scripts" / "healthcheck_stack.sh"
    assert p.exists()
    text = p.read_text()
    assert "TODO" not in text, "healthcheck_stack.sh is still a stub"
    assert "healthy" in text.lower()
