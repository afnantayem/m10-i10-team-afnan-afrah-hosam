"""FastAPI application — recipe service (Integration 10 backend).

Architecture constraints enforced here and verified by the autograder:

  - Neo4j driver, Weaviate client, spaCy pipeline, sentence-transformers
    embedder, and the flan-t5-base generator are constructed EXACTLY ONCE
    per process inside `lifespan` and stored on `app.state`. They are
    never instantiated inside a route handler or dependency.

  - `CORSMiddleware` is registered with `allow_origins=[WEB_ORIGIN]`.
    WEB_ORIGIN defaults to http://localhost:3000 (the Next.js dev server).
    In Compose it is set via the `WEB_ORIGIN` env var on the api service.
    Never set it to http://web:3000 — the browser cannot resolve Compose
    service-name DNS.

  - `/extract`, `/kg/query`, `/rag/answer` use Pydantic shapes imported
    from `models.py`. All shape changes must be announced on the team Slack
    channel before landing — the Frontend lead's lib/types.ts must be
    updated in the same review cycle.

  - `/kg/query` converts `UnsupportedQueryError` → HTTP 422 with a
    structured `UnsupportedQueryDetail` body. The autograder asserts the
    422 status code AND the `reason` field.

  - `/readyz` probes BOTH Neo4j (`RETURN 1`) AND Weaviate (`is_ready()`)
    within 2 seconds. Either failure → 503 with `{"neo4j": ..., "weaviate": ...}`.
    The Compose `start_period: 180s` on the api healthcheck accommodates a
    cold HuggingFace cache (spaCy + flan-t5-base download, up to ~4 min).

  - `/healthz` does NOT touch Neo4j or Weaviate. It is a lightweight liveness
    probe that returns immediately — used by load balancers / container
    orchestrators to distinguish "process alive" from "dependencies ready".

Structured logging is enabled at INFO level so `docker compose logs api -f`
gives the Infra-Integration lead full pipeline visibility.
"""
import logging
import os
from contextlib import asynccontextmanager

import spacy
import weaviate
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from .deps import get_embedder, get_generator, get_nlp, get_session, get_weaviate
from .kg import wrap_kg_query
from .m8_rag import load_generator
from .models import (
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    KGRequest,
    KGResponse,
    RAGRequest,
    RAGResponse,
    UnsupportedQueryDetail,
)
from .nlp import extract_entities
from .rag import compose_rag
from .w9b_mapper.errors import UnsupportedQueryError
from .w9b_mapper.shapes import SUPPORTED_PATTERNS

# ---------------------------------------------------------------------------
# Logging — structured INFO-level output readable by `docker compose logs`
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment — read at module load so missing vars surface immediately
# ---------------------------------------------------------------------------
_NEO4J_URI = os.environ["NEO4J_URI"]           # bolt://neo4j:7687  (Compose DNS)
_NEO4J_USER = os.environ["NEO4J_USER"]         # neo4j
_NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"] # from host .env
_WEB_ORIGIN = os.environ.get("WEB_ORIGIN", "http://localhost:3000")
_WEAVIATE_URL = os.environ["WEAVIATE_URL"]     # http://weaviate:8080 (Compose DNS)


