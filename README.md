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

See [TEAM.md](TEAM.md) for role assignments and the per-role file
checklist. See [CONTRIBUTING.md](CONTRIBUTING.md) for the internal-PR
review convention and the contract-change protocol.

## Starter Layout

```
api/                      Pre-implemented FastAPI backend (do not modify
                          unless extending; the Backend lead extends here)
web/                      Pre-implemented Next.js frontend
docker-compose.yml        Skeleton — Infra-Integration lead authors
scripts/
  seed_neo4j.sh           Stub — Infra-Integration lead authors
  seed_weaviate.sh        Stub — Infra-Integration lead authors
  healthcheck_stack.sh    Stub — Infra-Integration lead authors
.env.example              Placeholder credentials
TEAM.md                   Team roster — team fills in
CONTRIBUTING.md           Branch convention + internal-PR protocol
```

## Bring up the stack (runbook — Infra-Integration lead drafts this)

```bash
cp .env.example .env  # edit values; never commit .env

docker compose up -d --build
bash scripts/healthcheck_stack.sh
bash scripts/seed_neo4j.sh
bash scripts/seed_weaviate.sh

# Demo curl
curl -s -X POST http://localhost:8000/rag/answer \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I prep ginger for stir-fry?"}' | jq .

# Open the web UI at http://localhost:3000/rag
```

## Submission

Team submission (one per team): the team submitter pastes the team
fork's main-branch URL into TalentLMS → Module 10 → Integration Task.

Per-Team-Member participation confirmation (one per Team Member): each
Team Member separately submits a TalentLMS checkbox confirming
participation, naming their assigned role, and naming the files they
authored.

---

## License

This repository is provided for educational use only. See
[LICENSE](LICENSE) for terms. You may clone and modify this repository
for personal learning and practice, and reference code you wrote here
in your professional portfolio. Redistribution outside this course is
not permitted.
