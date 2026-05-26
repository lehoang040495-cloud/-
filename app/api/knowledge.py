"""
Knowledge Base API - CRUD for knowledge documents
"""
import os
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import KnowledgeDocument
from app.schemas import KnowledgeResponse, KnowledgeUpdate, MessageResponse
from app.services.rag_service import rag_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge(
    category: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge documents"""
    query = select(KnowledgeDocument).where(KnowledgeDocument.status == "active")
    if category:
        query = query.where(KnowledgeDocument.category == category)
    query = query.order_by(KnowledgeDocument.created_at.desc())

    result = await db.execute(query)
    docs = result.scalars().all()
    return docs


@router.post("/upload", response_model=KnowledgeResponse)
async def upload_knowledge(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("通用"),
    db: AsyncSession = Depends(get_db),
):
    """Upload a knowledge document and index it"""
    if not title:
        title = Path(file.filename).stem

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".doc", ".txt", ".xlsx", ".json", ".md"):
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Save file
    save_dir = os.path.abspath(settings.KNOWLEDGE_PATH)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create DB record
    doc = KnowledgeDocument(
        title=title,
        file_name=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        category=category,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Index into RAG
    chunk_count = await rag_service.index_document(
        file_path=file_path,
        doc_id=doc.id,
        title=title,
        category=category,
    )

    doc.chunk_count = chunk_count
    await db.commit()
    await db.refresh(doc)

    return doc


@router.put("/{doc_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    doc_id: int,
    update: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update knowledge document metadata"""
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if update.title is not None:
        doc.title = update.title
    if update.category is not None:
        doc.category = update.category
    if update.status is not None:
        doc.status = update.status

    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_knowledge(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a knowledge document"""
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    # Remove from vector store
    await rag_service.remove_document(doc_id)

    # Remove file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()

    return MessageResponse(message="Document deleted successfully")


@router.post("/reindex", response_model=MessageResponse)
async def reindex_knowledge(db: AsyncSession = Depends(get_db)):
    """Re-index all knowledge documents"""
    await rag_service.reindex_all()

    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.status == "active")
    )
    docs = result.scalars().all()

    total_chunks = 0
    for doc in docs:
        if os.path.exists(doc.file_path):
            chunk_count = await rag_service.index_document(
                file_path=doc.file_path,
                doc_id=doc.id,
                title=doc.title,
                category=doc.category,
            )
            doc.chunk_count = chunk_count
            total_chunks += chunk_count

    await db.commit()
    return MessageResponse(message=f"Re-indexed {len(docs)} documents, {total_chunks} chunks")


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all knowledge categories"""
    result = await db.execute(
        select(KnowledgeDocument.category).distinct()
    )
    return {"categories": [row[0] for row in result]}
