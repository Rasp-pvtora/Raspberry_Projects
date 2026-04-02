# TSD — Local LLM PrivateGPT

## 1 · Scope

Build a self-hosted, fully offline document Q&A system for Raspberry Pi. Users upload documents (PDF, DOCX, TXT, CSV, Markdown), which are chunked, embedded, and stored in ChromaDB. Questions are answered via Ollama (Llama 3 / Phi-3 Q4) using RAG with source citations. Web dashboard provides document management, conversational chat, model management, document comparison, summarization, and Q&A history export. All processing happens locally — no data ever leaves the Pi.

### In scope

| Area | Details |
|---|---|
| **RAG pipeline** | 1000-token chunks, 200 overlap, all-MiniLM-L6-v2 embeddings, ChromaDB vector store, similarity search, optional re-ranking |
| **Document ingestion** | PDF (PyMuPDF), DOCX (python-docx), TXT, CSV (pandas), Markdown |
| **LLM inference** | Ollama with Llama 3 8B Q4, Phi-3 Mini Q4, runtime model switching |
| **Conversation memory** | Session-scoped multi-turn Q&A with context carryover |
| **Source citations** | Document name + page number + highlighted passage per answer |
| **Document library** | Upload, view metadata, delete, re-index from dashboard |
| **Summarization** | Iterative chunk-based document summarization |
| **Model management** | List, pull, switch, view info from dashboard |
| **Document comparison** | AI-generated diff analysis of two documents |
| **API endpoint** | POST /api/ask with optional API key auth |
| **Q&A export** | CSV export of all questions, answers, citations |
| **Web dashboard** | Flask + SocketIO, dark theme, streaming responses, real-time progress |
| **Authentication** | Session-based with bcrypt, rate limiting, 24h expiry |
| **Mock mode** | Full development on laptop with local Ollama |

### Out of scope

| Area | Reason |
|---|---|
| OCR for scanned PDFs | Tesseract adds significant complexity; documented as upgrade path |
| Multi-user isolation | Single-user system; multi-user requires auth refactor |
| Cloud LLM fallback | Defeats the privacy-first design; strictly offline |
| Fine-tuning on-device | Requires GPU; export data for external fine-tuning instead |
| Image/audio document understanding | Requires multimodal models not yet optimized for Pi |

---

## 2 · MVP features

### 2.1 — Document ingestion pipeline

**Priority: P0**

- Accept file uploads via web form (drag-and-drop + file picker).
- Extract text from PDF (PyMuPDF/fitz), DOCX (python-docx), TXT, CSV (pandas), Markdown.
- Preserve page numbers (PDF) and section headers for citation metadata.
- Store original file in `UPLOAD_DIR`.
- Toggle: `INGESTION_ENABLED=true/false` in `.env`.

### 2.2 — Chunking engine

**Priority: P0**

- Split extracted text into chunks of `CHUNK_SIZE` tokens (default 1000).
- Overlap of `CHUNK_OVERLAP` tokens (default 200) between consecutive chunks.
- Each chunk retains metadata: document ID, page number, character offset, section title.
- Re-chunking available per document (for config changes).

### 2.3 — Embedding and vector storage

**Priority: P0**

