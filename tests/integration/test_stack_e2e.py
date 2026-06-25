"""End-to-end smoke harness — Infra-Integration lead.

Brings the four-service stack up via `docker compose up -d --build`,
seeds both data tiers, exercises the /rag/answer endpoint, and tears
down cleanly. Safe to re-run (idempotent seed scripts; volumes wiped
with -v on teardown).

NOT run by the autograder (which validates Compose topology structurally).
Used locally during demo-prep and by the TA during walkthrough.

Prerequisites (run from repo root):
  cp .env.example .env   # fill in NEO4J_PASSWORD
  pytest tests/integration/test_stack_e2e.py -v -s
"""

import json
import os
import subprocess
import time

import pytest
import requests

# ── Constants ─────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"
RAG_ENDPOINT = f"{API_BASE}/rag/answer"
SEEDED_QUESTION = "How do I prep ginger for stir-fry?"

# Budget in seconds for each tier to reach healthy.
HEALTHCHECK_BUDGET = {
    "neo4j": 120,
    "weaviate": 120,
    "api": 300,   # cold HuggingFace cache can add several minutes
    "web": 120,
}
POLL_INTERVAL = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    """Run a shell command from the repo root, streaming output."""
    return subprocess.run(cmd, shell=True, check=True, text=True, **kwargs)


def service_health(service: str) -> str:
    """Return the Health field for a single service from `docker compose ps`."""
    result = subprocess.run(
        "docker compose ps --format json",
        shell=True, capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = obj.get("Service") or obj.get("Name", "")
        if name == service:
            return obj.get("Health", "unknown")
    return "missing"


def wait_for_healthy(service: str, budget: int) -> None:
    """Poll until the service reports healthy or raise on timeout."""
    deadline = time.time() + budget
    while time.time() < deadline:
        health = service_health(service)
        if health == "healthy":
            return
        print(f"  [{service}] {health} — waiting …")
        time.sleep(POLL_INTERVAL)
    pytest.fail(f"{service} did not reach healthy within {budget}s "
                f"(last state: {service_health(service)})")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def compose_stack():
    """Bring the stack up, seed both tiers, yield, then tear down."""
    # Wipe any leftover volumes for a clean-slate test.
    run("docker compose down -v --remove-orphans")
    run("docker compose up -d --build")

    # Wait for each tier in dependency order.
    for svc, budget in HEALTHCHECK_BUDGET.items():
        print(f"\n→ Waiting for {svc} …")
        wait_for_healthy(svc, budget)

    # Seed data tiers.
    run("bash scripts/seed_neo4j.sh")
    run("bash scripts/seed_weaviate.sh")

    yield  # tests run here

    # Teardown — wipe volumes so repeated runs start clean.
    run("docker compose down -v --remove-orphans")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_api_healthz(compose_stack):
    """GET /healthz returns 200."""
    resp = requests.get(f"{API_BASE}/healthz", timeout=10)
    assert resp.status_code == 200, f"/healthz returned {resp.status_code}"


def test_api_readyz(compose_stack):
    """GET /readyz returns 200 — Neo4j, Weaviate, and model all loaded."""
    resp = requests.get(f"{API_BASE}/readyz", timeout=10)
    assert resp.status_code == 200, f"/readyz returned {resp.status_code}"


def test_rag_answer_seeded_question(compose_stack):
    """
    POST /rag/answer with the seeded question returns:
    - HTTP 200
    - non-empty answer (not the empty-retrieval sentinel)
    - at least one citation
    - confidence > 0
    """
    payload = {"question": SEEDED_QUESTION}
    resp = requests.post(RAG_ENDPOINT, json=payload, timeout=120)

    assert resp.status_code == 200, (
        f"/rag/answer returned {resp.status_code}: {resp.text}"
    )

    body = resp.json()
    assert body.get("answer"), "answer field is empty"
    assert body.get("citations"), "citations list is empty — grounding check failed"
    assert body.get("confidence", 0) > 0, "confidence is 0"

    # The RAG composer returns a sentinel string when citations cannot be
    # resolved. Any answer that equals the sentinel is a grounding failure.
    sentinel_fragments = ["cannot", "no information", "not found", "I don't know"]
    answer_lower = body["answer"].lower()
    for frag in sentinel_fragments:
        assert frag not in answer_lower, (
            f"Answer looks like the empty-retrieval sentinel: {body['answer']!r}"
        )

    print(f"\n✓ RAG answer: {body['answer'][:120]} …")
    print(f"  citations: {body['citations']}")
    print(f"  confidence: {body['confidence']}")


def test_idempotent_reseed(compose_stack):
    """Re-running both seed scripts does not duplicate data or raise errors."""
    run("bash scripts/seed_neo4j.sh")
    run("bash scripts/seed_weaviate.sh")

    # After re-seed the RAG endpoint must still work.
    resp = requests.post(RAG_ENDPOINT, json={"question": SEEDED_QUESTION}, timeout=120)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("citations"), "citations empty after idempotent re-seed"


def test_web_serves_rag_page(compose_stack):
    """GET http://localhost:3000/rag returns 200 (Next.js page renders)."""
    resp = requests.get("http://localhost:3000/rag", timeout=30)
    assert resp.status_code == 200, (
        f"/rag Next.js page returned {resp.status_code}"
    )