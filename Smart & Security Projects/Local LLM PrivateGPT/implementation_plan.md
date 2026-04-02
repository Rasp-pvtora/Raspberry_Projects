# Implementation Plan — Local LLM PrivateGPT

This document provides a phased, step-by-step implementation guide. Each phase focuses on a specific feature area. Complete all steps in order within each phase before moving to the next.

---

## Phase 1 — Core Ingestion and RAG (Foundation)

**Goal:** Documents are loaded, chunked, embedded, stored in ChromaDB. Questions retrieve relevant chunks and Ollama generates grounded answers.

- [ ] **Step 1.1** — Create project folder structure
  - [ ] Create all directories: `src/ingestion/`, `src/rag/`, `src/routes/`, `src/services/`, `data/`, `templates/`, `static/css/`, `static/js/`, `deploy/`, `docs/`, `tests/`
  - [ ] Create `requirements.txt` with pinned versions
  - [ ] Create `.env.default` with all variables documented
  - [ ] Create `.gitignore`
  - [ ] Verify: `pip install -r requirements.txt` succeeds

- [ ] **Step 1.2** — Implement multi-format document loader
  - [ ] Create `src/ingestion/loader.py`
  - [ ] `DocumentLoader.load(file_path)` → returns `Document(text, metadata)`
  - [ ] PDF: extract text per page via PyMuPDF (fitz). Preserve page numbers.
  - [ ] DOCX: extract paragraphs and tables via python-docx.
  - [ ] TXT / Markdown: read text, detect section headers.
  - [ ] CSV: read via pandas, format rows with column headers as context.
  - [ ] Validate file type by extension and magic bytes.
  - [ ] Test: load sample PDF → verify text and page numbers extracted

- [ ] **Step 1.3** — Implement chunking engine
  - [ ] Create `src/ingestion/chunker.py`
  - [ ] `Chunker.chunk(document)` → returns list of `Chunk(text, metadata)`
  - [ ] Token-based splitting at `CHUNK_SIZE` (default 1000) with `CHUNK_OVERLAP` (default 200)
  - [ ] Each chunk retains: document_id, page_number, char_offset, chunk_index
  - [ ] Handle edge cases: documents shorter than chunk size, empty pages
  - [ ] Test: chunk known text → verify sizes, overlap, and metadata

- [ ] **Step 1.4** — Implement embedding pipeline
  - [ ] Create `src/ingestion/embedder.py`
  - [ ] Load `all-MiniLM-L6-v2` via sentence-transformers
  - [ ] `Embedder.embed(chunks)` → returns list of 384-d vectors
  - [ ] Batch processing for efficiency
  - [ ] Create `src/services/vector_store.py`
  - [ ] `VectorStore.add(chunks, embeddings)` → insert into ChromaDB
  - [ ] `VectorStore.delete(document_id)` → remove document's entries
  - [ ] `VectorStore.search(query_embedding, top_k)` → return ranked chunks
  - [ ] Persist ChromaDB to `CHROMA_PERSIST_DIR`
  - [ ] Test: embed sample chunks → store → search → verify results

- [ ] **Step 1.5** — Implement RAG retriever
  - [ ] Create `src/rag/retriever.py`
  - [ ] `Retriever.retrieve(query, top_k)` → embed query → search ChromaDB → return chunks
  - [ ] Optional re-ranking: score chunks by query relevance, reorder
  - [ ] Check `RAG_ENABLED` and `RERANKING_ENABLED`
  - [ ] Test: query → verify correct chunks retrieved and ranked

- [ ] **Step 1.6** — Implement LLM generator
  - [ ] Create `src/rag/generator.py`
  - [ ] `Generator.generate(query, context_chunks)` → build prompt → call Ollama → stream answer
  - [ ] Prompt template: system instruction + context blocks (with source metadata) + user question
  - [ ] Stream tokens via Ollama API (`stream=True`)
  - [ ] Parse citations from context metadata
  - [ ] Handle Ollama connection errors: return error message, don't crash
  - [ ] Test: mock Ollama → verify prompt construction and citation extraction

