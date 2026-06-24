"""Cross-boundary tests — Backend ↔ Frontend, Infra ↔ Backend.

Each test checks one of the role boundaries called out in
integration-task-spec.md (the per-role contribution surfaces).
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    p = REPO_ROOT / rel
    return p.read_text() if p.exists() else ""


def _pydantic_field_names(py_text: str) -> set[str]:
    """Extract Pydantic field names from `api/models.py` via AST.

    A Pydantic field is any AnnAssign inside a class that inherits from
    something looking like `BaseModel`. Looking at the AST (rather than
    substring-grepping the text) means comments and string literals
    containing field-name tokens do not satisfy the check.
    """
    try:
        tree = ast.parse(py_text)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = " ".join(
            (b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", ""))
            for b in node.bases
        )
        if "BaseModel" not in bases:
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                names.add(stmt.target.id)
    return names


def _ts_interface_field_names(ts_text: str) -> set[str]:
    """Extract typed interface fields from `web/lib/types.ts`.

    Strips block comments (`/* ... */`) and single-line comments (`// ...`)
    first so a stale comment listing the old field name does not satisfy
    the check. Then matches typed-field declarations:

        chunk_id: number;
        score?: number;
        text: string;

    via a regex anchored on the colon. Plain identifiers in prose or
    type-union expressions are not matched.
    """
    # Strip /* ... */ blocks.
    stripped = re.sub(r"/\*.*?\*/", "", ts_text, flags=re.DOTALL)
    # Strip // line comments.
    stripped = re.sub(r"//[^\n]*", "", stripped)
    # Match `name:` or `name?:` at typed-field position. Allow indentation,
    # require the following token to look like a type (lowercase identifier
    # or `Array<…>` / `Citation[]` / `string` / `number` etc.).
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\??\s*:\s*[A-Za-z_]")
    return set(pattern.findall(stripped))


# --- Backend ↔ Frontend ---------------------------------------------

def test_openapi_contract_matches_ts():
    """Catches buggy variant: Backend lead renames a Pydantic field;
    Frontend lead's lib/types.ts is stale → page renders nothing.

    Structural check: every Pydantic field name appearing in
    `api/models.py` for the three response shapes also appears as a
    typed field declaration in `web/lib/types.ts`. AST-extracts the
    Python side; regex-extracts only typed field declarations on the
    TypeScript side. Comment tokens (e.g., `chunk_id` mentioned inside
    a `/* ... */` block) no longer satisfy the assertion.
    """
    py = _read("api/models.py")
    ts = _read("web/lib/types.ts")
    if not py or not ts:
        # If the live integration repo has not yet bundled the lab's
        # api/web, the test cannot run — skip rather than fail.
        import pytest

        pytest.skip("api/models.py or web/lib/types.ts not bundled yet")
    py_fields = _pydantic_field_names(py)
    ts_fields = _ts_interface_field_names(ts)
    required = {"chunk_id", "score", "answer", "citations", "confidence",
                "cypher", "rows", "count", "text", "label", "start", "end",
                "entities"}
    missing_py = required - py_fields
    missing_ts = required - ts_fields
    assert not missing_py, (
        f"api/models.py missing Pydantic field declarations: {sorted(missing_py)}. "
        f"Found: {sorted(py_fields)}"
    )
    assert not missing_ts, (
        f"web/lib/types.ts missing typed field declarations: {sorted(missing_ts)}. "
        f"Found: {sorted(ts_fields)}"
    )


# --- Infra ↔ Backend / Frontend -------------------------------------

def test_compose_healthz_reachable_from_web(compose_config):
    """Catches buggy variant: Infra lead misnames the `api` service,
    misconfigures the network, OR places api and web on disjoint
    custom networks so the web container cannot resolve `api` DNS.

    Three structural checks:
      1. api exposes port 8000 (via `ports` or `expose`).
      2. neither api nor web declares `network_mode: host`.
      3. api and web share at least one Compose network — either both
         use the default network (no `networks:` field), or their
         `networks:` lists intersect. Disjoint custom networks would
         silently break service-name DNS resolution.
    """
    api = compose_config["services"]["api"]
    web = compose_config["services"]["web"]

    # (1) api listener on 8000.
    ports = api.get("ports") or []
    expose = api.get("expose") or []
    has_8000 = any("8000" in str(p) for p in ports) or any("8000" in str(p) for p in expose)
    assert has_8000, "api must expose port 8000 (via `ports` or `expose`)"

    # (2) host-mode kills service DNS for both directions.
    assert api.get("network_mode") != "host", "api on `network_mode: host` cannot use service-name DNS"
    assert web.get("network_mode") != "host", "web on `network_mode: host` cannot use service-name DNS"

    # (3) shared-network check. Compose puts services with no `networks:`
    # field on a single default network — that's the implicit-default
    # case. If either side declares an explicit network list, the lists
    # must intersect.
    def _net_set(svc):
        nets = svc.get("networks")
        if nets is None:
            return None  # implicit default
        if isinstance(nets, list):
            return set(nets)
        if isinstance(nets, dict):
            return set(nets.keys())
        return set()

    api_nets = _net_set(api)
    web_nets = _net_set(web)
    if api_nets is None and web_nets is None:
        return  # both on implicit default; reachable.
    # If only one side declared a network, the other is on default and
    # they cannot reach each other.
    assert api_nets is not None and web_nets is not None, (
        "api and web must both be on the same network. One declared a "
        "custom `networks:` list and the other did not — they will be "
        "on disjoint networks and `http://api:8000` will not resolve."
    )
    shared = api_nets & web_nets
    assert shared, (
        f"api and web are on disjoint networks ({sorted(api_nets)} vs "
        f"{sorted(web_nets)}). `http://api:8000` from the web container "
        f"will not resolve. Put them on at least one shared network."
    )


def test_seed_weaviate_idempotent():
    """Catches buggy variant: Infra lead's seed script runs on every
    `up` and inserts on every run, polluting the index.

    Structural check: the Python seeder must contain an existence
    check (skip-if-exists) or a class-creation guard. We grep the
    actual seeder content; the lab's reference seed_weaviate.py uses
    `schema.exists("Chunk")` and an `existing_ids` skip block.
    """
    p = REPO_ROOT / "api" / "seed_weaviate.py"
    if not p.exists():
        import pytest

        pytest.skip("seed_weaviate.py not bundled yet (lab carry-forward)")
    text = p.read_text()
    assert "schema.exists" in text or "schema.contains" in text or "existing_ids" in text or "exists_in_class" in text
