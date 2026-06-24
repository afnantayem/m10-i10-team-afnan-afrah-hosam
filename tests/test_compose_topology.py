"""Compose topology + service-config structural tests.

Every test maps to a "Catches buggy variant" row in integration-task-spec.md
Test Plan.
"""
from pathlib import Path

import pytest

from tests.conftest import normalize_env

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_compose_declares_four_services(compose_config):
    """Catches buggy variant: learner omits a service."""
    services = compose_config.get("services") or {}
    for s in ("api", "web", "neo4j", "weaviate"):
        assert s in services, f"missing service {s!r}"


def test_neo4j_has_memory_caps(compose_config):
    """Catches buggy variant: OOM under load on 16 GB laptop."""
    env = normalize_env(compose_config["services"]["neo4j"].get("environment"))
    assert env.get("NEO4J_dbms_memory_heap_max__size") == "1G"
    assert env.get("NEO4J_dbms_memory_pagecache_size") == "512M"


def test_neo4j_has_named_volume(compose_config):
    """Catches buggy variant: anonymous volume → silent data loss on down -v."""
    svc = compose_config["services"]["neo4j"]
    volumes = svc.get("volumes") or []
    assert any("neo4j_data" in v and "/data" in v for v in volumes), volumes
    top_volumes = compose_config.get("volumes") or {}
    assert "neo4j_data" in top_volumes


def test_neo4j_has_healthcheck(compose_config):
    """Catches buggy variant: omitted healthcheck silently degrades
    `condition: service_healthy`."""
    hc = compose_config["services"]["neo4j"].get("healthcheck") or {}
    test_block = " ".join(hc.get("test", [])) if isinstance(hc.get("test"), list) else str(hc.get("test", ""))
    assert "cypher-shell" in test_block or "RETURN 1" in test_block


def test_weaviate_has_named_volume(compose_config):
    """Catches buggy variant: anonymous volume."""
    svc = compose_config["services"]["weaviate"]
    volumes = svc.get("volumes") or []
    assert any("weaviate_data" in v and "/var/lib/weaviate" in v for v in volumes)
    assert "weaviate_data" in (compose_config.get("volumes") or {})


def test_weaviate_has_healthcheck(compose_config):
    """Catches buggy variant: omitted."""
    hc = compose_config["services"]["weaviate"].get("healthcheck") or {}
    test_block = " ".join(hc.get("test", [])) if isinstance(hc.get("test"), list) else str(hc.get("test", ""))
    assert "v1/.well-known/ready" in test_block


def test_weaviate_has_vectorizer_module_none(compose_config):
    """Catches buggy variant: default vectorizer conflict — silent
    insert failures."""
    env = normalize_env(compose_config["services"]["weaviate"].get("environment"))
    assert env.get("DEFAULT_VECTORIZER_MODULE") == "none"


def test_api_depends_on_neo4j_and_weaviate_healthy(compose_config):
    """Catches buggy variant: bare depends_on list → race condition."""
    deps = compose_config["services"]["api"].get("depends_on")
    assert isinstance(deps, dict), "Use long-form depends_on with conditions"
    for backend in ("neo4j", "weaviate"):
        assert backend in deps
        assert deps[backend].get("condition") == "service_healthy"


def test_api_uri_uses_compose_dns(compose_config):
    """Catches buggy variant: learner copies localhost from Lab env into
    the api container."""
    env = normalize_env(compose_config["services"]["api"].get("environment"))
    assert env.get("NEO4J_URI") == "bolt://neo4j:7687"
    assert env.get("WEAVIATE_URL") == "http://weaviate:8080"


def test_web_depends_on_api_healthy(compose_config):
    """Catches buggy variant: bare or missing."""
    deps = compose_config["services"]["web"].get("depends_on")
    assert isinstance(deps, dict)
    assert deps.get("api", {}).get("condition") == "service_healthy"


