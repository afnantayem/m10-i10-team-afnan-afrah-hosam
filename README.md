# Integration 10 — Dockerize the Four-Service Stack

Compose the Lab's FastAPI backend and Next.js frontend with
**containerized Neo4j and Weaviate** into a one-command Dockerized
stack delivered as a 3-Team-Member team.

> Read the full Integration guide on the cohort site:
> <https://LevelUp-Applied-AI.github.io/aispire-14005-pages/modules/module-10/a0cae6a2>
>
> Team-facing spec:
> <https://LevelUp-Applied-AI.github.io/aispire-14005-pages/modules/module-10/4ba363ed>

## Team Roles

See [TEAM.md](TEAM.md) for role assignments and the per-role file checklist.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the internal-PR review convention and the contract-change protocol.

---

## Stack Overview

| Service | Image / Build | Port | Purpose |
|---|---|---|---|
| `neo4j` | `neo4j:5-community` | 7687, 7474 | Recipe knowledge graph |
| `weaviate` | `semitechnologies/weaviate:1.24.10` | 8080 | Vector index for RAG retrieval |
| `api` | `./` + `api/Dockerfile` | 8000 | FastAPI backend (extract, KG query, RAG) |
| `web` | `./web/Dockerfile` | 3000 | Next.js frontend |

Startup order enforced by `depends_on` with `condition: service_healthy`:
`neo4j` + `weaviate` → `api` → `web`

---

## Prerequisites

- Docker Desktop ≥ 4.x (or Docker Engine + Compose plugin v2)
- At least **8 GB RAM** allocated to Docker (16 GB recommended — Neo4j + Weaviate + flan-t5-base are memory-hungry)
- Ports 3000, 7474, 7687, 8000, 8080 free on the host

---

## Runbook — From Clone to Browser Demo

### 1. Clone the team fork

```bash
git clone https://github.com/<team-fork-owner>/m10-i10-team-work.git
cd m10-i10-team-work
```

### 2. Create and configure `.env`

```bash
cp .env.example .env
```

Open `.env` and set a strong password — **never commit this file**:

```dotenv
NEO4J_AUTH=neo4j/your-strong-password
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-strong-password
WEB_ORIGIN=http://localhost:3000
```

> `NEO4J_PASSWORD` must match the value after the `/` in `NEO4J_AUTH`. The api service reads `NEO4J_USER` and `NEO4J_PASSWORD` separately for the Bolt driver connection.

### 3. Build and start the stack

```bash
docker compose up -d --build
```

The first build downloads ~2 GB of layers (Python wheels for `torch`, `transformers`, `sentence-transformers`; Neo4j; Weaviate; Next.js node_modules). Subsequent builds are cached.

### 4. Wait for all services to become healthy

```bash
bash scripts/healthcheck_stack.sh
```

Expected output when ready:

```
✓ All services healthy after Xs.
NAME       STATUS     PORTS
neo4j      healthy    ...
weaviate   healthy    ...
api        healthy    ...
web        healthy    ...
```

You can also watch manually:

```bash
docker compose ps
```

Typical cold-boot timings:

| Service | Typical wait |
|---|---|
| `neo4j` | 30–60 s |
| `weaviate` | 15–30 s |
| `api` | 2–5 min (HuggingFace model download on first boot) |
| `web` | 20–40 s |

> **First boot only:** the `api` container downloads `spaCy en_core_web_sm` and `flan-t5-base` (~1.5 GB total) into the HuggingFace cache. Subsequent starts use the cached models and take ~30 s.

### 5. Seed Neo4j (recipe knowledge graph)

Run from the **repo root** (the directory containing `docker-compose.yml`):

```bash
bash scripts/seed_neo4j.sh
```

Expected output:

```
→ Seeding Neo4j from seed.cypher …
✓ Neo4j seeded successfully (idempotent — safe to re-run).
```

This pipes `seed.cypher` into the running Neo4j container via `cypher-shell`. The script is idempotent — re-running it will not duplicate nodes or relationships (`MERGE` + `CREATE CONSTRAINT IF NOT EXISTS`).

### 6. Seed Weaviate (vector index)

