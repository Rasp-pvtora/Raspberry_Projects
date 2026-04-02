# Local LLM PrivateGPT

A self-hosted, fully offline document Q&A system for Raspberry Pi. Upload PDFs, DOCX, TXT, CSV, and Markdown files → chunk and embed into a ChromaDB vector database → ask questions → Ollama (Llama 3 / Phi-3 Q4) retrieves relevant chunks via RAG and generates grounded answers with source citations. No data ever leaves the Pi. Includes a Flask + SocketIO web dashboard for document management, conversational Q&A chat, model management, document comparison, summarization, and analytics.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Libraries and dependencies](#libraries-and-dependencies)
5. [Quickstart — Laptop (development)](#quickstart--laptop-development)
6. [Environment configuration (.env)](#environment-configuration-env)
7. [System overview — RAG pipeline](#system-overview--rag-pipeline)
8. [Feature — Multi-format document ingestion](#feature--multi-format-document-ingestion)
9. [Feature — Chunking and embedding](#feature--chunking-and-embedding)
10. [Feature — RAG question answering](#feature--rag-question-answering)
11. [Feature — Conversation memory](#feature--conversation-memory)
12. [Feature — Source citations](#feature--source-citations)
13. [Feature — Document library management](#feature--document-library-management)
14. [Feature — Summarization mode](#feature--summarization-mode)
15. [Feature — Model management](#feature--model-management)
16. [Feature — Document comparison mode](#feature--document-comparison-mode)
17. [Feature — API endpoint](#feature--api-endpoint)
18. [Feature — CSV export of Q&A history](#feature--csv-export-of-qa-history)
19. [Feature — Web dashboard](#feature--web-dashboard)
20. [Authentication](#authentication)
21. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
22. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
23. [Security notes](#security-notes)
24. [Troubleshooting](#troubleshooting)
25. [Where to next](#where-to-next)

---

## Project structure

```
.
├── app.py                     ← Python entry point (Flask + SocketIO)
├── requirements.txt           ← Python dependencies
├── .env.default               ← Environment variable template (copy to .env)
├── .gitignore                 ← Git ignore rules
├── src/
│   ├── ingestion/
│   │   ├── loader.py          ← Multi-format document loader (PDF, DOCX, TXT, CSV, MD)
│   │   ├── chunker.py         ← Token-based text chunking with overlap
│   │   └── embedder.py        ← Sentence-transformer embedding generation
│   ├── rag/
│   │   ├── retriever.py       ← ChromaDB similarity search + re-ranking
│   │   ├── generator.py       ← Ollama LLM prompt construction + response
│   │   ├── conversation.py    ← Session-based conversation memory
│   │   └── summarizer.py      ← Document summarization pipeline
│   ├── routes/
│   │   ├── auth.py            ← Login / logout routes
│   │   ├── dashboard.py       ← Dashboard API and pages
│   │   ├── documents.py       ← Document upload, list, delete, re-index
│   │   ├── chat.py            ← Q&A chat API and WebSocket
│   │   ├── models.py          ← Model management API
│   │   ├── compare.py         ← Document comparison API
│   │   ├── api.py             ← Public REST API (POST /api/ask)
│   │   └── settings.py        ← Settings API
│   └── services/
│       ├── db.py              ← SQLite database initialization
│       ├── vector_store.py    ← ChromaDB collection management
│       ├── model_service.py   ← Ollama model listing, pulling, switching
│       ├── export_service.py  ← CSV export of Q&A history
│       ├── alert_service.py   ← Optional alert channels (webhook)
│       └── system_service.py  ← System info (temp, memory, disk)
├── data/
│   ├── privategpt.db          ← SQLite database
│   ├── uploads/               ← Uploaded source documents
│   └── chroma/                ← ChromaDB vector database files
├── templates/                 ← Jinja2 HTML templates
│   ├── layout.html            ← Base layout with sidebar navigation
│   ├── login.html             ← Login page
│   ├── dashboard.html         ← Overview: document count, Q&A stats, system info
│   ├── chat.html              ← Q&A chat interface with source citations
│   ├── documents.html         ← Document library: upload, list, delete, re-index
│   ├── compare.html           ← Document comparison interface
│   ├── models.html            ← Model management: switch, pull, status
│   └── settings.html          ← Configuration and export
├── static/
│   ├── css/style.css          ← Dark theme stylesheet
│   └── js/
│       ├── main.js            ← Shared utilities
│       ├── chat.js            ← WebSocket chat client + citation rendering
│       ├── documents.js       ← Upload, delete, re-index logic
│       ├── compare.js         ← Comparison interface logic
│       └── models.js          ← Model management logic
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── tests/
├── README.md
├── TSD.md
├── task.md
└── implementation_plan.md
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (8 GB) / Pi 5 | Yes | 8 GB RAM required for LLM inference |
| microSD card (32 GB+) | Yes | For OS, models, and vector database |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet or WiFi | Yes | For dashboard access |

### Optional hardware

| Component | Required | Notes |
|---|---|---|
| USB 3.0 SSD (128 GB+) | Optional | Faster I/O for large document collections and model storage |
| Active cooler / heatsink | Recommended | LLM inference causes sustained high CPU/GPU load |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| USB 3.0 SSD (128 GB) | $20 – $30 | Faster model loading and vector DB I/O |
| **Total (minimum)** | **$0** | No extra hardware needed beyond the Pi |
| **Total (recommended)** | **~$20 – $30** | With USB SSD for performance |

> **Note:** The Raspberry Pi, microSD card, and power supply are not included above.

---

## Libraries and dependencies

### Python dependencies

| Library | Version | Purpose |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | ^3.1.0 | Web framework and API routing |
| [Flask-SocketIO](https://flask-socketio.readthedocs.io/) | ^5.4.0 | WebSocket for real-time chat streaming |
| [Jinja2](https://jinja.palletsprojects.com/) | ^3.1.4 | Server-side HTML templating |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ^1.0.1 | Load environment variables from `.env` |
| [ollama](https://pypi.org/project/ollama/) | ^0.4.0 | Python client for Ollama LLM API |
| [chromadb](https://www.trychroma.com/) | ^0.5.0 | Vector database for document embeddings |
| [sentence-transformers](https://www.sbert.net/) | ^3.0.0 | all-MiniLM-L6-v2 embedding model |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | ^1.24.0 | PDF text extraction (fitz) |
| [python-docx](https://python-docx.readthedocs.io/) | ^1.1.0 | DOCX text extraction |
| [pandas](https://pandas.pydata.org/) | ^2.2.0 | CSV parsing and Q&A history export |
| [numpy](https://numpy.org/) | ^1.26.0 | Numerical operations |
| [bcrypt](https://pypi.org/project/bcrypt/) | ^4.2.0 | Password hashing |
| [reportlab](https://pypi.org/project/reportlab/) | ^4.2.0 | PDF report generation |
| [requests](https://requests.readthedocs.io/) | ^2.32.0 | Webhook alerts (optional) |

### Dev dependencies

| Library | Version | Purpose |
|---|---|---|
| [pytest](https://docs.pytest.org/) | ^8.3.0 | Testing framework |

### System packages (Pi)

| Package | Purpose |
|---|---|
| `ollama` | Local LLM inference server (install via `curl -fsSL https://ollama.com/install.sh \| sh`) |
| `Python 3.11+` | Python runtime |

---

## Quickstart — Laptop (development)

**1. Clone and navigate**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Local LLM PrivateGPT"
```

**2. Create `.env` from template**

```bash
cp .env.default .env    # Linux/macOS
copy .env.default .env  # Windows
```

**3. Virtual environment and dependencies**

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

**4. Install Ollama and pull a model**

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (choose one)
ollama pull llama3:8b-q4_0      # Llama 3 8B quantized (recommended for Pi 5)
ollama pull phi3:mini-q4_0      # Phi-3 Mini quantized (faster, lighter)
```

**5. Start the server**

```bash
python app.py
```

**6. Open dashboard** → `http://localhost:5000`

> On a laptop, all features work identically. Ollama must be running locally.

---

## Environment configuration (.env)

Copy `.env.default` to `.env`. **Never commit `.env` to git.**

### General

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Web server port |
| `HOST` | `0.0.0.0` | Listen address |
| `SESSION_SECRET` | `CHANGE_ME...` | Session encryption key |
| `ADMIN_USERNAME` | `admin` | Dashboard login |
| `ADMIN_PASSWORD` | `changeme` | Dashboard password |

### LLM settings

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3:8b-q4_0` | Default LLM model for generation |
| `OLLAMA_TEMPERATURE` | `0.3` | Generation temperature (0.0–1.0) |
| `OLLAMA_MAX_TOKENS` | `512` | Max tokens per response |
| `OLLAMA_CONTEXT_WINDOW` | `4096` | Model context window size |
| `MODEL_MANAGEMENT_ENABLED` | `true` | Enable model switching from dashboard |

### RAG pipeline

| Variable | Default | Description |
|---|---|---|
| `RAG_ENABLED` | `true` | Enable RAG pipeline |
| `CHUNK_SIZE` | `1000` | Chunk size in tokens |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model for embeddings |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage directory |
| `RETRIEVAL_TOP_K` | `5` | Number of chunks to retrieve per query |
| `RERANKING_ENABLED` | `true` | Enable re-ranking of retrieved chunks |

### Document ingestion

| Variable | Default | Description |
|---|---|---|
| `INGESTION_ENABLED` | `true` | Enable document upload and ingestion |
| `UPLOAD_DIR` | `./data/uploads` | Uploaded document storage |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |
| `ALLOWED_EXTENSIONS` | `pdf,docx,txt,csv,md` | Accepted file types |

### Features

| Variable | Default | Description |
|---|---|---|
| `CONVERSATION_MEMORY_ENABLED` | `true` | Enable conversation memory within session |
| `CITATIONS_ENABLED` | `true` | Show source citations with answers |
| `SUMMARIZATION_ENABLED` | `true` | Enable document summarization mode |
| `COMPARISON_ENABLED` | `true` | Enable document comparison mode |
| `API_ENABLED` | `true` | Enable POST /api/ask endpoint |
| `API_KEY` | `` | API key for /api/ask (empty = no auth) |
| `EXPORT_ENABLED` | `true` | Enable CSV export of Q&A history |

### Alerts

| Variable | Default | Description |
|---|---|---|
| `ALERT_WEBHOOK_ENABLED` | `false` | Enable webhook alerts |
| `ALERT_WEBHOOK_URL` | `` | Webhook endpoint URL |

---

## System overview — RAG pipeline

This system implements **Retrieval-Augmented Generation (RAG)** entirely on-device:

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL LLM PRIVATEGPT                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  DOCUMENT INGESTION                      │  │
│  │                                                          │  │
│  │  Upload (PDF/DOCX/TXT/CSV/MD)                           │  │
│  │  → Extract text (PyMuPDF / python-docx / pandas)        │  │
│  │  → Chunk (1000 tokens, 200 overlap)                     │  │
│  │  → Embed (all-MiniLM-L6-v2)                             │  │
│  │  → Store in ChromaDB                                     │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │                    RAG PIPELINE                           │  │
│  │                                                          │  │
│  │  User question                                           │  │
│  │  → Embed query (all-MiniLM-L6-v2)                       │  │
│  │  → Retrieve top-K chunks (ChromaDB similarity search)    │  │
│  │  → Re-rank chunks (optional)                             │  │
│  │  → Build prompt: system + context chunks + question      │  │
│  │  → Generate answer (Ollama: Llama 3 / Phi-3)            │  │
│  │  → Attach source citations (doc name + page + passage)   │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │                  SHARED SERVICES                          │  │
│  │                                                          │  │
│  │  SQLite DB │ ChromaDB │ Ollama │ Export │ System Monitor  │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │                  WEB DASHBOARD                            │  │
│  │  Flask + SocketIO + Chart.js                              │  │
│  │  Chat │ Documents │ Models │ Compare │ Settings           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Processing pipeline:**

```
Document → Extract text → Chunk → Embed → ChromaDB
Question → Embed → Retrieve top-K → Re-rank → LLM prompt → Answer + citations
```

**Key design principles:**
- **Fully offline.** No data leaves the device. Ollama runs locally.
- **Privacy first.** All documents, embeddings, and conversations stay on the Pi.
- **Modular.** Each pipeline stage is independently configurable via `.env`.

---

## Feature — Multi-format document ingestion

Upload and process documents in multiple formats.

- **PDF:** Text extraction via PyMuPDF (fitz). Preserves page numbers for citations.
- **DOCX:** Paragraph and table extraction via python-docx.
- **TXT / Markdown:** Direct text ingestion with section detection.
- **CSV:** Row-by-row ingestion with column headers as context.
- Maximum file size configurable via `MAX_FILE_SIZE_MB`.
- Enable/disable: `INGESTION_ENABLED=true` in `.env`.

---

## Feature — Chunking and embedding

Split documents into retrievable chunks and compute vector embeddings.

- **Chunk size:** 1000 tokens (configurable via `CHUNK_SIZE`).
- **Overlap:** 200 tokens between consecutive chunks to preserve context at boundaries.
- **Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers (384-dimensional vectors).
- **Storage:** ChromaDB persisted to `CHROMA_PERSIST_DIR`.
- Chunks retain metadata: document ID, page number, character offset.
- Re-indexing: delete and re-embed all chunks for a document from the dashboard.

---

## Feature — RAG question answering

Ask natural-language questions and get grounded answers from your documents.

- Query is embedded using the same model as document chunks.
- ChromaDB similarity search retrieves the top-K most relevant chunks (`RETRIEVAL_TOP_K`).
- Optional re-ranking: score chunks by relevance to the query and reorder.
- Prompt construction: system prompt + retrieved context + user question.
- Ollama generates the answer using the configured LLM.
- Enable/disable: `RAG_ENABLED=true` in `.env`.

---

## Feature — Conversation memory

Maintain context across multiple questions within a session.

- Previous Q&A pairs are included in the prompt for follow-up questions.
- Memory is session-scoped (cleared on logout or session expiry).
- Configurable memory depth (number of previous exchanges to include).
- Enable/disable: `CONVERSATION_MEMORY_ENABLED=true` in `.env`.

---

## Feature — Source citations

Every answer includes references to the source documents.

- Citations show: document name, page number, and highlighted passage.
- Multiple citations per answer (one per retrieved chunk used).
- Click a citation to view the full chunk in context.
- Enable/disable: `CITATIONS_ENABLED=true` in `.env`.

---

## Feature — Document library management

Full lifecycle management of ingested documents.

- **Upload:** Drag-and-drop or file picker. Progress bar during ingestion.
- **View:** List all documents with metadata (name, type, size, chunk count, upload date).
- **Delete:** Remove document and all its chunks from ChromaDB.
- **Re-index:** Re-chunk and re-embed a document (useful after config changes).
- Enable/disable: `INGESTION_ENABLED=true` in `.env`.

---

## Feature — Summarization mode

Generate a concise summary of an entire document.

- Select a document from the library → click "Summarize."
- Iterative summarization: chunk summaries → combined final summary.
- Useful for long PDFs and reports.
- Enable/disable: `SUMMARIZATION_ENABLED=true` in `.env`.

---

## Feature — Model management

Switch between Ollama LLM models from the dashboard.

- List available models (locally downloaded).
- Pull new models from Ollama registry.
- Switch the active model at runtime (no restart needed).
- View model info: size, quantization, parameters.
- Enable/disable: `MODEL_MANAGEMENT_ENABLED=true` in `.env`.

---

## Feature — Document comparison mode

Compare two documents side-by-side with AI-generated diff analysis.

- Select two documents from the library.
- The LLM identifies key differences, similarities, and contradictions.
- Useful for comparing contract versions, policy updates, or research papers.
- Enable/disable: `COMPARISON_ENABLED=true` in `.env`.

---

## Feature — API endpoint

Programmatic access to the Q&A system.

- **POST /api/ask** — Send a question, receive an answer with citations.
- Request body: `{ "question": "...", "document_ids": [...] }` (optional filter).
- Response: `{ "answer": "...", "citations": [...] }`.
- Optional API key authentication via `API_KEY` in `.env`.
- Enable/disable: `API_ENABLED=true` in `.env`.

---

## Feature — CSV export of Q&A history

Export all questions and answers for record-keeping or analysis.

- Download from Settings page or via API.
- Columns: timestamp, question, answer, model used, source documents, citations.
- Date range filter.
- Enable/disable: `EXPORT_ENABLED=true` in `.env`.

---

## Feature — Web dashboard

| Page | Description |
|---|---|
| **Dashboard** | Overview: document count, total chunks, Q&A count, Ollama model status, system info (CPU temp, RAM, disk) |
| **Chat** | Conversational Q&A interface with streaming responses, source citations, and conversation history |
| **Documents** | Document library: upload, view metadata, delete, re-index, summarize |
| **Compare** | Side-by-side document comparison with AI-generated analysis |
| **Models** | Model management: list, pull, switch, view info |
| **Settings** | Configuration, password change, CSV export, system info |

**Real-time features:**
- Streaming LLM responses via WebSocket (tokens appear as generated).
- Live ingestion progress during document upload.
- Model pull progress indicator.

---

## Authentication

- Session-based login with bcrypt password hashing.
- Rate limiting: 10 attempts per 15 minutes per IP.
- Session expiry: 24 hours.
- Password changeable from Settings page.

---

## How to deploy to Raspberry Pi

SSH config at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Deploy script:**

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/PrivateGPT
```

**Manual:**

```bash
rsync -avz --delete \
  --exclude='venv/' --exclude='.env' --exclude='.git/' --exclude='data/' \
  ./ rasp-pi:/home/pi/Projects/PrivateGPT/
```

---

## How to run on the Raspberry Pi

```bash
ssh rasp-pi
cd /home/pi/Projects/PrivateGPT

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3:8b-q4_0

nano .env   # Set SESSION_SECRET, ADMIN_PASSWORD
source venv/bin/activate
python app.py
```

Access: `http://192.168.216.90:5000`

**systemd service:**

```ini
[Unit]
Description=Local LLM PrivateGPT
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projects/PrivateGPT
ExecStart=/home/pi/Projects/PrivateGPT/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## Security notes

- Change the default password immediately.
- Generate a strong `SESSION_SECRET`: `python -c "import secrets; print(secrets.token_hex(32))"`
- `.env` contains sensitive data — never commit. Protect: `chmod 600 .env`
- All documents and embeddings stored locally. No external API calls.
- API endpoint (`/api/ask`) should be firewalled or protected with `API_KEY` if exposed.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ollama not running | Start Ollama: `ollama serve`. Check: `curl http://localhost:11434/api/tags`. |
| Model too slow | Use a smaller model: `ollama pull phi3:mini-q4_0`. Reduce `OLLAMA_MAX_TOKENS`. |
| Out of memory | Use Q4 quantized models only. Close other processes. Add swap: `sudo fallocate -l 4G /swapfile`. |
| ChromaDB errors | Delete `data/chroma/` and re-index all documents. Check disk space. |
| PDF extraction fails | Ensure PyMuPDF installed: `pip install PyMuPDF`. Some scanned PDFs need OCR (not supported). |
| DOCX extraction fails | Ensure python-docx installed: `pip install python-docx`. |
| Embedding model slow on first load | First load downloads ~90 MB model. Subsequent loads are cached. |
| Upload fails | Check `MAX_FILE_SIZE_MB` in `.env`. Check disk space. |
| USB SSD not mounted | Mount: `sudo mount /dev/sda1 /mnt/ssd`. Update `CHROMA_PERSIST_DIR` and `UPLOAD_DIR` in `.env`. |

---

## Where to next

- Add OCR support (Tesseract) for scanned PDFs.
- Add image-based document understanding (multimodal LLMs).
- Add EPUB and HTML ingestion support.
- Add scheduled re-indexing for updated documents.
- Add multi-user support with per-user document collections.
- Add Hailo-8L or Google Coral accelerator for faster embedding.
