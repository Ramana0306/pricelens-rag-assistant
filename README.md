# PriceLens AI — Product RAG Assistant

PriceLens AI is a guest-first product knowledge assistant. A user pastes a public product-page URL; the backend extracts accessible page text, splits it into chunks, creates embeddings, stores chunks in PostgreSQL/pgvector, retrieves relevant chunks for each question, and asks an LLM to answer using the retrieved evidence.

**No registration or login is required.** The frontend creates a temporary guest-session ID in browser session storage. Guest data expires based on `SESSION_TTL_MINUTES` (default 60 minutes).

## Features

- New React interface with no login/register flow.
- Product page extraction using HTTPX and BeautifulSoup.
- Manual text entry fallback for pages that block automated reading.
- Text chunking and embedding generation.
- PostgreSQL + pgvector storage and similarity search.
- Gemini chat + embeddings by default; optional OpenAI fallback.
- Grounded answers with source references.
- Per-guest-session data scoping and automatic expired-session cleanup.
- Keyword retrieval fallback when embeddings cannot be generated.

## Project layout

```text
pricelens-ai/
  backend/
    app/
      config.py
      database.py
      main.py
      models.py
      product_service.py
      rag_service.py
      schemas.py
    .env.example
    requirements.txt
  frontend/
    src/
      App.jsx
      lib/api.js
      main.jsx
      styles.css
    .env.example
    index.html
    package.json
    vite.config.js
```

## 1. Database setup

Create a PostgreSQL database with pgvector support. Supabase PostgreSQL is supported.

1. Open your Supabase project.
2. Find the database connection string in **Project Settings → Database**.
3. Copy `backend/.env.example` to `backend/.env`.
4. Put the real database connection string in `DATABASE_URL`. URL-encode special characters in the password (for example, `@` becomes `%40`).
5. The backend tries to enable the `vector` extension and creates tables on startup. If your database role cannot create extensions, enable the `vector` extension from Supabase's Database Extensions page first.

The existing `knowledge_chunks.embedding` column is `vector(1536)`. Gemini embeddings are requested at 1536 dimensions to match it. If you have a pre-existing database from a different project version, back up data before making schema changes.

## 2. Configure the AI provider

Recommended: create a Gemini API key at <https://aistudio.google.com/> and set it in `backend/.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

You can alternatively configure `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, and `OPENAI_EMBEDDING_MODEL`. Gemini is selected when both provider keys are configured.

Do not share `.env` files or commit them to Git. Rotate keys if they are ever exposed.

## 3. Start the backend (Windows PowerShell)

Open PowerShell:

```powershell
cd path\to\pricelens-ai\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set DATABASE_URL and GEMINI_API_KEY
python -m uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks activation, use the terminal command permitted by your machine's execution policy or activate the environment from your IDE. Always run Uvicorn from the `backend` folder because the import path is `app.main:app`.

API docs: <http://127.0.0.1:8000/docs>
Health check: <http://127.0.0.1:8000/api/health>

## 4. Start the frontend

Open a second terminal:

```powershell
cd path\to\pricelens-ai\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open <http://localhost:5173>.

If your backend runs on another address, set `VITE_API_URL` in `frontend/.env` and include the frontend origin in `CORS_ORIGINS` in `backend/.env`.

## 5. Use the app

1. Paste a public product-page URL and select **Build knowledge**.
2. The API attempts to read the page's title, description, metadata, and accessible text.
3. The text is split into chunks; each chunk is saved in PostgreSQL. When an embedding provider is configured, each chunk also gets a vector.
4. Ask a product question in the assistant panel.
5. The backend embeds the question, retrieves relevant chunks from the current product's knowledge base, and asks the LLM to answer from that evidence.
6. Expand the sources beneath an answer to inspect the source URL/topic.

### If a product page blocks extraction

Retailer sites can block automated requests or render product data with JavaScript. If the app reports an extraction error, open **Add text manually instead** and paste the product title, description, specs, or warranty information. That text is chunked and stored the same way.

## API endpoints

- `GET /api/health` — service/config status.
- `POST /api/session` — create/refresh a temporary guest session.
- `POST /api/analyze` — fetch a product URL, extract content, chunk it and save it.
- `POST /api/ingest-text` — save manually supplied product information.
- `POST /api/chat` — retrieve product chunks and generate a grounded answer.
- `POST /api/knowledge` — compatibility endpoint to save a single text chunk.
- `DELETE /api/session` — delete the current guest session and its related data.

## Limitations and safety notes

- The system can only answer from text it successfully extracts or the user supplies. It does not guarantee that a retailer page exposes every specification.
- Product websites may block automated fetching. Manual text entry is the supported fallback.
- Answers can still be wrong; check the cited source for important warranty, compatibility, or safety decisions.
- This starter does not process PDFs or images. Those can be added as separate ingestion paths later.
- Guest session IDs are not user accounts. Treat them as temporary workspace identifiers, not authentication credentials.
- For a public deployment, add rate limiting, stronger SSRF protection, monitoring, and a privacy/data-retention review before accepting arbitrary URLs at scale.