- [ ] **Step 1.7** — Implement database
  - [ ] Create `src/services/db.py`
  - [ ] Initialize SQLite at `data/privategpt.db`
  - [ ] Create tables: `documents`, `chunks`, `conversations`, `messages`, `settings`
  - [ ] Test: create tables, insert test rows, query back

- [ ] **Step 1.8** — Create Flask app entry point
  - [ ] Create `app.py` with Flask + SocketIO
  - [ ] Load `.env` with python-dotenv
  - [ ] Initialize database, vector store, embedder, retriever, generator
  - [ ] Register route blueprints
  - [ ] Test: `python app.py` starts without errors

- [ ] **Phase 1 checkpoint:** Upload document → extract text → chunk → embed → store → query → retrieve → generate answer with citations

---

## Phase 2 — Document Management

**Goal:** Full lifecycle management of documents in the library.

- [ ] **Step 2.1** — Implement document upload
  - [ ] Create `src/routes/documents.py` — upload endpoint
  - [ ] Accept multipart file upload
  - [ ] Validate: extension in `ALLOWED_EXTENSIONS`, size ≤ `MAX_FILE_SIZE_MB`, magic bytes
  - [ ] Sanitize filename (werkzeug `secure_filename` + additional path traversal checks)
  - [ ] Save to `UPLOAD_DIR`
  - [ ] Insert record into `documents` table (status: `processing`)
  - [ ] Trigger ingestion: load → chunk → embed → store
  - [ ] Update status to `ready` (or `error` on failure)
  - [ ] Test: upload PDF → verify file stored, chunks in DB, embeddings in ChromaDB

- [ ] **Step 2.2** — Implement document listing
  - [ ] GET /documents → return all documents with metadata
  - [ ] Include: filename, type, size, chunk_count, page_count, status, upload date
  - [ ] Sort by upload date (newest first)
  - [ ] Test: upload 3 docs → verify listing shows all with correct metadata

- [ ] **Step 2.3** — Implement document deletion
  - [ ] DELETE /documents/<id> → cascade delete
  - [ ] Remove original file from `UPLOAD_DIR`
  - [ ] Delete chunks from `chunks` table
  - [ ] Delete embeddings from ChromaDB (by document_id filter)
  - [ ] Test: delete document → verify file gone, chunks gone, embeddings gone

- [ ] **Step 2.4** — Implement re-indexing
  - [ ] POST /documents/<id>/reindex
  - [ ] Delete existing chunks and embeddings
  - [ ] Re-run ingestion pipeline (load → chunk → embed → store)
  - [ ] Update `documents.indexed_at`
  - [ ] Test: change chunk size → re-index → verify new chunk count

- [ ] **Step 2.5** — Implement deduplication
  - [ ] Compute SHA-256 of uploaded file
  - [ ] Check against existing `documents.checksum`
  - [ ] If duplicate: return warning (allow override)
  - [ ] Test: upload same file twice → verify warning

- [ ] **Phase 2 checkpoint:** Upload → store → list → delete → re-index → dedup check

---

## Phase 3 — Chat Interface

**Goal:** Conversational Q&A with streaming responses, citations, and memory.

- [ ] **Step 3.1** — Implement chat backend
  - [ ] Create `src/routes/chat.py` — chat page + WebSocket handler
  - [ ] On message: retrieve chunks → generate answer → stream tokens via SocketIO
  - [ ] Store question and answer in `messages` table
  - [ ] Create/update conversation in `conversations` table
  - [ ] Test: send question via WebSocket → receive streamed answer

- [ ] **Step 3.2** — Implement chat frontend
  - [ ] Create `templates/chat.html` — chat interface
  - [ ] Create `static/js/chat.js` — WebSocket client
  - [ ] Message bubbles (user / assistant)
  - [ ] "Thinking..." indicator during retrieval
  - [ ] Token-by-token rendering of streamed response
  - [ ] Test: type question → see streaming answer in browser

