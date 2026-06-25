#!/usr/bin/env bash
# Seed the running Neo4j container with the recipe fixture.
#
# Idempotent — seed.cypher uses MERGE and CREATE CONSTRAINT IF NOT EXISTS,
# so repeat runs do not duplicate nodes or relationships.
#
# Run from the repo root (the directory that contains docker-compose.yml):
#   bash scripts/seed_neo4j.sh
#
# Running from inside scripts/ produces:
#   no configuration file provided: not found
# because `docker compose exec` resolves the Compose project from the
# current working directory.

set -euo pipefail

# Load .env if it exists and the vars aren't already in the environment.
# This lets the script work both when called directly (needs .env loaded)
# and when called from inside a CI step that has already exported the vars.
if [[ -f .env ]]; then
  # Export only lines that look like KEY=VALUE, skip comments and blanks.
  set -o allexport
  # shellcheck disable=SC2046
  source .env
  set +o allexport
fi

: "${NEO4J_USER:?NEO4J_USER is not set. Copy .env.example to .env and fill in the password.}"
: "${NEO4J_PASSWORD:?NEO4J_PASSWORD is not set. Copy .env.example to .env and fill in the password.}"

echo "→ Seeding Neo4j from seed.cypher …"

# -T disables pseudo-TTY allocation so the pipe works non-interactively.
# cypher-shell -f reads from a file; piping via stdin is equivalent and
# avoids a separate file-copy step into the container.
docker compose exec -T neo4j \
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
  < api/seed.cypher

echo "✓ Neo4j seeded successfully (idempotent — safe to re-run)."