#!/usr/bin/env bash
# Poll `docker compose ps` until all four services report healthy or until
# the 90-second budget expires (45 iterations × 2 s sleep).
#
# Exit 0  — all four services healthy within budget.
# Exit 1  — timeout reached; prints which service(s) are still unhealthy.
#
# Run from the repo root after `docker compose up -d --build`:
#   bash scripts/healthcheck_stack.sh

set -euo pipefail

SERVICES=(neo4j weaviate api web)
MAX_ITERATIONS=180
SLEEP_SECONDS=2

echo "→ Waiting for all services to become healthy (budget: $((MAX_ITERATIONS * SLEEP_SECONDS))s) …"

for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  all_healthy=true
  unhealthy_list=()

  # `docker compose ps --format json` emits one JSON object per line (NDJSON).
  # We extract Name and Health fields with Python to avoid a jq dependency.
  while IFS= read -r line; do
    name=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('Service', d.get('Name','')))" 2>/dev/null || true)
    health=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('Health',''))" 2>/dev/null || true)

    # Only check the four services we own.
    for svc in "${SERVICES[@]}"; do
      if [[ "$name" == "$svc" && "$health" != "healthy" ]]; then
        all_healthy=false
        unhealthy_list+=("$svc($health)")
      fi
    done
  done < <(docker compose ps --format json 2>/dev/null)

  if $all_healthy; then
    echo "✓ All services healthy after $((i * SLEEP_SECONDS))s."
    docker compose ps
    exit 0
  fi

  echo "  [${i}/${MAX_ITERATIONS}] Still waiting: ${unhealthy_list[*]}"
  sleep "$SLEEP_SECONDS"
done

echo "✗ Timeout: the following services did not reach healthy in time:"
docker compose ps
exit 1