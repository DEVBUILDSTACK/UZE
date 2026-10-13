"""RAG — embeddings + pgvector similarity search for GIRA guidance.

Pipeline: chunk content -> embed (OpenAI-compatible API) -> store as
pgvector(1536) -> cosine-similarity search at query time.

Env (add to .env / Secret Manager):
  EMBEDDING_BASE_URL   e.g. https://api.openai.com/v1
  EMBEDDING_API_KEY    secret — never baked into images
  EMBEDDING_MODEL      e.g. text-embedding-3-small (1536 dims)
"""
import httpx

from src.config import settings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via an OpenAI-compatible embeddings API."""
    base = getattr(settings, "EMBEDDING_BASE_URL", "")
    key = getattr(settings, "EMBEDDING_API_KEY", "")
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small")
    if not base or not key:
        raise RuntimeError(
            "EMBEDDING_BASE_URL / EMBEDDING_API_KEY not set — "
            "see .env.example."
        )
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
    return [row["embedding"] for row in sorted(data, key=lambda r: r["index"])]


async def vector_search(prisma, query_vector: list[float], top_k: int = 5):
    """Cosine-similarity search over DocumentChunk embeddings."""
    vec = "[" + ",".join(str(x) for x in query_vector) + "]"
    rows = await prisma.query_raw(
        """
        SELECT id, source, content,
               1 - (embedding <=> $1::vector) AS score
        FROM "DocumentChunk"
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1::vector
        LIMIT $2
        """,
        vec,
        top_k,
    )
    return [
        {"id": r["id"], "source": r["source"],
         "content": r["content"], "score": float(r["score"])}
        for r in rows
    ]
