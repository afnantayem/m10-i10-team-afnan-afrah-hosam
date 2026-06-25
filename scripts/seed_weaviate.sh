#!/usr/bin/env bash
# Seed the running Weaviate container with the chunked-docs fixture.
#
# Idempotent — seed_weaviate.py skips chunk_ids that already exist in
# the Chunk class, so repeat runs do not duplicate vectors.
#
# Run from the repo root (the directory that contains docker-compose.yml):
#   bash scripts/seed_weaviate.sh
#
# WHY we run inside the api container (not on the host):
#   sentence-transformers, weaviate-client, and the other api requirements
#   live in the api image. Running `python api/seed_weaviate.py` from the host
#   venv only works if the learner has manually installed all api requirements
#   locally — this script must not depend on that.
#
# Expected runtime: ~10–45 s on a warm image (sentence-transformers already
# downloaded). First boot may take longer if the HuggingFace model cache is
# cold (all-MiniLM-L6-v2 downloads ~90 MB).

set -euo pipefail

echo "→ Seeding Weaviate via api container …"

# seed_weaviate.py lives at api/seed_weaviate.py in the repo, but the api
# Dockerfile sets WORKDIR /app and COPYs the api/ directory there, so inside
# the container the script is at /app/api/seed_weaviate.py.
# -T disables pseudo-TTY allocation so the command runs non-interactively.
docker compose exec -T api python api/seed_weaviate.py

echo "✓ Weaviate seeded successfully (idempotent — safe to re-run)."