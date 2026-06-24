# Team Roster — Module 10 Integration

This file is the team roster artifact for the Module 10 four-service Docker Compose Integration. The instructional team pre-populates the role assignments before handing the template repo to the team; the team fills in the Team Member identifier, branch, and Slack channel fields.

> **No personal names** in this file. Use anonymized initials, role tokens, or team-chosen identifiers. The team grading and TA cross-reference use `git log --author=<email>` for attribution, not names in this file.

---

## Team Identity

- **Team name:** _(team-chosen identifier — e.g., `team-aurora`)_
- **Team Slack channel:** _(cohort Slack channel — e.g., `#m10-team-aurora`)_
- **Team-formation date:** _(YYYY-MM-DD — the date the instructional team posted the roster)_
- **Designated team submitter:** _(role token — typically `Infra-Integration lead`)_

---

## Team Roster

| Role | Team Member identifier | Assigned by | Branch | Internal-PR reviewer | Primary files owned |
|---|---|---|---|---|---|
| Backend lead | _(initials or anon ID)_ | Instructional team | `backend/api-endpoints` | Frontend lead | `api/main.py`, `api/models.py`, `api/rag.py`, `api/deps.py`, `api/Dockerfile` |
| Frontend lead | _(initials or anon ID)_ | Instructional team | `frontend/nextjs-pages` | Backend lead | `web/pages/{extract,kg,rag}.tsx`, `web/lib/types.ts`, `web/Dockerfile`, `tests/frontend/playwright/*` |
| Infra-Integration lead | _(initials or anon ID)_ | Instructional team | `infra/docker-compose` | Backend lead | `docker-compose.yml`, `seed_neo4j.sh`, `seed_weaviate.sh`, `.env.example`, `README.md`, `tests/integration/*` |

**Fallback compositions for non-3-Team-Member teams:**

- **2 Team Members:** Frontend and Infra-Integration roles merge. The merged Team Member owns all `web/`, `docker-compose.yml`, and `seed_*.sh` files.
- **4 Team Members:** Infra-Integration splits into "Compose + healthchecks" (owns `docker-compose.yml`, all healthchecks, readiness ordering) and "Seed + runbook" (owns `seed_neo4j.sh`, `seed_weaviate.sh`, `README.md` runbook). The two Team Members internal-review each other.

---

## Per-Role File Checklist (used for TA grading cross-reference)

The TA cross-references this checklist against `git log --author=<email>` on the team fork during per-role grading. Check the box when the Team Member confirms they authored the file.

### Backend lead

- [ ] `api/main.py` — path operations, `lifespan`, CORS middleware
- [ ] `api/models.py` — Pydantic shapes
- [ ] `api/rag.py` — RAG composer with grounding contract
- [ ] `api/deps.py` — `Depends()` functions
- [ ] `api/Dockerfile` — single-stage Python

### Frontend lead

- [ ] `web/pages/extract.tsx`
- [ ] `web/pages/kg.tsx`
- [ ] `web/pages/rag.tsx`
- [ ] `web/lib/types.ts` — three TypeScript interfaces mirroring Pydantic
- [ ] `web/Dockerfile` — multi-stage Node
- [ ] `tests/frontend/playwright/*.spec.ts` — one per page

### Infra-Integration lead

- [ ] `docker-compose.yml` — four services, healthchecks, `depends_on` chain, named volumes
- [ ] `seed_neo4j.sh`
- [ ] `seed_weaviate.sh`
- [ ] `.env.example` (no real credentials)
- [ ] `README.md` runbook
- [ ] `tests/integration/test_stack_e2e.py`

---

## Escalation Checklist (apply in order)

When a disagreement about scope, role boundaries, or contract changes arises:

1. **Inline comment on the internal PR.** State the disagreement specifically and link the contract artifact (Pydantic shape, TypeScript interface, Compose service entry).
2. **Team Slack channel with TA tagged.** Tag the TA who covers the team. Allow up to 4 working hours for response.
3. **Support Instructor.** If the TA decision is contested or the TA is unavailable, escalate to the Support Instructor via the cohort Slack channel.
4. **Lead Instructor.** Only if a role-rebalancing decision is needed or the disagreement is not resolved by the Support Instructor.

Document the escalation path taken in the team submission PR description.

---

## Contract-Change Protocol

- **Backend lead** announces any Pydantic shape change on the team Slack channel **before** the change lands.
- **Frontend lead** requests new backend fields via an internal-PR comment on the Backend lead's branch — does not assume.
- **Infra-Integration lead** announces any `.env` or DNS-affecting change before the change lands.

The protocol is enforced by the internal-PR review — the reviewer rejects PRs where the contract change was not announced.

---

## Submission

When all three role branches merge to the team fork's `main` and `docker compose up -d` smoke passes locally for each Team Member:

1. The team submitter pastes the team fork URL into TalentLMS → Module 10 → Integration Task.
2. Each Team Member separately submits the participation-confirmation TalentLMS unit naming their assigned role and the files they authored.

The two-tier grading model (team tier 60 pts + per-role tier 40 pts) is described in the team-facing Integration Spec at <https://LevelUp-Applied-AI.github.io/aispire-14005-pages/modules/module-10/4ba363ed>.
