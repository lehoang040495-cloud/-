"""
Import knowledge documents directly (bypass HTTP API to avoid timeout)
"""
import asyncio
import os
import sys
import shutil

# Force offline - model is local
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import async_session, init_db
from app.models import KnowledgeDocument
from app.services.rag_service import rag_service
from app.config import settings


async def import_file(file_path: str, title: str, category: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".pdf", ".docx", ".doc", ".txt", ".xlsx", ".json", ".md"):
        print(f"  SKIP: unsupported type {ext}")
        return 0

    save_dir = os.path.abspath(settings.KNOWLEDGE_PATH)
    os.makedirs(save_dir, exist_ok=True)
    dest_path = os.path.join(save_dir, os.path.basename(file_path))
    if dest_path != file_path:
        shutil.copy2(file_path, dest_path)

    async with async_session() as db:
        doc = KnowledgeDocument(
            title=title,
            file_name=os.path.basename(file_path),
            file_path=dest_path,
            file_type=ext.lstrip("."),
            category=category,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        print(f"  DB record: id={doc.id}")

        print(f"  Extracting text...")
        text = rag_service._extract_text_from_file(dest_path)
        print(f"  Text: {len(text)} chars")

        if not text.strip():
            print(f"  SKIP: no text extracted")
            return 0

        chunks = rag_service._split_text(text)
        print(f"  Chunks: {len(chunks)}")

        if not chunks:
            return 0

        print(f"  Encoding {len(chunks)} chunks...")
        embeddings = await rag_service._encode(chunks)

        if rag_service.index is not None:
            import faiss
            rag_service.index.add(embeddings.astype('float32'))
        else:
            import faiss
            dimension = embeddings.shape[1]
            rag_service.index = faiss.IndexFlatIP(dimension)
            rag_service.index.add(embeddings.astype('float32'))

        for i, chunk in enumerate(chunks):
            rag_service.chunks.append(chunk)
            rag_service.chunk_metadata.append({
                "doc_id": doc.id,
                "title": title,
                "category": category,
                "chunk_index": i,
            })

        rag_service._save_index()
        rag_service._initialized = True

        doc.chunk_count = len(chunks)
        await db.commit()
        print(f"  Done: {len(chunks)} chunks indexed")
        return len(chunks)


async def main():
    await init_db()

    data_dir = os.path.join(
        os.environ.get("TEMP", ""),
        "zip_contents",
        "示范景区公开资料包",
    )

    if not os.path.exists(data_dir):
        print(f"ERROR: Data dir not found: {data_dir}")
        return

    files = [
        ("灵山胜境 景点结构化数据集.docx", "灵山胜境景点结构化数据集", "景点数据"),
        ("灵山胜境：历史、文化、景点特色与个性化游览指南.docx", "灵山胜境历史文化旅游指南", "景区介绍"),
        ("景点景区旅游数据行为分析数据.xlsx", "景点景区旅游行为分析数据", "数据分析"),
    ]

    total = 0
    for fname, title, cat in files:
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            print(f"SKIP: {fname}")
            continue
        size_kb = os.path.getsize(fpath) / 1024
        print(f"\n{'='*60}")
        print(f"Importing: {fname} ({size_kb:.0f}KB)")
        print(f"{'='*60}")
        chunks = await import_file(fpath, title, cat)
        total += chunks

    print(f"\nTotal chunks: {total}")


if __name__ == "__main__":
    asyncio.run(main())
