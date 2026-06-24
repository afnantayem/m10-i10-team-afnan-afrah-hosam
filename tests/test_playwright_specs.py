"""Playwright spec implementation tests.

The starter ships three Playwright specs under
`tests/frontend/playwright/` as `test.skip(...)` stubs that the
Frontend lead is supposed to author. Without a structural check,
skipped tests pass silently — a Frontend lead who submits without
touching the specs gets green CI on the structural job.

These tests enforce that each spec has been authored (no `test.skip`
on the active test block) and contains at least one `expect(` call.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO_ROOT / "tests" / "frontend" / "playwright"
SPECS = ("extract.spec.ts", "kg.spec.ts", "rag.spec.ts")


@pytest.mark.parametrize("spec_name", SPECS)
def test_playwright_spec_authored(spec_name):
    """Catches buggy variant: Frontend lead submits with `test.skip(...)`
    placeholders intact. Skipped tests do not fail, so without this
    check the Playwright stubs ship un-implemented and silently pass."""
    spec_path = SPEC_DIR / spec_name
    assert spec_path.exists(), f"missing Playwright spec: {spec_path}"
    text = spec_path.read_text()

    # No `test.skip(` calls remain (allow `test.skip` in a comment).
    code = re.sub(r"//.*", "", text)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    assert "test.skip(" not in code, (
        f"{spec_name}: replace `test.skip(...)` with an authored "
        f"`test(...)` block. Skipped Playwright tests pass silently."
    )

    # At least one `test(` block exists.
    assert re.search(r"\btest\s*\(", code), (
        f"{spec_name}: must contain at least one `test(...)` block."
    )

    # The authored block must contain at least one assertion.
    assert "expect(" in code, (
        f"{spec_name}: must contain at least one `expect(...)` "
        f"assertion — an empty test body silently passes."
    )
