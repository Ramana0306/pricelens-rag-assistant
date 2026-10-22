from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import re

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, init_db, SessionLocal
from .models import GuestSession, ProductComparison, ChatMessage, KnowledgeChunk
from .schemas import AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse, IngestTextRequest
from .product_service import extract_product, chunk_text
from .rag_service import answer_question, embed_text

scheduler = BackgroundScheduler(timezone="UTC")


def now_utc():
    return datetime.now(timezone.utc)


def cleanup_expired_sessions():
    db = SessionLocal()
    try:
        db.execute(delete(GuestSession).where(GuestSession.expires_at < now_utc()))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        scheduler.add_job(cleanup_expired_sessions, "interval", minutes=5, id="guest-session-cleanup", replace_existing=True)
        scheduler.start()
    except Exception as exc:
        print(f"Database startup warning: {exc}")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="PriceLens AI Product RAG API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://pricelens-rag-assistant.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session(x_session_id: str | None, db: Session) -> GuestSession:
    sid = x_session_id or uuid4().hex
    guest = db.get(GuestSession, sid)
    now = now_utc()
    if guest and guest.expires_at <= now:
        db.delete(guest)
        db.commit()
        guest = None
    if not guest:
        guest = GuestSession(id=sid, created_at=now, last_seen_at=now, expires_at=now + timedelta(minutes=settings.session_ttl_minutes))
        db.add(guest)
        db.commit()
        db.refresh(guest)
    else:
        guest.last_seen_at = now
        guest.expires_at = now + timedelta(minutes=settings.session_ttl_minutes)
        db.commit()
    return guest


def _save_product_knowledge(db: Session, guest: GuestSession, product: dict, source_url: str, source_type: str) -> tuple[ProductComparison, int]:
    content = product.get("content", "")
    chunks = chunk_text(content)
    if not chunks:
        raise HTTPException(status_code=422, detail="No usable product text was found. Paste product specifications or description manually.")
    product_for_db = {k: v for k, v in product.items() if k != "content"}
    record = ProductComparison(
        session_id=guest.id,
        source_url=source_url,
        product_name=product.get("name", "Product information")[:300],
        category="product",
        product_data=product_for_db,
        retailers=[],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    saved = 0
    for index, content_chunk in enumerate(chunks, start=1):
        embedding = None
        try:
            embedding = embed_text(content_chunk)
        except Exception as exc:
            # Preserve the text even if the embedding provider is temporarily unavailable.
            print(f"Embedding warning for chunk {index}: {exc}")
        db.add(KnowledgeChunk(
            session_id=guest.id,
            product_key=str(record.id),
            topic=f"product information · chunk {index}",
            source_url=source_url,
            content=content_chunk,
            embedding=embedding,
        ))
        saved += 1
    db.commit()
    product_for_response = dict(product_for_db)
    product_for_response.update({"chunk_count": saved, "character_count": len(content), "source_type": source_type})
    record.product_data = product_for_response
    db.commit()
    return record, saved


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "PriceLens AI Product RAG",
        "llm_configured": bool(settings.gemini_api_key or settings.openai_api_key),
        "embeddings_configured": bool(settings.gemini_api_key or settings.openai_api_key),
        "session_ttl_minutes": settings.session_ttl_minutes,
    }


@app.post("/api/session")
def create_session(db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    guest = get_session(x_session_id, db)
    return {"session_id": guest.id, "expires_at": guest.expires_at.isoformat(), "ttl_minutes": settings.session_ttl_minutes}


@app.delete("/api/session")
def delete_session(db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    if x_session_id:
        guest = db.get(GuestSession, x_session_id)
        if guest:
            db.delete(guest)
            db.commit()
    return {"deleted": True}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    guest = get_session(x_session_id, db)
    try:
        product = extract_product(str(request.url))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    record, chunk_count = _save_product_knowledge(db, guest, product, product["source_url"], "Product webpage")
    response_product = dict(record.product_data)
    response_product.pop("content", None)
    notice = (
        f"Saved {chunk_count} text chunks for retrieval. Page extraction only includes content accessible to the server; "
        "some retailer details may be missing. Answers will be based on the saved text and may not cover information that was not extracted."
    )
    return AnalyzeResponse(comparison_id=record.id, product=response_product, retailers=[], notice=notice)


@app.post("/api/ingest-text", response_model=AnalyzeResponse)
def ingest_text(request: IngestTextRequest, db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    guest = get_session(x_session_id, db)
    content = request.content.strip()
    product = {
        "name": request.title.strip(),
        "brand": "Unknown",
        "category": "Product",
        "model": request.title.strip(),
        "source_url": request.source_url.strip(),
        "description": content[:1200],
        "content": f"Product title: {request.title.strip()}\n\nProduct information supplied by user:\n{content}",
        "image": "",
        "source_type": "Manually added text",
        "highlights": [line.strip(" -*•\t") for line in content.splitlines() if len(line.strip()) > 15][:8],
    }
    record, chunk_count = _save_product_knowledge(db, guest, product, request.source_url.strip(), "Manually added text")
    response_product = dict(record.product_data)
    response_product.pop("content", None)
    return AnalyzeResponse(
        comparison_id=record.id,
        product=response_product,
        retailers=[],
        notice=f"Saved {chunk_count} chunks from the text you supplied. Answers will use this content as evidence.",
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    guest = get_session(x_session_id, db)
    db.add(ChatMessage(session_id=guest.id, role="user", content=request.question))
    db.commit()
    answer, sources = answer_question(db, guest.id, request.question, request.comparison_id)
    db.add(ChatMessage(session_id=guest.id, role="assistant", content=answer))
    db.commit()
    return ChatResponse(answer=answer, sources=sources)


@app.post("/api/knowledge")
def add_knowledge(payload: dict, db: Session = Depends(get_db), x_session_id: str | None = Header(default=None)):
    """Compatibility endpoint for adding a text chunk to the guest knowledge base."""
    guest = get_session(x_session_id, db)
    content = str(payload.get("content", "")).strip()
    if len(content) < 30:
        raise HTTPException(status_code=422, detail="Provide at least 30 characters of product documentation text.")
    if len(content) > 50000:
        raise HTTPException(status_code=413, detail="Text is too long; split it into smaller chunks.")
    embedding = None
    try:
        embedding = embed_text(content)
    except Exception as exc:
        print(f"Embedding warning: {exc}")
    chunk = KnowledgeChunk(
        session_id=guest.id,
        product_key=str(payload.get("product_key", "current-product"))[:300],
        topic=str(payload.get("topic", "general"))[:100],
        source_url=str(payload.get("source_url", ""))[:2000],
        content=content,
        embedding=embedding,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return {"id": chunk.id, "embedded": embedding is not None, "message": "Knowledge saved for this temporary guest session."}
