# Contributing — Module 10 Integration Team

This file is the team's working agreement for the Module 10 four-service Docker Compose Integration. The instructional team pre-populates the conventions; teams do not redesign the workflow — they follow it. Adjustments to the workflow itself require approval from the Support Instructor.

---

## Branch Convention

Each role works on a role-named branch on the team fork. Use these branch prefixes; subdivide if needed:

- `backend/*` — Backend lead (e.g., `backend/api-endpoints`, `backend/lifespan-fix`).
- `frontend/*` — Frontend lead (e.g., `frontend/nextjs-pages`, `frontend/types-mirror`).
- `infra/*` — Infra-Integration lead (e.g., `infra/docker-compose`, `infra/healthchecks`).

Do not push directly to the team fork's `main`. All changes land through internal PRs.

---

## Internal-PR Convention

Each role's branch opens an **internal Pull Request against the team fork's `main`** before any work integrates. The reviewer is the teammate whose contract surface the change touches:

| Branch | Reviewer (role) | Why |
|---|---|---|
| `backend/*` | Frontend lead | OpenAPI / Pydantic shapes are the boundary the Frontend consumes |
| `frontend/*` | Backend lead | `web/lib/types.ts` must mirror Pydantic exactly |
| `infra/*` | Backend lead | Compose service-name DNS, CORS env, and healthchecks must reflect the API contract |

**At least one teammate approval is required** before merging to the team fork's `main`. The reviewer is expected to read the diff substantively, not just click "Approve."

The autograder workflow does not run on internal PRs (it would consume CI minutes three times); it runs on the team submission PR opened from the team fork to upstream (or — equivalent for fork-and-submit pattern — on the team fork's `main` once the team submitter pastes the URL).

---

## Contract-Change Protocol

When a change crosses a role boundary, the role making the change is responsible for communicating it before the change lands. The receiving role's work depends on the announcement.

### Backend → Frontend (Pydantic shape changes)

1. **Announce** the proposed shape change on the team Slack channel with a one-line summary (e.g., "Renaming `chunk_id` → `chunkId` on `Citation` model").
2. **Wait** for the Frontend lead to acknowledge.
3. **Open** the internal PR with the shape change.
4. **The Frontend lead** updates `web/lib/types.ts` in the same review cycle (either on the Backend PR or on a paired Frontend PR).

### Backend → Infra-Integration (env variable changes)

1. Announce the proposed env-var addition or rename on the team Slack channel.
2. Open the internal PR.
3. The Infra-Integration lead updates `.env.example` and `docker-compose.yml` in the same review cycle.

### Frontend → Backend (request for new field)

1. The Frontend lead opens an **internal-PR comment** on the Backend lead's open branch (or files a Slack request if no Backend branch is open) describing the field they need and why.
2. The Backend lead either accepts (and opens an internal PR with the shape change) or counter-proposes (e.g., "use the existing `confidence` field rather than adding `quality_score`").
3. The Frontend lead does **not** assume the field will be added — does not write TypeScript against a hypothetical shape.

### Infra-Integration → Backend / Frontend (DNS, port, or env change)

1. Announce the proposed change on the team Slack channel (e.g., "Switching the Weaviate port mapping from `8080:8080` to `8081:8080` because port 8080 conflicts with `web` on my laptop").
2. Open the internal PR.
3. The Backend lead updates anything that depends on the new value (env defaults, healthcheck targets).

---

## Role-to-Reviewer Mapping (quick reference)

```
Backend lead       → Frontend lead   reviews OpenAPI / Pydantic changes
Frontend lead      → Backend lead    reviews lib/types.ts mirror
Infra-Integration  → Backend lead    reviews docker-compose.yml + env
```

---

## Escalation Protocol

When a disagreement about scope, role boundaries, or contract changes is not resolved within the internal-PR review:

1. **Inline comment on the internal PR.** State the disagreement specifically and link the contract artifact.
2. **Team Slack channel with TA tagged.** Tag the TA who covers the team. Allow up to 4 working hours for response.
3. **Support Instructor.** If the TA decision is contested or the TA is unavailable.
4. **Lead Instructor.** Only if a role-rebalancing decision is needed.

Document the escalation path taken in the team submission PR description so the TA can verify the team-tier grading dimensions are not affected by an unresolved disagreement.

---

## What Counts as "Done"

A role branch is ready to merge to the team fork's `main` when:

- [ ] The reviewer has approved with substantive comments (not just a thumbs-up).
- [ ] Any contract changes are announced and the receiving role has updated their work.
- [ ] The branch's local `docker compose up -d` smoke passes (where applicable to the role).
- [ ] The per-role file checklist entries in `TEAM.md` are checked.

The team is ready for team submission when:

- [ ] All three role branches have merged to the team fork's `main`.
- [ ] Each Team Member has independently run `docker compose up -d` on their machine and confirmed the stack reaches healthy.
- [ ] The demo curl on `/rag/answer` returns 200 with citations for each Team Member.
- [ ] The Playwright `/rag` page renders a cited answer for each Team Member.
- [ ] The team submission PR description includes one per-role contribution paragraph per Team Member.

---

## A Note on Role Drift

A Team Member "helping" by writing files outside their assigned role surface is a **role-drift event**. Role drift dilutes per-role attribution and makes per-role grading harder. If the Backend lead needs help with the Frontend, the right path is to ask the Frontend lead on Slack to address it, not to write the Frontend code themselves.

If a Team Member is consistently blocked and the team is sliding into role drift, escalate to the TA per the Escalation Protocol — role rebalancing is a Support Instructor decision.
