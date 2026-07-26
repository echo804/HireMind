"""Knowledge base service: parsing, chunking, embedding, search"""

import io, uuid, re, logging
from typing import Optional
import fitz
from docx import Document as DocxDocument
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.modules.knowledgebase.models import KnowledgeDocument, KnowledgeChunk

logger = logging.getLogger(__name__)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_pdf(self, content: bytes) -> str:
        doc = fitz.open(stream=content, filetype="pdf")
        return "\n\n".join(page.get_text() for page in doc)

    def _parse_docx(self, content: bytes) -> str:
        doc = DocxDocument(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _parse_txt(self, content: bytes) -> str:
        return content.decode("utf-8", errors="replace")

    def _parse_document(self, content: bytes, file_type: str) -> str:
        parsers = {"pdf": self._parse_pdf, "docx": self._parse_docx, "txt": self._parse_txt, "md": self._parse_txt}
        parser = parsers.get(file_type)
        if not parser:
            raise BusinessException(ErrorCode.BAD_REQUEST, f"Unsupported format: {file_type}")
        return parser(content)

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences = []
        for p in paragraphs:
            parts = re.split(r"(?<=[\u3002\uff01\uff1f.!?\n])", p)
            sentences.extend(s.strip() for s in parts if s.strip())
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) <= CHUNK_SIZE:
                current += s
            else:
                if current:
                    chunks.append(current)
                overlap = current[-CHUNK_OVERLAP:] if current and len(current) > CHUNK_OVERLAP else ""
                current = overlap + s
        if current:
            chunks.append(current)
        return chunks if chunks else [text]

    async def _get_api_config(self):
        from app.config.settings import settings as s
        api_key, base_url = s.AI_BAILIAN_API_KEY, s.AI_BAILIAN_BASE_URL
        if not api_key:
            from app.modules.settings.service import get_active_config
            cfg = get_active_config()
            api_key, base_url = cfg.get("api_key", ""), cfg.get("base_url", "")
        if not api_key:
            raise BusinessException(ErrorCode.BAD_REQUEST, "Configure AI API Key first")
        return api_key, base_url

    async def _embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        import httpx
        api_key, base_url = await self._get_api_config()
        BATCH = 10
        all_results = []
        async with httpx.AsyncClient(timeout=120) as client:
            for start in range(0, len(chunks), BATCH):
                batch = chunks[start:start + BATCH]
                resp = await client.post(f"{base_url}/embeddings", json={"model": "text-embedding-v3", "input": batch},
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                if resp.status_code != 200:
                    logger.error(f"Embedding API: {resp.status_code} {resp.text[:300]}")
                    raise BusinessException(ErrorCode.AI_SERVICE_UNAVAILABLE, f"Embedding failed: {resp.status_code}")
                data = resp.json()
                result = [None] * len(batch)
                for item in data["data"]:
                    result[item["index"]] = item["embedding"]
                all_results.extend(result)
        return all_results

    async def upload_document(self, user_id: str, content: bytes, filename: str) -> dict:
        ft = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        if ft not in ("pdf", "docx", "txt", "md"):
            raise BusinessException(ErrorCode.BAD_REQUEST, f"Unsupported: {ft}")
        doc = KnowledgeDocument(user_id=uuid.UUID(user_id), filename=filename, file_type=ft, file_size=len(content), status="processing")
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        try:
            raw = self._parse_document(content, ft)
            if not raw.strip():
                raise BusinessException(ErrorCode.BAD_REQUEST, "No extractable text")
            chunks = self._chunk_text(raw)
            logger.info(f"Doc {doc.id}: {len(chunks)} chunks")
            embeddings = await self._embed_chunks(chunks)
            for i, (ct, em) in enumerate(zip(chunks, embeddings)):
                self.db.add(KnowledgeChunk(document_id=doc.id, chunk_index=i, content=ct, embedding=em))
            doc.status, doc.chunk_count = "ready", len(chunks)
            await self.db.commit()
            await self.db.refresh(doc)
        except Exception as e:
            doc.status, doc.error_message = "failed", str(e)
            await self.db.commit()
            raise
        return doc.to_dict()



    async def get_document_content(self, doc_id: str, user_id: str) -> dict:
        """Get document with all its chunks"""
        did, uid = uuid.UUID(doc_id), uuid.UUID(user_id)
        r = await self.db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == did,
                KnowledgeDocument.user_id == uid,
            )
        )
        doc = r.scalar_one_or_none()
        if not doc:
            raise BusinessException(ErrorCode.NOT_FOUND, "Document not found")

        # Get chunks
        cr = await self.db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == did)
            .order_by(KnowledgeChunk.chunk_index)
        )
        chunks = cr.scalars().all()

        return {
            **doc.to_dict(),
            "chunks": [
                {"index": c.chunk_index, "content": c.content}
                for c in chunks
            ],
        }

    async def list_documents(self, user_id: str) -> list[dict]:
        r = await self.db.execute(select(KnowledgeDocument).where(KnowledgeDocument.user_id == uuid.UUID(user_id)).order_by(KnowledgeDocument.created_at.desc()))
        return [d.to_dict() for d in r.scalars().all()]

    async def delete_document(self, doc_id: str, user_id: str):
        did, uid = uuid.UUID(doc_id), uuid.UUID(user_id)
        r = await self.db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == did, KnowledgeDocument.user_id == uid))
        doc = r.scalar_one_or_none()
        if not doc:
            raise BusinessException(ErrorCode.NOT_FOUND, "Document not found")
        await self.db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == did))
        await self.db.delete(doc)
        await self.db.commit()

    async def search(self, query: str, top_k: int = 3, user_id: Optional[str] = None) -> list[dict]:
        import httpx
        api_key, base_url = await self._get_api_config()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{base_url}/embeddings", json={"model": "text-embedding-v3", "input": query},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
            if resp.status_code != 200:
                logger.error(f"Query embedding: {resp.status_code} {resp.text[:300]}")
                raise BusinessException(ErrorCode.AI_SERVICE_UNAVAILABLE, f"Query embedding: {resp.status_code}")
            qvec = resp.json()["data"][0]["embedding"]
        vs = "[" + ",".join(str(v) for v in qvec) + "]"
        wc = "AND kd.user_id = :uid::uuid" if user_id else ""
        params = {"emb": vs, "emb2": vs, "top": top_k}
        if user_id:
            params["uid"] = user_id
        sql = text(f"""
            SELECT kc.content, kc.chunk_index,
                   1 - (kc.embedding <=> :emb) AS score,
                   kd.filename AS doc_name
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kd.status = 'ready' {wc}
            ORDER BY kc.embedding <=> :emb2
            LIMIT :top
        """)
        rows = (await self.db.execute(sql, params)).fetchall()
        return [{"content": r[0], "chunk_index": r[1], "score": float(r[2]), "document_name": r[3]} for r in rows]