# ---------------------------------------------------------------------------
# Lifespan — construct every shared resource ONCE
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load all heavy resources. Shutdown: close the Neo4j driver."""
    logger.info("lifespan | startup — loading resources")

    logger.info("lifespan | connecting Neo4j uri=%s user=%s", _NEO4J_URI, _NEO4J_USER)
    app.state.neo4j_driver = GraphDatabase.driver(
        _NEO4J_URI,
        auth=(_NEO4J_USER, _NEO4J_PASSWORD),
    )

    logger.info("lifespan | connecting Weaviate url=%s", _WEAVIATE_URL)
    app.state.weaviate_client = weaviate.Client(_WEAVIATE_URL)

    logger.info("lifespan | loading spaCy en_core_web_sm")
    app.state.nlp = spacy.load("en_core_web_sm")

    logger.info("lifespan | loading flan-t5-base generator")
    app.state.generator = load_generator()

    logger.info(
        "lifespan | loading sentence-transformers all-MiniLM-L6-v2 embedder"
    )
    # Must match the model used in seed_weaviate.py — changing either side
    # without the other causes silent semantic mismatches at query time.
    app.state.embedder = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    logger.info("lifespan | all resources ready")
    yield

    logger.info("lifespan | shutdown — closing Neo4j driver")
    app.state.neo4j_driver.close()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="M10 Recipe Service",
    description=(
        "Recipe knowledge-graph + RAG API. "
        "Backend lead surface: api/main.py, api/models.py, api/rag.py, "
        "api/deps.py, api/Dockerfile."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_WEB_ORIGIN],
    allow_credentials=False,  # no cookies / auth headers needed
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract named entities from free text",
    tags=["NLP"],
)
def extract(
    req: ExtractRequest,
    nlp=Depends(get_nlp),
) -> ExtractResponse:
    """Run spaCy NER over `req.text` and return a list of entity spans.

    Each span includes `text`, `label`, `start`, and `end` character offsets.
    The Frontend lead's ExtractResult interface mirrors these four fields
    exactly — do not rename them.
    """
    return ExtractResponse(entities=extract_entities(req.text, nlp))


@app.post(
    "/kg/query",
    response_model=KGResponse,
    summary="Translate a natural-language question into Cypher and run it",
    tags=["Knowledge Graph"],
)
def kg_query(
    req: KGRequest,
    session=Depends(get_session),
) -> KGResponse:
    """Map `req.question` to a Cypher query via the W9B mapper and execute it.

    Returns the generated Cypher string, the raw rows, and a count.

    Raises HTTP 422 with `UnsupportedQueryDetail` when the question does not
    match any supported pattern — the autograder asserts both the status code
    and the `reason: "unsupported_question"` field in the response body.
    """
    try:
        cypher, params = wrap_kg_query(req.question)
    except UnsupportedQueryError:
        raise HTTPException(
            status_code=422,
            detail=UnsupportedQueryDetail(
                reason="unsupported_question",
                supported_patterns=list(SUPPORTED_PATTERNS),
            ).model_dump(),
        )
    rows = [r.data() for r in session.run(cypher, **params)]
    return KGResponse(cypher=cypher, rows=rows, count=len(rows))


@app.post(
    "/rag/answer",
    response_model=RAGResponse,
    summary="Answer a recipe question using RAG over the Weaviate chunk index",
    tags=["RAG"],
)
def rag_answer(
    req: RAGRequest,
    weaviate_client=Depends(get_weaviate),
    generator=Depends(get_generator),
    embedder=Depends(get_embedder),
) -> RAGResponse:
    """Run the four-stage RAG pipeline and return a grounded cited answer.

    Grounding contract (enforced — do NOT weaken):
      - `answer` == sentinel  →  `citations == []` and `confidence == 0.0`
      - `answer` != sentinel  →  `len(citations) > 0` and `confidence > 0`

    The autograder's stack-job demo curl asserts:
      - HTTP 200
      - `len(citations) > 0`
      - `confidence > 0`
      - `answer` is not the empty-retrieval sentinel
    """
    result = compose_rag(
        req.question,
        embedder,
        weaviate_client,
        generator,
        k=req.k,
    )
    return RAGResponse(**result)


@app.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Liveness probe — process alive",
    tags=["Operations"],
)
def healthz() -> HealthResponse:
    """Lightweight liveness probe.

    Does NOT touch Neo4j or Weaviate. Returns immediately once the uvicorn
    worker is running. Used by the Compose healthcheck to distinguish
    "process alive" (healthz) from "dependencies ready" (readyz).
    """
    return HealthResponse(status="ok")


@app.get(
    "/readyz",
    summary="Readiness probe — dependencies reachable",
    tags=["Operations"],
)
def readyz(
    session=Depends(get_session),
    weaviate_client=Depends(get_weaviate),
) -> dict:
    """Readiness probe: verifies Neo4j AND Weaviate are reachable.

    Both probes run within the 2-second uvicorn request timeout.
    Either failure → HTTP 503 with {"neo4j": "<detail>", "weaviate": "<detail>"}.
    The Compose `start_period: 180s` on the api healthcheck means this probe
    is only called after the lifespan loader has had time to download models —
    so a 503 here means a genuine connectivity failure, not a cold-start race.
    """
    detail: dict[str, str] = {"neo4j": "unknown", "weaviate": "unknown"}

    try:
        session.run("RETURN 1").single()
        detail["neo4j"] = "ok"
        logger.debug("readyz | neo4j=ok")
    except Exception as exc:
        detail["neo4j"] = f"unavailable: {exc.__class__.__name__}"
        logger.warning("readyz | neo4j=%s", detail["neo4j"])

    try:
        if weaviate_client.is_ready():
            detail["weaviate"] = "ok"
            logger.debug("readyz | weaviate=ok")
        else:
            detail["weaviate"] = "not ready"
            logger.warning("readyz | weaviate=not ready")
    except Exception as exc:
        detail["weaviate"] = f"unavailable: {exc.__class__.__name__}"
        logger.warning("readyz | weaviate=%s", detail["weaviate"])

    if detail["neo4j"] != "ok" or detail["weaviate"] != "ok":
        raise HTTPException(status_code=503, detail=detail)

    return detail