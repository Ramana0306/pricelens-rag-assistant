
"""Embedding, retrieval and grounded answer generation for PriceLens AI."""
from __future__ import annotations

import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import KnowledgeChunk


def embed_text(text: str):
    text = (text or "").strip()[:8000]
    if not text:
        return None

    if settings.gemini_api_key:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        result = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config={"output_dimensionality": 1536},
        )
        return list(result.embeddings[0].values)

    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        result = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        values = result.data[0].embedding

        if len(values) != 1536:
            raise RuntimeError(
                f"The embedding model returned {len(values)} dimensions; "
                "the database expects 1536."
            )

        return values

    return None


def _retrieve_chunks(
    db: Session,
    session_id: str,
    question: str,
    comparison_id: int | None,
):
    stmt = select(KnowledgeChunk).where(
        KnowledgeChunk.session_id == session_id
    )

    if comparison_id is not None:
        stmt = stmt.where(
            KnowledgeChunk.product_key == str(comparison_id)
        )

    chunks = db.scalars(
        stmt.order_by(KnowledgeChunk.id.desc()).limit(80)
    ).all()

    if not chunks:
        return []

    vector = None
    try:
        vector = embed_text(question)
    except Exception as exc:
        print(f"Question embedding warning: {exc}")

    if vector:
        try:
            embedded_stmt = select(KnowledgeChunk).where(
                KnowledgeChunk.session_id == session_id,
                KnowledgeChunk.embedding.is_not(None),
            )

            if comparison_id is not None:
                embedded_stmt = embedded_stmt.where(
                    KnowledgeChunk.product_key == str(comparison_id)
                )

            embedded_stmt = embedded_stmt.order_by(
                KnowledgeChunk.embedding.cosine_distance(vector)
            ).limit(5)

            hits = db.scalars(embedded_stmt).all()
            if hits:
                return hits

        except Exception as exc:
            print(f"Vector retrieval warning; using keyword search: {exc}")

    query_tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", question.lower())
        if len(token) > 2
    }

    scored = []
    for chunk in chunks:
        body = chunk.content.lower()
        score = sum(1 for token in query_tokens if token in body)
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [chunk for score, chunk in scored[:5] if score > 0] or chunks[:3]


def _generate_gemini_answer(prompt: str) -> str:
    """Retry temporary Gemini errors with increasing delays."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    delays = (1, 2, 4)
    last_error = None

    for attempt, delay in enumerate(delays, start=1):
        try:
            response = client.models.generate_content(
                model=settings.gemini_chat_model,
                contents=prompt,
            )

            answer = getattr(response, "text", None)
            if answer and answer.strip():
                return answer.strip()

            raise RuntimeError("Gemini returned an empty answer.")

        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()

            temporary = any(
                marker in error_text
                for marker in (
                    "503",
                    "unavailable",
                    "429",
                    "resource_exhausted",
                    "500",
                    "internal server error",
                    "deadline exceeded",
                    "timed out",
                    "timeout",
                )
            )

            if not temporary or attempt == len(delays):
                break

            print(
                f"Temporary Gemini error on attempt {attempt}; "
                f"retrying in {delay} seconds."
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Gemini could not generate an answer after retries: {last_error}"
    ) from last_error


def answer_question(
    db: Session,
    session_id: str,
    question: str,
    comparison_id: int | None = None,
):
    chunks = _retrieve_chunks(
        db, session_id, question, comparison_id
    )

    if not chunks:
        return (
            "I don't have product information saved for this workspace yet. "
            "Add a product URL or paste its specifications first.",
            [],
        )

    evidence = "\n\n".join(
        f"[Source {i + 1}: "
        f"{chunk.source_url or 'Manually added product notes'} | "
        f"{chunk.topic}]\n{chunk.content}"
        for i, chunk in enumerate(chunks)
    )

    prompt = (
        "You are PriceLens AI, a careful product-documentation assistant. "
        "Answer the user's question using only the evidence below. "
        "Do not invent specifications, warranty details, compatibility, "
        "prices, availability, or claims. If the evidence does not answer "
        "the question, say that the supplied product information does not "
        "specify it. Cite relevant sources using [Source 1] labels. "
        "Keep the answer clear and concise.\n\n"
        f"USER QUESTION:\n{question}\n\n"
        f"RETRIEVED EVIDENCE:\n{evidence}"
    )

    sources = [
        {
            "label": f"Source {i + 1}",
            "url": chunk.source_url or "",
            "topic": chunk.topic,
        }
        for i, chunk in enumerate(chunks)
    ]

    try:
        if settings.gemini_api_key:
            answer = _generate_gemini_answer(prompt)

        elif settings.openai_api_key:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_chat_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Answer only from supplied evidence. Never "
                            "invent product details. State when evidence "
                            "is insufficient and cite [Source N]."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            answer = response.choices[0].message.content or ""

        else:
            answer = (
                "Your product information was retrieved, but no AI "
                "provider is configured. Add GEMINI_API_KEY to "
                "backend/.env to enable generated answers."
            )

    except Exception as exc:
        print(f"Answer generation failed: {exc}")
        answer = (
            "I found relevant product information, but the AI service "
            "is temporarily unavailable. Please try your question again "
            "in a moment. Your saved product information is still available."
        )

    return (
        answer or "I couldn't generate an answer from the retrieved information.",
        sources,
    )
