"""RAG router — ingest document chunks, query by semantic similarity.
Powers GIRA agentic guidance retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth import require_auth
from src.db import prisma
from src.rag import embed_texts, vector_search
from src.schemas import APIResponse, ok

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestIn(BaseModel):
    source: str
    chunks: list[str]


class QueryIn(BaseModel):
    query: str
    top_k: int = 5


@router.post("/ingest", response_model=APIResponse[dict],
             dependencies=[Depends(require_auth)])
async def ingest(body: IngestIn):
    if not body.chunks:
        raise HTTPException(status_code=422, detail="chunks required")
    vectors = await embed_texts(body.chunks)
    stored = 0
    for text, vec in zip(body.chunks, vectors):
        vec_literal = "[" + ",".join(str(x) for x in vec) + "]"
        await prisma.query_raw(
            'INSERT INTO "DocumentChunk" (id, source, content, embedding, '
            '"createdAt") VALUES (gen_random_uuid(), $1, $2, $3::vector, now())',
            body.source,
            text,
            vec_literal,
        )
        stored += 1
    return ok({"stored": stored, "source": body.source})


@router.post("/query", response_model=APIResponse[list])
async def query(body: QueryIn):
    vectors = await embed_texts([body.query])
    results = await vector_search(
        prisma, vectors[0], top_k=min(body.top_k, 20)
    )
    return ok(results)