- [ ] **Step 3.3** — Implement source citations
  - [ ] Render citations below each answer
  - [ ] Display: document name, page number, highlighted passage
  - [ ] Click to expand full chunk text
  - [ ] Check `CITATIONS_ENABLED`
  - [ ] Test: answer includes citations → click expands passage

- [ ] **Step 3.4** — Implement conversation memory
  - [ ] Create `src/rag/conversation.py`
  - [ ] `ConversationMemory.add(question, answer)` — store exchange
  - [ ] `ConversationMemory.get_context()` — return previous exchanges for prompt
  - [ ] Include in LLM prompt as conversation history
  - [ ] Check `CONVERSATION_MEMORY_ENABLED`
  - [ ] Test: ask follow-up question → verify previous context included in prompt

- [ ] **Step 3.5** — Implement conversation history
  - [ ] Sidebar: list previous conversations (title, date)
  - [ ] Click to load past conversation messages
  - [ ] New conversation button
  - [ ] Auto-generate title from first question
  - [ ] Test: create 2 conversations → switch between them

- [ ] **Phase 3 checkpoint:** Chat → streaming answer → citations → follow-up with memory → history

---

## Phase 4 — Web Dashboard and Auth

**Goal:** Complete web interface with authentication, dark theme, and all pages.

- [ ] **Step 4.1** — Authentication
  - [ ] Create `src/routes/auth.py` — login(), logout()
  - [ ] bcrypt hash verification
  - [ ] Rate limiting: track IP attempts, block after 10 in 15 min
  - [ ] Session cookie with `SESSION_SECRET` (HttpOnly, SameSite)
  - [ ] Session expiry: 24 hours
  - [ ] Create `templates/login.html`
  - [ ] Test: login with correct/incorrect credentials, rate limit test

- [ ] **Step 4.2** — Layout and navigation
  - [ ] Create `templates/layout.html` — sidebar with links to all pages
  - [ ] Create `static/css/style.css` — dark theme
  - [ ] Pages: Dashboard, Chat, Documents, Compare, Models, Settings
  - [ ] Responsive sidebar for mobile
  - [ ] Test: pages render with layout

- [ ] **Step 4.3** — Dashboard page
  - [ ] Create `templates/dashboard.html`
  - [ ] Implement `src/routes/dashboard.py`
  - [ ] Stats: document count, total chunks, total conversations, total messages
  - [ ] Ollama status: model name, model size, running state
  - [ ] System info: CPU temp, RAM usage, disk usage
  - [ ] Recent activity: last 10 Q&A exchanges
  - [ ] Test: dashboard shows correct stats

- [ ] **Step 4.4** — Documents page
  - [ ] Create `templates/documents.html`
  - [ ] Create `static/js/documents.js`
  - [ ] Upload form: drag-and-drop area + file picker + progress bar
  - [ ] Document table: name, type, size, chunks, status, date, actions
  - [ ] Actions: delete, re-index, summarize (if enabled)
  - [ ] Test: upload, list, delete, re-index from UI

- [ ] **Step 4.5** — Settings page
  - [ ] Create `templates/settings.html`
  - [ ] Password change form
  - [ ] CSV export button (download Q&A history)
  - [ ] Display current configuration (read-only)
  - [ ] System info panel
  - [ ] Test: change password, download export

- [ ] **Phase 4 checkpoint:** Login → dashboard → chat → documents → settings — all functional

---

## Phase 5 — Advanced Features

**Goal:** Summarization, model management, comparison, API, export.

- [ ] **Step 5.1** — Implement summarization
  - [ ] Create `src/rag/summarizer.py`
  - [ ] `Summarizer.summarize(document_id)` → retrieve all chunks → iterative summarization
  - [ ] Strategy: summarize each chunk → combine summaries → final summary
  - [ ] Stream progress via SocketIO
  - [ ] Add "Summarize" button to documents page
  - [ ] Check `SUMMARIZATION_ENABLED`
  - [ ] Test: summarize a multi-page PDF → verify coherent summary

