"""Unmodified Starter Failure Rule structural marker.

The other tests in this suite fail against the unmodified starter:
- docker-compose.yml ships `services: {}` → all topology tests fail.
- seed_*.sh scripts contain literal "TODO" → seed tests fail.
- TEAM.md ships with placeholder fields → TEAM.md test may pass
  (it tests presence + role names, not roster fill-in) but the
  topology tests are enough to keep the gate red.

This file exists to document the gate, not to add a new assertion.
"""


def test_unmodified_starter_gate_documented():
    """Pass — see module docstring for the gate's enforcement vector."""
    pass
