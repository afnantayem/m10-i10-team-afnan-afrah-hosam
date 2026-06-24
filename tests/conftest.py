"""Shared fixtures for Integration 10 autograder.

Per the Autograder Test Path Rule, `..` is the insertion (`starter/`
becomes repo root after template push).
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def compose_config():
    """Parsed docker-compose.yml as a dict."""
    yaml = pytest.importorskip("yaml")
    with open(REPO_ROOT / "docker-compose.yml") as f:
        return yaml.safe_load(f)


def normalize_env(env):
    """Compose accepts either a list `KEY=value` or a dict `{KEY: value}`."""
    if env is None:
        return {}
    if isinstance(env, list):
        return dict(item.split("=", 1) for item in env)
    return {k: str(v) for k, v in env.items()}
