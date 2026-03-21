# 🧠 AI RAG API

> A full-stack, real-time Retrieval-Augmented Generation (RAG) system — built from scratch. Ask questions about your own documents, get accurate streaming answers. No hallucinations. No API costs. Runs 100% locally.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--db-orange?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-TinyLlama-purple?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-containerized-blue?style=flat-square&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-deployed-326CE5?style=flat-square&logo=kubernetes)

---

## 📖 What is this project?

Most AI chatbots make things up when they don't know the answer — this is called **hallucination**. RAG (Retrieval-Augmented Generation) fixes that by giving the AI access to a knowledge base *you* control. Before answering, it searches your documents for relevant context, then uses that context to generate a grounded, accurate answer.

This project is a complete, production-ready RAG system built from scratch — FastAPI backend, ChromaDB vector store, local LLM, and a React frontend that streams responses token by token just like ChatGPT:

- Upload any document (`.txt`, `.md`, `.csv`, `.json`, `.py`) via drag & drop
- It gets split into smart overlapping chunks and stored in a vector database
- Ask a question — the system finds the most semantically relevant chunks
- A local LLM (TinyLlama via Ollama) generates an answer using only that context
- The answer streams back **token by token** in real time via SSE

Everything runs **locally on your machine** — no OpenAI key, no cloud costs, no data leaving your computer.

---

## 🖥️ UI

The React frontend has three areas that work together in real time:

- **Sidebar** — drag & drop file upload, indexed document list with delete, chunk info
- **Chat panel** — streaming chat interface with source citations shown per message
- **Status bar** — live backend health dot, active model name, total chunks indexed

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React UI (Vite)                      │
│    Sidebar · ChatPanel · Message · StatusBar             │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTP + SSE streaming
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                          │
│  GET  /health             → Ollama status + chunk count  │
│  POST /query              → Full answer (non-streaming)  │
│  POST /query/stream       → Token-by-token SSE stream    │
│  POST /ingest/upload      → Upload + chunk + store file  │
│  GET  /ingest/list        → List all indexed documents   │
│  DEL  /ingest/document/   → Remove a document            │
└────────┬───────────────────────┬────────────────────────┘
         │                       │
┌────────▼────────┐    ┌─────────▼────────┐
│    ChromaDB     │    │   Ollama (local)  │
│  Vector store   │    │   TinyLlama LLM   │
│  Cosine search  │    │   stream=True     │
│  Persistent db  │    │   No API costs    │
└─────────────────┘    └──────────────────┘
```

**How a query flows through the system:**

1. User types a question → React calls `POST /query/stream`
2. FastAPI searches ChromaDB for the top 3 most relevant chunks
3. Chunks are formatted into a prompt and sent to Ollama with `stream=True`
4. Each token Ollama generates is immediately forwarded to the browser via SSE
5. React appends each token to the message bubble — the answer appears word by word

---

## ✨ Features

| Feature | Details |
|---|---|
| **Real-time streaming** | Tokens stream via Server-Sent Events (SSE) — no waiting for the full response |
| **Smart chunking** | Documents split into 500-char overlapping chunks so no context is lost at boundaries |
| **Deduplication** | Content-hashed chunk IDs mean re-ingesting a file never creates duplicates |
| **Drag & drop upload** | Drop any supported file into the sidebar — chunked and indexed automatically |
| **Source citations** | Every AI response shows exactly which document chunks were used |
| **Document management** | Upload, list, and delete indexed documents directly from the UI |
| **Health monitoring** | Status bar shows live backend health, model name, and chunk count |
| **Privacy-first** | 100% local — no data sent to any external API |
| **Zero hallucination** | LLM is instructed to answer only from retrieved context |
| **Docker ready** | Single `docker build` packages the entire backend |
| **Kubernetes deployed** | Manifests included for Minikube and production clusters |

---

## 📁 Project Structure

```
AI_RAG_API/
│
├── backend/
│   ├── app.py          # FastAPI app — all endpoints including SSE streaming
│   ├── embed.py        # Chunking logic + ChromaDB ingestion (reusable module)
│   ├── ingest.py       # Upload / delete / list API endpoints
│   └── db/             # ChromaDB persistent storage (auto-created, git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx              # React entry point
│   │   ├── App.jsx               # Root component — holds all state
│   │   ├── App.css
│   │   ├── index.css
│   │   └── components/
│   │       ├── ChatPanel.jsx     # Message list + streaming input box
│   │       ├── ChatPanel.css
│   │       ├── Sidebar.jsx       # File upload + document list
│   │       ├── Sidebar.css
│   │       ├── Message.jsx       # Individual message bubble + sources
│   │       ├── Message.css
│   │       ├── StatusBar.jsx     # Backend health + model info
│   │       └── StatusBar.css
│   ├── vite.config.js            # Proxy — forwards /api/* to FastAPI
│   └── package.json
│
├── .env                # Config: model name, chunk size, DB path (git-ignored)
├── .gitignore
├── requirements.txt    # All Python dependencies pinned
├── Dockerfile          # Container definition for the backend
├── deployment.yaml     # Kubernetes deployment manifest
├── service.yaml        # Kubernetes NodePort service
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai/) installed

### 1. Clone and set up Python environment

