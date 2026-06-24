#!/usr/bin/env bash
# Seed the running Neo4j container with the recipe fixture.
#
# Idempotent — `MERGE` and `CREATE CONSTRAINT IF NOT EXISTS` in seed.cypher
# mean repeat runs do not duplicate nodes.
#
# TODO (Infra-Integration lead): implement this script.
# Required:
# - Read NEO4J_USER and NEO4J_PASSWORD from the environment (loaded
#   from .env by docker compose).
# - Pipe seed.cypher into the neo4j container via
#   `docker compose exec -T neo4j cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD`.
# - Print a one-line confirmation.

set -euo pipefail
echo "TODO: implement seed_neo4j.sh"
exit 1