- Compute embeddings using `all-MiniLM-L6-v2` via sentence-transformers (384-d vectors).
- Store embeddings + metadata in ChromaDB collection.
- ChromaDB persisted to `CHROMA_PERSIST_DIR`.
- Support delete (remove document's chunks) and re-index (delete + re-embed).

### 2.4 — RAG retrieval and generation

**Priority: P0**

- Embed user query using the same embedding model.
- ChromaDB similarity search: retrieve `RETRIEVAL_TOP_K` chunks (default 5).
- Optional re-ranking: score and reorder chunks by query relevance.
- Construct prompt: system instruction + retrieved context chunks + user question.
- Send to Ollama, stream response tokens back to client.
- Toggle: `RAG_ENABLED=true/false` in `.env`.

### 2.5 — Web dashboard

**Priority: P0**

**Database schema:**

**Table: `documents`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `filename` | TEXT | Original filename |
| `file_type` | TEXT | Extension: `pdf`, `docx`, `txt`, `csv`, `md` |
| `file_size` | INTEGER | File size in bytes |
| `file_path` | TEXT | Path to stored file in uploads/ |
| `chunk_count` | INTEGER | Number of chunks generated |
| `page_count` | INTEGER | Number of pages (PDF) or sections |
| `checksum` | TEXT | SHA-256 hash for deduplication |
| `status` | TEXT | `processing`, `ready`, `error` |
| `uploaded_at` | DATETIME | Upload timestamp |
| `indexed_at` | DATETIME | Last embedding timestamp |

**Table: `chunks`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `document_id` | INTEGER FK | References documents.id |
| `chunk_index` | INTEGER | Order within document |
| `content` | TEXT | Chunk text content |
| `page_number` | INTEGER | Source page (PDF) or section index |
| `char_offset` | INTEGER | Character offset in original text |
| `token_count` | INTEGER | Number of tokens in chunk |
| `chroma_id` | TEXT | Corresponding ChromaDB entry ID |
| `created_at` | DATETIME | Chunk creation timestamp |

**Table: `conversations`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | TEXT | Session identifier |
| `title` | TEXT | Auto-generated conversation title |
| `model_used` | TEXT | Ollama model name |
| `created_at` | DATETIME | Conversation start |
| `updated_at` | DATETIME | Last message timestamp |

**Table: `messages`**

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `conversation_id` | INTEGER FK | References conversations.id |
| `role` | TEXT | `user` or `assistant` |
| `content` | TEXT | Message text |
| `citations` | TEXT | JSON array of citation objects |
| `chunks_used` | TEXT | JSON array of chunk IDs used for retrieval |
| `model_used` | TEXT | Ollama model for this response |
| `generation_time` | REAL | Seconds to generate response |
| `token_count` | INTEGER | Tokens in response |
| `created_at` | DATETIME | Message timestamp |

**Table: `settings`**

| Column | Type | Description |
|---|---|---|
| `key` | TEXT PK | Setting name |
| `value` | TEXT | Setting value (JSON) |
| `updated_at` | DATETIME | Last update |

### 2.6 — Authentication

**Priority: P0**

- bcrypt password hashing.
- Rate limiting: 10 attempts / 15 min.
- Session cookies (HttpOnly, SameSite).
- Session expiry: 24 hours.

### 2.7 — Deploy script

**Priority: P0**

- `deploy/deploy_to_pi.sh`: rsync + venv + pip install.
- systemd service unit documented in README.

---

## 3 · Nice-to-have features

### 3.1 — Summarization mode

**Requires:** Document with sufficient text content.

- Iterative summarization: chunk summaries → combined final summary.
- Configurable summary length.
- Toggle: `SUMMARIZATION_ENABLED=true`.

### 3.2 — Model management

**Requires:** Ollama installed and running.

- List locally available models.
- Pull new models from Ollama registry.
- Switch active model at runtime.
- Toggle: `MODEL_MANAGEMENT_ENABLED=true`.

### 3.3 — Document comparison

**Requires:** At least two documents in library.

- Select two documents from the library.
- LLM generates structured diff analysis.
- Toggle: `COMPARISON_ENABLED=true`.

### 3.4 — API endpoint

**Requires:** Network access to the Pi.

- POST /api/ask with JSON body.
- Optional API key authentication.
- Toggle: `API_ENABLED=true`.

### 3.5 — CSV export

**Requires:** At least one Q&A conversation.

- Export all Q&A history as CSV.
- Date range filter.
- Toggle: `EXPORT_ENABLED=true`.

---

## 4 · High-level architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL LLM PRIVATEGPT                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  INGESTION LAYER                         │  │
│  │                                                          │  │
│  │  PDF (PyMuPDF) ─┐                                       │  │
│  │  DOCX           ├→ Text → Chunker → Embedder → ChromaDB │  │
│  │  TXT / MD       │    (1000 tok)   (MiniLM-L6)           │  │
│  │  CSV (pandas)  ─┘    (200 overlap)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  RAG LAYER                               │  │
│  │                                                          │  │
│  │  Query → Embed → ChromaDB search (top-K)                │  │
│  │       → Re-rank → Prompt build → Ollama LLM             │  │
│  │       → Answer + citations                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  SERVICE LAYER                           │  │
│  │                                                          │  │
│  │  SQLite │ ChromaDB │ Ollama │ Export │ System Monitor    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  WEB LAYER                               │  │
│  │                                                          │  │
│  │  Flask + SocketIO │ Jinja2 │ Chart.js │ Dark theme       │  │
│  │  Chat │ Documents │ Compare │ Models │ Settings          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5 · Security / Threat model

| # | Threat | Mitigation |
|---|---|---|
| T1 | Credential exposure | `.env` in `.gitignore`, `chmod 600` |
| T2 | Brute-force login | Rate limiting: 10/15 min |
| T3 | Session hijacking | Strong `SESSION_SECRET`, HttpOnly, SameSite cookies |
| T4 | XSS | Jinja2 auto-escaping |
| T5 | SQL injection | Parameterized queries |
| T6 | Path traversal (upload) | Sanitize filenames, store in `UPLOAD_DIR` only, validate extensions |
| T7 | Malicious file upload | Validate file type by extension and magic bytes, size limit |
| T8 | API abuse | Rate limiting, optional API key, input validation |
| T9 | Data exfiltration | Fully offline — no external network calls |
| T10 | Prompt injection | System prompt hardening, input sanitization, context-only grounding |
| T11 | Disk exhaustion | `MAX_FILE_SIZE_MB` limit, disk space check before upload |

---

## 6 · Suggested tech stack

### Backend

| Component | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best ML/NLP ecosystem |
| Web framework | Flask 3.1 + SocketIO | Lightweight, real-time streaming |
| LLM inference | Ollama (Llama 3 / Phi-3 Q4) | Local, offline, optimized for ARM |
| Vector database | ChromaDB 0.5 | Embedded, zero-config, Python-native |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Small, fast, good quality |
| PDF extraction | PyMuPDF (fitz) 1.24 | Fast, accurate, page-aware |
| DOCX extraction | python-docx 1.1 | Standard DOCX library |
| CSV processing | pandas 2.2 | Robust CSV handling |
| Database | SQLite | Zero-config file-based |
| Reports | ReportLab 4.2 | PDF generation |
| Auth | bcrypt + Flask sessions | Password hashing |

### Frontend

| Component | Technology |
|---|---|
| Templates | Jinja2 |
| Charts | Chart.js 4 (CDN) |
| WebSocket | Socket.IO client (CDN) |
| Styling | Custom CSS (dark theme) |

---

## 7 · Development phases

### Phase 1 — Core ingestion and RAG

| # | Task | Priority |
|---|---|---|
| 1.1 | Project scaffolding | P0 |
| 1.2 | Multi-format document loader (PDF, DOCX, TXT, CSV, MD) | P0 |
| 1.3 | Chunking engine (1000 tokens, 200 overlap) | P0 |
| 1.4 | Embedding pipeline (all-MiniLM-L6-v2 → ChromaDB) | P0 |
| 1.5 | RAG retriever (similarity search + re-ranking) | P0 |
| 1.6 | Ollama LLM generator (prompt construction + streaming) | P0 |
| 1.7 | Database initialization | P0 |
| 1.8 | Unit tests | P1 |

### Phase 2 — Document management

| # | Task | Priority |
|---|---|---|
| 2.1 | Document upload with progress | P0 |
| 2.2 | Document listing with metadata | P0 |
| 2.3 | Document deletion (files + chunks + embeddings) | P0 |
| 2.4 | Document re-indexing | P0 |
| 2.5 | Deduplication (SHA-256 checksum) | P1 |
| 2.6 | Unit tests | P1 |

### Phase 3 — Chat interface

| # | Task | Priority |
|---|---|---|
| 3.1 | Chat page with streaming WebSocket responses | P0 |
| 3.2 | Source citation rendering | P0 |
| 3.3 | Conversation memory (session-scoped) | P0 |
| 3.4 | Conversation history sidebar | P1 |
| 3.5 | Unit tests | P1 |

### Phase 4 — Web dashboard and auth

| # | Task | Priority |
|---|---|---|
| 4.1 | Flask app + auth + layout (dark theme) | P0 |
| 4.2 | Dashboard: document stats, Q&A stats, system info | P0 |
| 4.3 | Documents page: upload, list, delete, re-index | P0 |
| 4.4 | Settings page: config, password change, export | P0 |
| 4.5 | WebSocket streaming integration | P0 |

### Phase 5 — Advanced features

| # | Task | Priority |
|---|---|---|
| 5.1 | Summarization mode | P1 |
| 5.2 | Model management (list, pull, switch) | P1 |
| 5.3 | Document comparison mode | P1 |
| 5.4 | API endpoint (POST /api/ask) | P1 |
| 5.5 | CSV export of Q&A history | P1 |

### Phase 6 — Deployment and polish

| # | Task | Priority |
|---|---|---|
| 6.1 | Deploy script | P0 |
| 6.2 | systemd service | P1 |
| 6.3 | Threat model document | P1 |
| 6.4 | End-to-end testing | P1 |

---

## 8 · `.env.default` reference

```ini
# ─── General ────────────────────────────────────────────────────
PORT=5000
HOST=0.0.0.0
SESSION_SECRET=CHANGE_ME_TO_A_RANDOM_STRING
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# ─── LLM Settings ──────────────────────────────────────────────
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:8b-q4_0
OLLAMA_TEMPERATURE=0.3
OLLAMA_MAX_TOKENS=512
OLLAMA_CONTEXT_WINDOW=4096
MODEL_MANAGEMENT_ENABLED=true

# ─── RAG Pipeline ──────────────────────────────────────────────
RAG_ENABLED=true
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./data/chroma
RETRIEVAL_TOP_K=5
RERANKING_ENABLED=true

# ─── Document Ingestion ────────────────────────────────────────
INGESTION_ENABLED=true
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,txt,csv,md

# ─── Features ──────────────────────────────────────────────────
CONVERSATION_MEMORY_ENABLED=true
CITATIONS_ENABLED=true
SUMMARIZATION_ENABLED=true
COMPARISON_ENABLED=true
API_ENABLED=true
API_KEY=
EXPORT_ENABLED=true

# ─── Alerts ────────────────────────────────────────────────────
ALERT_WEBHOOK_ENABLED=false
ALERT_WEBHOOK_URL=
```

---

## 9 · API reference

### POST /api/ask

**Request:**

```json
{
  "question": "What are the key findings in the Q3 report?",
  "document_ids": [1, 3],
  "model": "llama3:8b-q4_0"
}
```

- `question` (required): The question to ask.
- `document_ids` (optional): Filter retrieval to specific documents. Omit for all documents.
- `model` (optional): Override the default model for this request.

**Response:**

```json
{
  "answer": "The Q3 report identifies three key findings...",
  "citations": [
    {
      "document": "Q3_Report_2025.pdf",
      "page": 12,
      "passage": "Revenue increased by 15% compared to Q2...",
      "chunk_id": "abc123"
    }
  ],
  "model": "llama3:8b-q4_0",
  "generation_time": 4.2
}
```

**Authentication:** Include `X-API-Key` header if `API_KEY` is set in `.env`.

**Error responses:**

| Status | Reason |
|---|---|
| 400 | Missing `question` field |
| 401 | Invalid or missing API key |
| 503 | Ollama not running or model not loaded |