```bash
git clone https://github.com/uditbh123/ai_rag_api.git
cd ai_rag_api

python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -r requirements.txt
```

### 2. Pull the AI model

```bash
ollama pull tinyllama
```

### 3. Configure environment

Create a `.env` file inside the `backend/` folder:

```env
OLLAMA_MODEL=tinyllama
CHROMA_PATH=./db
N_RESULTS=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### 4. Ingest your first document

```bash
cd backend
python embed.py
```

This reads `k8s.txt`, splits it into overlapping chunks, and stores them in ChromaDB. Add your own files to the `files_to_ingest` list in `embed.py`, or upload them directly through the UI.

### 5. Start everything

Ollama starts automatically on Windows and macOS. Open two terminals:

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — the status bar should show a green dot and your model name. Visit `http://localhost:8000/docs` for the interactive Swagger UI to test every API endpoint directly.

---

## 📡 API Reference

### Core endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Ollama status, available models, total chunks indexed |
| `POST` | `/query` | Ask a question — returns the full answer at once |
| `POST` | `/query/stream` | Ask a question — streams tokens via SSE in real time |

### Document management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/upload` | Upload a file — chunked and stored automatically (max 10MB) |
| `GET` | `/ingest/list` | List all source documents with chunk counts and previews |
| `DELETE` | `/ingest/document/{name}` | Remove all chunks belonging to a document |

### Example: streaming query

```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?", "n_results": 3}'
```

Each SSE event arrives as it is generated:
```
data: {"sources": ["Kubernetes is a container..."], "done": false}
data: {"token": "Kubernetes", "done": false}
data: {"token": " is", "done": false}
data: {"token": " a container", "done": false}
data: {"token": ".", "done": true}
```

### Example: upload a document

```bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "file=@my_document.txt"
```

```json
{
  "message": "Successfully ingested 'my_document.txt'",
  "chunks_stored": 12,
  "filename": "my_document.txt",
  "file_size_kb": 5.3
}
```

---

## 🧠 Key Concepts Explained

**Why chunking matters**

Storing a 50-page document as one blob means the vector search retrieves everything for every query — the LLM drowns in noise. Splitting into 500-character chunks means the search returns only the 2-3 paragraphs that actually answer the question.

**Why overlap matters**

Splitting at exactly character 500 might cut a sentence in half. The 50-character overlap means each chunk shares a small tail with the next one — no context is ever lost at a boundary.

**Why cosine similarity**

Two sentences can mean the same thing using completely different words. Cosine similarity measures the angle between meaning vectors (direction), not word-for-word distance. This catches semantic similarity far better than keyword matching.

**Why SSE instead of WebSockets**

WebSockets are bidirectional — both sides send and receive freely. SSE is one-directional (server pushes to client). For streaming LLM tokens we only need the server to push — SSE is simpler, works over plain HTTP, and needs zero extra infrastructure.

**Why state lives in App.jsx**

All React state (messages, documents, health) lives at the root component and gets passed down as props. This is called lifting state up — the most important React pattern. It means Sidebar, ChatPanel, and StatusBar all read from the same source of truth and stay in sync automatically.

**Why content-hashed IDs for deduplication**

Each chunk is stored with an ID derived from an MD5 hash of its content. Running `embed.py` twice on the same file produces the same IDs — ChromaDB's `upsert()` updates instead of duplicating. No stale data, no bloat.

---

## 🐳 Docker

```bash
# Build
docker build -t rag-app .

# Run (Ollama must be running on the host)
docker run -p 8000:8000 rag-app
```

The Dockerfile runs `embed.py` at build time so the knowledge base is ready the moment the container starts. The container reaches Ollama on the host machine via `host.docker.internal:11434`.

---

## ☸️ Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
minikube service rag-app-service --url
```

`deployment.yaml` defines pod scaling and resource limits. `service.yaml` exposes the API via NodePort so it is reachable from your local machine.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API framework | FastAPI | Async, fast, auto-generates Swagger docs |
| LLM runtime | Ollama + TinyLlama | Local inference, zero API cost |
| Vector database | ChromaDB | Persistent, cosine similarity, simple API |
| Streaming | Server-Sent Events (SSE) | Simple, HTTP-native, no WebSocket overhead |
| Frontend framework | React 18 + Vite | Fast dev server, component-based UI |
| State management | React hooks only | No Redux needed at this scale |
| Config management | python-dotenv | Keeps secrets and settings out of source code |
| Containerization | Docker | Reproducible environments across machines |
| Orchestration | Kubernetes | Production-grade scaling and deployment |

---

## 🗺️ Roadmap

- ✅ **Phase 1** — RAG API with SSE streaming, smart chunking, upload endpoints
- ✅ **Phase 2** — Containerize with Docker
- ✅ **Phase 3** — Deploy on Kubernetes (Minikube)
- ✅ **Phase 4** — React UI with real-time streaming, drag & drop upload, source citations
- ⏳ **Phase 5** — Conversation history (multi-turn chat memory)
- ⏳ **Phase 6** — CI/CD pipeline with GitHub Actions
- ⏳ **Phase 7** — Monitoring and dashboards with Grafana

---

## 🤝 Contributing

Pull requests are welcome! For major changes please open an issue first.

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
# Open a Pull Request
```

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with curiosity · Runs locally · No cloud required</p>