- [ ] **Step 5.2** — Implement model management
  - [ ] Create `src/services/model_service.py`
  - [ ] `list_models()` → query Ollama API for local models
  - [ ] `pull_model(name)` → download from registry with progress
  - [ ] `switch_model(name)` → update active model (no restart needed)
  - [ ] Create `templates/models.html` and `static/js/models.js`
  - [ ] Create `src/routes/models.py`
  - [ ] Check `MODEL_MANAGEMENT_ENABLED`
  - [ ] Test: list models, pull a small model, switch models

- [ ] **Step 5.3** — Implement document comparison
  - [ ] Create `src/routes/compare.py`
  - [ ] Create `templates/compare.html` and `static/js/compare.js`
  - [ ] Select two documents from dropdown
  - [ ] Retrieve key chunks from both
  - [ ] LLM generates structured comparison: similarities, differences, contradictions
  - [ ] Stream comparison result
  - [ ] Check `COMPARISON_ENABLED`
  - [ ] Test: compare two documents → verify structured output

- [ ] **Step 5.4** — Implement API endpoint
  - [ ] Create `src/routes/api.py`
  - [ ] POST /api/ask — JSON body: `{ question, document_ids?, model? }`
  - [ ] JSON response: `{ answer, citations, model, generation_time }`
  - [ ] API key auth: check `X-API-Key` header against `API_KEY` env var
  - [ ] Rate limiting for API requests
  - [ ] Check `API_ENABLED`
  - [ ] Test: curl POST → verify JSON response with citations

- [ ] **Step 5.5** — Implement CSV export
  - [ ] Create `src/services/export_service.py`
  - [ ] `export_qa_history(start_date, end_date)` → generate CSV
  - [ ] Columns: timestamp, question, answer, model, source documents, citations
  - [ ] Download endpoint on settings page
  - [ ] Check `EXPORT_ENABLED`
  - [ ] Test: export → verify CSV content matches database

- [ ] **Phase 5 checkpoint:** Summarize → model switch → compare → API → export — all functional

---

## Phase 6 — Deployment and Polish

**Goal:** Production-ready deployment, documentation, end-to-end testing.

- [ ] **Step 6.1** — Deploy script
  - [ ] Write `deploy/deploy_to_pi.sh`
  - [ ] rsync with correct excludes (`venv/`, `.env`, `.git/`, `data/`)
  - [ ] Remote venv creation + pip install
  - [ ] Check Ollama is installed on Pi (prompt to install if not)
  - [ ] Create `.env` from `.env.default` if missing
  - [ ] Test: deploy to Pi, verify app starts

- [ ] **Step 6.2** — systemd service
  - [ ] Create service unit file (documented in README)
  - [ ] `After=network-online.target ollama.service`
  - [ ] Enable + start service
  - [ ] Test: reboot Pi → service auto-starts → dashboard accessible

- [ ] **Step 6.3** — Documentation
  - [ ] Write `docs/threat_model.md`
  - [ ] Final review of README.md, TSD.md, task.md
  - [ ] Verify all `.env` variables documented
  - [ ] Verify all API endpoints documented

- [ ] **Step 6.4** — End-to-end testing
  - [ ] Upload PDF → verify chunks and embeddings created
  - [ ] Ask question about PDF → verify grounded answer with citations
  - [ ] Ask follow-up → verify conversation memory includes context
  - [ ] Delete document → verify cascade cleanup
  - [ ] Re-index document → verify updated chunks
  - [ ] Summarize document → verify coherent summary
  - [ ] Switch model → verify new model used for next answer
  - [ ] Compare two documents → verify structured diff
  - [ ] POST /api/ask → verify JSON response
  - [ ] CSV export → verify correct data
  - [ ] Deploy + systemd lifecycle test

- [ ] **Phase 6 checkpoint:** App deployed on Pi, auto-starts, all features working, docs complete
