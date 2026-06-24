"""Pydantic request/response models for the recipe service.

Mirrors `web/lib/types.ts` field-for-field — `chunk_id` not `chunkId`,
`start` not `start_char`. Drift produces silent render failures in the
Next.js frontend.

Constraints below are the source of truth for the autograder's 422 gates.
"""
from typing import List, Literal

from pydantic import BaseModel, Field


# --- /extract --------------------------------------------------------

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class ExtractResponse(BaseModel):
    entities: List[Entity]


# --- /kg/query -------------------------------------------------------

class KGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class KGResponse(BaseModel):
    cypher: str
    rows: List[dict]
    count: int


class UnsupportedQueryDetail(BaseModel):
    reason: Literal["unsupported_question"]
    supported_patterns: List[str]


# --- /rag/answer -----------------------------------------------------

class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    k: int = Field(4, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: int
    score: float


class RAGResponse(BaseModel):
    answer: str
    citations: List[Citation]
    confidence: float


# --- Health / readiness ---------------------------------------------

class HealthResponse(BaseModel):
    status: str


class ReadyDetail(BaseModel):
    neo4j: str
    weaviate: str
