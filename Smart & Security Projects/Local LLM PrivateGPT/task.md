# Task List — Local LLM PrivateGPT

## Phase 1 — Core Ingestion and RAG

- [ ] **1.1 Project scaffolding**
  - [ ] Create folder structure (`src/`, `data/`, `templates/`, `static/`, `deploy/`, `docs/`, `tests/`)
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.default` with all configuration variables
  - [ ] Create `.gitignore` (exclude `venv/`, `.env`, `data/`, `__pycache__/`)
  - [ ] Create `app.py` entry point with Flask + SocketIO

- [ ] **1.2 Multi-format document loader**
  - [ ] Implement `src/ingestion/loader.py`
  - [ ] PDF extraction via PyMuPDF (fitz) — preserve page numbers
  - [ ] DOCX extraction via python-docx — paragraphs and tables
  - [ ] TXT and Markdown — direct text with section detection
  - [ ] CSV extraction via pandas — row-by-row with column headers
  - [ ] Return structured text with metadata (page numbers, sections)
  - [ ] Validate file type by extension and magic bytes

- [ ] **1.3 Chunking engine**
  - [ ] Implement `src/ingestion/chunker.py`
  - [ ] Token-based splitting with configurable `CHUNK_SIZE` (default 1000)
  - [ ] Overlap of `CHUNK_OVERLAP` tokens (default 200)
  - [ ] Preserve metadata per chunk: document ID, page number, char offset
  - [ ] Handle edge cases: very short documents, empty pages

- [ ] **1.4 Embedding pipeline**
  - [ ] Implement `src/ingestion/embedder.py`
  - [ ] Load `all-MiniLM-L6-v2` via sentence-transformers
  - [ ] Batch embed chunks (384-dimensional vectors)
  - [ ] Store embeddings + metadata in ChromaDB collection
  - [ ] Implement `src/services/vector_store.py` — ChromaDB collection management
  - [ ] Persist ChromaDB to `CHROMA_PERSIST_DIR`

- [ ] **1.5 RAG retriever**
  - [ ] Implement `src/rag/retriever.py`
  - [ ] Embed user query using same embedding model
  - [ ] ChromaDB similarity search: return top-K chunks (`RETRIEVAL_TOP_K`)
  - [ ] Optional re-ranking: score chunks by relevance, reorder
  - [ ] Return ranked chunks with metadata

- [ ] **1.6 LLM generator**
  - [ ] Implement `src/rag/generator.py`
  - [ ] Construct prompt: system instruction + context chunks + user question
  - [ ] Send to Ollama via `ollama` Python client
  - [ ] Stream response tokens back (for WebSocket integration)
  - [ ] Parse and attach source citations from context chunks
  - [ ] Handle Ollama connection errors gracefully

- [ ] **1.7 Database initialization**
  - [ ] Implement `src/services/db.py` — create SQLite tables
  - [ ] Tables: `documents`, `chunks`, `conversations`, `messages`, `settings`

- [ ] **1.8 Unit tests — Phase 1**
  - [ ] Test document loader with sample PDF, DOCX, TXT, CSV
  - [ ] Test chunker with known text → verify chunk sizes and overlap
  - [ ] Test embedder → verify vector dimensions
  - [ ] Test retriever with mock ChromaDB data
  - [ ] Test generator with mock Ollama response

## Phase 2 — Document Management

- [ ] **2.1 Document upload**
  - [ ] Implement upload route in `src/routes/documents.py`
  - [ ] File validation: extension, size (`MAX_FILE_SIZE_MB`), magic bytes
  - [ ] Sanitize filenames (prevent path traversal)
  - [ ] Store original file in `UPLOAD_DIR`
  - [ ] Trigger ingestion pipeline: extract → chunk → embed → store
  - [ ] Update `documents` table with metadata and status

- [ ] **2.2 Document listing**
  - [ ] List all documents with metadata: name, type, size, chunk count, upload date, status
  - [ ] Sort by date, name, or type
  - [ ] Search/filter by filename

- [ ] **2.3 Document deletion**
  - [ ] Delete original file from `UPLOAD_DIR`
  - [ ] Delete all chunks from `chunks` table
  - [ ] Delete all embeddings from ChromaDB collection
  - [ ] Update UI to reflect removal

- [ ] **2.4 Document re-indexing**
  - [ ] Delete existing chunks and embeddings for the document
  - [ ] Re-run ingestion pipeline with current settings
  - [ ] Update `documents.indexed_at` timestamp
  - [ ] Useful when `CHUNK_SIZE` or `CHUNK_OVERLAP` changes

- [ ] **2.5 Deduplication**
  - [ ] Compute SHA-256 checksum on upload
  - [ ] Warn if duplicate file already exists
  - [ ] Toggle: allow or reject duplicates

- [ ] **2.6 Unit tests — Phase 2**
  - [ ] Test upload with valid and invalid files
  - [ ] Test deletion cascade (file + chunks + embeddings)
  - [ ] Test re-indexing produces updated chunks

## Phase 3 — Chat Interface

- [ ] **3.1 Chat page with streaming**
  - [ ] Implement `src/routes/chat.py` — chat page and WebSocket handler
  - [ ] Create `templates/chat.html` — chat interface
  - [ ] Create `static/js/chat.js` — WebSocket client
  - [ ] Stream LLM response tokens as they arrive
  - [ ] Show "thinking" indicator during retrieval phase

- [ ] **3.2 Source citation rendering**
  - [ ] Display citations below each answer: document name, page, passage
  - [ ] Click citation to expand/highlight the full chunk
  - [ ] Toggle: `CITATIONS_ENABLED`

- [ ] **3.3 Conversation memory**
  - [ ] Implement `src/rag/conversation.py`
  - [ ] Track Q&A pairs within a session
  - [ ] Include previous exchanges in the LLM prompt for follow-up context
  - [ ] Configurable memory depth
  - [ ] Toggle: `CONVERSATION_MEMORY_ENABLED`

- [ ] **3.4 Conversation history**
  - [ ] Store conversations and messages in database
  - [ ] Sidebar: list previous conversations
  - [ ] Click to reload a past conversation
  - [ ] New conversation button

- [ ] **3.5 Unit tests — Phase 3**
  - [ ] Test streaming response via WebSocket
  - [ ] Test conversation memory context building
  - [ ] Test citation extraction and formatting

## Phase 4 — Web Dashboard and Auth

- [ ] **4.1 Flask app + auth**
  - [ ] Set up Flask with Jinja2 templates
  - [ ] Implement `src/routes/auth.py` — login, logout, session
  - [ ] bcrypt password hashing
  - [ ] Rate limiting on login (10 attempts / 15 min)
  - [ ] Session expiry (24 hours)

- [ ] **4.2 Layout and navigation**
  - [ ] Create `templates/layout.html` — sidebar with links to all pages
  - [ ] Create `static/css/style.css` — dark theme
  - [ ] Responsive sidebar for mobile
  - [ ] Test: pages render with layout

- [ ] **4.3 Dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Document count, total chunks, total Q&A sessions
  - [ ] Ollama model status (name, size, running)
  - [ ] System info: CPU temp, RAM usage, disk usage
  - [ ] Recent activity feed

- [ ] **4.4 Documents page**
  - [ ] Create `templates/documents.html`
  - [ ] Create `static/js/documents.js`
  - [ ] Upload form with drag-and-drop and progress bar
  - [ ] Document table with metadata columns
  - [ ] Delete and re-index buttons per document
  - [ ] Summarize button (if enabled)

- [ ] **4.5 Settings page**
  - [ ] Create `templates/settings.html`
  - [ ] Password change form
  - [ ] CSV export button (if enabled)
  - [ ] System configuration display
  - [ ] Test: change password, download CSV export

- [ ] **4.6 WebSocket integration**
  - [ ] SocketIO server for streaming LLM responses
  - [ ] SocketIO for ingestion progress updates
  - [ ] SocketIO for model pull progress

## Phase 5 — Advanced Features

- [ ] **5.1 Summarization mode**
  - [ ] Implement `src/rag/summarizer.py`
  - [ ] Iterative summarization: chunk summaries → combined final summary
  - [ ] Configurable summary length
  - [ ] UI: "Summarize" button on documents page
  - [ ] Toggle: `SUMMARIZATION_ENABLED`

- [ ] **5.2 Model management**
  - [ ] Implement `src/services/model_service.py`
  - [ ] List locally available Ollama models
  - [ ] Pull new models (with progress via WebSocket)
  - [ ] Switch active model at runtime
  - [ ] Create `templates/models.html` and `static/js/models.js`
  - [ ] Toggle: `MODEL_MANAGEMENT_ENABLED`

- [ ] **5.3 Document comparison**
  - [ ] Implement `src/routes/compare.py`
  - [ ] Select two documents from library
  - [ ] Retrieve key chunks from both documents
  - [ ] LLM generates structured diff: similarities, differences, contradictions
  - [ ] Create `templates/compare.html` and `static/js/compare.js`
  - [ ] Toggle: `COMPARISON_ENABLED`

- [ ] **5.4 API endpoint**
  - [ ] Implement `src/routes/api.py`
  - [ ] POST /api/ask — question + optional document filter
  - [ ] JSON response with answer + citations
  - [ ] Optional API key auth (`X-API-Key` header)
  - [ ] Toggle: `API_ENABLED`

- [ ] **5.5 CSV export**
  - [ ] Implement `src/services/export_service.py`
  - [ ] Export all Q&A history: timestamp, question, answer, model, citations
  - [ ] Date range filter
  - [ ] Download from settings page
  - [ ] Toggle: `EXPORT_ENABLED`

## Phase 6 — Deployment and Polish

- [ ] **6.1 Deploy script**
  - [ ] Write `deploy/deploy_to_pi.sh`
  - [ ] rsync with correct excludes
  - [ ] Remote venv creation + pip install
  - [ ] Create `.env` from `.env.default` if missing
  - [ ] Test: deploy to Pi, verify app starts

- [ ] **6.2 systemd service**
  - [ ] Create service unit file (documented in README)
  - [ ] Depends on: `ollama.service`, `network-online.target`
  - [ ] Enable + start service
  - [ ] Test: reboot Pi → service auto-starts

- [ ] **6.3 Documentation**
  - [ ] Write `docs/threat_model.md`
  - [ ] Final review of README.md, TSD.md, task.md
  - [ ] Verify all `.env` variables documented

- [ ] **6.4 End-to-end testing**
  - [ ] Upload PDF → verify chunks in ChromaDB
  - [ ] Ask question → verify answer with citations
  - [ ] Conversation follow-up → verify memory context
  - [ ] Delete document → verify cleanup (file + chunks + embeddings)
  - [ ] Model switch → verify new model used
  - [ ] API endpoint → verify JSON response
  - [ ] CSV export → verify download content
  - [ ] Deploy + systemd lifecycle test
