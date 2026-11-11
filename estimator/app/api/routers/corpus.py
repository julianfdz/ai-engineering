"""``GET /api/v1/corpus`` — read-only view of what is indexed (local addition for the live session).

Lists the three Session 10 collections (budget, transcript, technical_doc) so the
client can render the corpus: totals per ``chunk_type`` and a paginated page of
chunks with their metadata. Embeddings are never returned (1536 floats each).

Thin transport over the chunk tables; no business logic, no auth (same as the
``/api/v1/config`` read endpoints the Ajustes tab uses).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select

from app.foundation.persistence.database import get_async_session_factory
from app.generation.rag.retrieval.collections import Collection, spec_for
from app.generation.rag.store.models import DocumentRow

router = APIRouter(prefix="/api/v1/corpus", tags=["corpus"])


class CollectionSummary(BaseModel):
    collection: str
    table: str
    total_chunks: int
    by_chunk_type: dict[str, int]


class CorpusSummary(BaseModel):
    collections: list[CollectionSummary]


class CorpusChunk(BaseModel):
    id: int
    chunk_type: str
    content: str
    metadata: dict
    source_path: str | None
    document_type: str | None


class CorpusPage(BaseModel):
    collection: str
    total: int
    limit: int
    offset: int
    chunks: list[CorpusChunk]


@router.get("", response_model=CorpusSummary)
async def summary() -> CorpusSummary:
    """Chunk totals per collection and per ``chunk_type``."""
    factory = get_async_session_factory()
    out: list[CollectionSummary] = []
    async with factory() as session:
        for collection in Collection:
            model = spec_for(collection).model
            rows = (
                await session.execute(select(model.chunk_type, func.count()).group_by(model.chunk_type))
            ).all()
            by_type = {chunk_type: count for chunk_type, count in rows}
            out.append(
                CollectionSummary(
                    collection=collection.value,
                    table=model.__tablename__,
                    total_chunks=sum(by_type.values()),
                    by_chunk_type=by_type,
                )
            )
    return CorpusSummary(collections=out)


@router.get("/{collection}", response_model=CorpusPage)
async def list_chunks(
    collection: str,
    chunk_type: str | None = None,
    q: str | None = Query(default=None, description="Case-insensitive substring over the chunk text."),
    limit: int = Query(default=30, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CorpusPage:
    """One page of chunks of a collection, optionally filtered by type and text."""
    try:
        spec = spec_for(Collection(collection))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown collection: {collection}") from exc
    model = spec.model

    conditions = []
    if chunk_type:
        conditions.append(model.chunk_type == chunk_type)
    if q:
        conditions.append(or_(model.content.ilike(f"%{q}%")))

    factory = get_async_session_factory()
    async with factory() as session:
        total = (await session.execute(select(func.count()).select_from(model).where(*conditions))).scalar_one()
        rows = (
            await session.execute(
                select(model, DocumentRow.source_path, DocumentRow.document_type)
                .join(DocumentRow, DocumentRow.id == model.document_id, isouter=True)
                .where(*conditions)
                .order_by(model.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()

    chunks = [
        CorpusChunk(
            id=row.id,
            chunk_type=row.chunk_type,
            content=row.content,
            metadata=row.metadata_ or {},
            source_path=source_path,
            document_type=document_type,
        )
        for row, source_path, document_type in rows
    ]
    return CorpusPage(collection=collection, total=total, limit=limit, offset=offset, chunks=chunks)
