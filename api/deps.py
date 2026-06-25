"""FastAPI dependency-injection helpers.

Resolves process-scoped resources (Neo4j driver, Weaviate client, spaCy
pipeline, flan-t5-base generator, sentence-transformers embedder) that were
constructed exactly once in `main.lifespan` and stored on `app.state`.

Each dependency is a thin accessor — no business logic lives here. The goal
is testability: unit tests can override any dependency via
`app.dependency_overrides[get_session] = lambda: mock_session`.

Integration note for the Infra-Integration lead:
  All five resources are available only after `lifespan` completes. If a
  request arrives while the API container is still loading the HuggingFace
  models (which can take several minutes on a cold cache), the /readyz probe
  returns 503 and `depends_on: condition: service_healthy` keeps the web
  container waiting — this is correct behaviour.
"""
from fastapi import Request


async def get_session(request: Request):
    """Yield a short-lived Neo4j session from the process-scoped driver.

    Uses a context-manager so the session is closed (and the connection
    returned to the driver pool) after the request handler returns, even
    if an exception is raised inside the handler.
    """
    driver = request.app.state.neo4j_driver
    with driver.session() as session:
        yield session


def get_weaviate(request: Request):
    """Return the process-scoped Weaviate client.

    The weaviate.Client is thread-safe and reused across requests.
    """
    return request.app.state.weaviate_client


def get_generator(request: Request):
    """Return the process-scoped flan-t5-base HuggingFace pipeline.

    Loaded once in lifespan from `m8_rag.load_generator`. The pipeline
    object is not thread-safe for simultaneous calls; FastAPI's default
    thread-pool executor serialises non-async route handlers, so this is
    safe for the integration load profile (< 5 concurrent demo requests).
    """
    return request.app.state.generator


def get_nlp(request: Request):
    """Return the process-scoped spaCy pipeline (en_core_web_sm).

    spaCy `Language` objects are safe for concurrent use after loading.
    """
    return request.app.state.nlp


def get_embedder(request: Request):
    """Return the process-scoped sentence-transformers embedder.

    `/rag/answer` uses this to encode the query into the same vector space
    as the chunks seeded by `seed_weaviate.py`, enabling `with_near_vector`
    to return meaningful cosine-similarity results against the
    `vectorizer=none` Weaviate class.

    The SentenceTransformer model (all-MiniLM-L6-v2) must match the model
    used at seed time. Changing either side without changing the other
    causes silent semantic mismatches — retrieved chunks appear relevant
    by distance but are semantically unrelated to the query.
    """
    return request.app.state.embedder