```bash
bash scripts/seed_weaviate.sh
```

Expected output:

```
→ Seeding Weaviate via api container …
Weaviate seeded: N new chunks (idempotent).
✓ Weaviate seeded successfully (idempotent — safe to re-run).
```

This runs `seed_weaviate.py` inside the `api` container (where `sentence-transformers` and `weaviate-client` are already installed). Expected runtime: 10–45 s on a warm image; longer on first run if the `all-MiniLM-L6-v2` model cache is cold (~90 MB download).

### 7. Verify the RAG endpoint

```bash
curl -s -X POST http://localhost:8000/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I prep ginger for stir-fry?"}' | jq .
```

A healthy response looks like:

```json
{
  "answer": "To prep ginger for stir-fry, peel it with a spoon ...",
  "citations": [1, 3],
  "confidence": 0.87
}
```

The response must have a non-empty `answer`, at least one entry in `citations`, and `confidence > 0`.

### 8. Open the web UI

Navigate to **http://localhost:3000/rag** in your browser.

Type the seeded question:

> **Find Sichuan recipes that use ginger**

Click **Submit** and observe a cited answer rendered with inline `[N]` citation markers.

---

## Teardown

To stop the stack and **wipe all data volumes** (clean slate for re-testing):

```bash
docker compose down -v
```

To stop without wiping volumes (data persists across restarts):

```bash
docker compose down
```

---

## Repo Layout

```
api/                        FastAPI backend (Backend lead)
  main.py                   Path operations, lifespan, CORS
  models.py                 Pydantic shapes
  rag.py                    RAG composer
  deps.py                   Depends() functions
  Dockerfile                Single-stage Python 3.11-slim
  seed_weaviate.py          Weaviate seeder (run inside api container)
web/                        Next.js frontend (Frontend lead)
  pages/
    extract.tsx
    kg.tsx
    rag.tsx
  lib/types.ts              TypeScript interfaces mirroring Pydantic
  Dockerfile                Multi-stage Node 20-slim
scripts/                    Infra-Integration lead
  seed_neo4j.sh
  seed_weaviate.sh
  healthcheck_stack.sh
tests/
  frontend/playwright/      Playwright specs (Frontend lead)
  integration/
    test_stack_e2e.py       End-to-end smoke harness (Infra lead)
docker-compose.yml          Four-service topology
seed.cypher                 Recipe graph fixture (12 recipes)
.env.example                Credential placeholders (commit this)
.env                        Real credentials (git-ignored — never commit)
TEAM.md                     Team roster and per-role file checklist
CONTRIBUTING.md             Branch convention and internal-PR protocol
```

---

## Common Pitfalls

| Symptom | Likely cause | Fix |
|---|---|---|
| `api` container exits with `ModuleNotFoundError: No module named 'api'` | `build: ./api` used instead of `context: .` | Use long-form build with `context: .`, `dockerfile: api/Dockerfile` |
| Neo4j healthcheck always fails | `NEO4J_USER`/`NEO4J_PASSWORD` not set in `.env` | Copy `.env.example` to `.env` and fill in the password |
| Weaviate never reaches healthy | `curl` used in healthcheck instead of `wget` | The weaviate image ships `wget`, not `curl`; use `wget --spider` |
| `api` never reaches healthy on cold boot | `start_period` too short | `start_period: 180s` covers the HuggingFace model download |
| Seed script errors: `no configuration file provided` | Script run from inside `scripts/` | Always run seed scripts from the repo root |
| Browser gets no answer / empty citations | Weaviate `DEFAULT_VECTORIZER_MODULE` not set to `none` | Set `DEFAULT_VECTORIZER_MODULE: "none"` in weaviate service env |
| `NEXT_PUBLIC_API_URL` doesn't reach the browser | Set as runtime `environment:` instead of build `args:` | Must be under `services.web.build.args` — Next.js bakes it at build time |

---

## License

This repository is provided for educational use only. See [LICENSE](LICENSE) for terms.
You may clone and modify this repository for personal learning and practice,
and reference code you wrote here in your professional portfolio.
Redistribution outside this course is not permitted.