def test_web_uses_localhost_api_url(compose_config):
    """Catches buggy variant: learner uses http://api:8000 — browser
    cannot resolve service-name DNS — OR learner sets the URL as a
    runtime environment variable instead of a Next.js build arg.

    Per the guide's Web service section: NEXT_PUBLIC_API_URL is **baked at
    build time** by Next.js into the client-side bundle, so it must be
    declared under `services.web.build.args` (not `environment`).
    """
    web_svc = compose_config["services"]["web"]
    build = web_svc.get("build")
    args = {}
    if isinstance(build, dict):
        args = build.get("args") or {}
        # Compose accepts args as a list of "KEY=value" entries too.
        if isinstance(args, list):
            args = dict(s.split("=", 1) for s in args if "=" in s)
    url = args.get("NEXT_PUBLIC_API_URL", "")
    assert url, (
        "NEXT_PUBLIC_API_URL must be declared as a build arg under "
        "`services.web.build.args` — Next.js bakes NEXT_PUBLIC_* values "
        "into the client bundle at build time, so a runtime "
        "`environment:` entry never reaches the browser."
    )
    assert "localhost" in url
    assert "//api:" not in url


def test_api_has_healthcheck(compose_config):
    """Catches buggy variant: omitted — web's depends_on degrades to
    container-start only."""
    hc = compose_config["services"]["api"].get("healthcheck") or {}
    assert hc.get("test")


def test_api_build_context_is_repo_root(compose_config):
    """Catches buggy variant: learner writes `build: ./api` (the
    intuitive form). Image builds, but the api container crashes at
    startup with `ModuleNotFoundError: No module named 'api'` because
    the package-relative imports in api/main.py require the repo root
    as the build context.

    Per the guide's Infra-Integration section: api service must use
    `build: { context: ., dockerfile: api/Dockerfile }`.
    """
    build = compose_config["services"]["api"].get("build")
    assert isinstance(build, dict), (
        "api.build must be the long-form mapping with `context` and "
        "`dockerfile`. The short form `build: ./api` produces a "
        "container that crashes at startup with "
        "`ModuleNotFoundError: No module named 'api'` because the "
        "package-relative imports require the repo root as context."
    )
    assert build.get("context") in (".", "./"), (
        f"api.build.context must be the repo root ('.'). Got "
        f"{build.get('context')!r}."
    )
    assert build.get("dockerfile") == "api/Dockerfile", (
        f"api.build.dockerfile must be 'api/Dockerfile' so the build "
        f"finds the Dockerfile relative to the repo root. Got "
        f"{build.get('dockerfile')!r}."
    )


def test_neo4j_healthcheck_passes_credentials(compose_config):
    """Catches buggy variant: learner hardcodes the password in the
    healthcheck or omits credential interpolation entirely.

    The guide specifies `cypher-shell -u neo4j -p ${NEO4J_PASSWORD}` so
    that Compose interpolates the password from .env at parse time. A
    hardcoded password or a missing credential turns the healthcheck
    into a silent pass that doesn't actually verify auth.
    """
    hc = compose_config["services"]["neo4j"].get("healthcheck") or {}
    test_block = (
        " ".join(hc.get("test", []))
        if isinstance(hc.get("test"), list)
        else str(hc.get("test", ""))
    )
    # Require the substitution form. The previous version accepted the
    # CI-rendered literal `testtest12345` so a learner who copy-pasted
    # the CI password directly into the healthcheck (instead of
    # `$NEO4J_PASSWORD`) would pass and ship a hardcoded credential —
    # the same silent-pass failure mode this test was meant to catch.
    assert any(
        token in test_block
        for token in ("$NEO4J_PASSWORD", "${NEO4J_PASSWORD}")
    ), (
        f"neo4j healthcheck must pass the password via "
        f"`${{NEO4J_PASSWORD}}` interpolation, not hardcoded. "
        f"Got: {test_block!r}"
    )
