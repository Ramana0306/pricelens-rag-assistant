from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from .database import Base


def utcnow(): return datetime.now(timezone.utc)

class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    messages: Mapped[list["ChatMessage"]] = relationship(cascade="all, delete-orphan")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(cascade="all, delete-orphan")

class ProductComparison(Base):
    __tablename__ = "product_comparisons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    product_name: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(80), default="product")
    product_data: Mapped[dict] = mapped_column(JSON, default=dict)
    retailers: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    product_key: Mapped[str] = mapped_column(String(300), index=True)
    topic: Mapped[str] = mapped_column(String(100), default="general")
    source_url: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)

Index("ix_chunks_session_product", KnowledgeChunk.session_id, KnowledgeChunk.product_key)
