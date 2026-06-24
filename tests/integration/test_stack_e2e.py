"""End-to-end smoke harness — Infra-Integration lead authors.

Brings the four-service stack up via `docker compose up -d --wait` and
verifies the demo `/rag/answer` curl returns 200 with citations against
the seeded fixture. Skipped in the autograder (which exercises compose
topology structurally, not at runtime); used locally during demo-prep
and by the TA during walkthrough.
"""
import os

import pytest


@pytest.mark.skip(reason="TODO (Infra-Integration lead): author the end-to-end harness")
def test_stack_e2e_seeded_rag_query():
    raise NotImplementedError
