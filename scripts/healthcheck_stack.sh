#!/usr/bin/env bash
# Poll `docker compose ps` until all four services report healthy or
# until the 90s budget expires.
#
# TODO (Infra-Integration lead): implement this script.
# - Loop with 2s sleep, up to 45 iterations.
# - Use `docker compose ps --format json` and check Health=="healthy"
#   for api, web, neo4j, weaviate.
# - Exit 0 on all healthy; exit 1 on timeout.

set -euo pipefail
echo "TODO: implement healthcheck_stack.sh"
exit 1
