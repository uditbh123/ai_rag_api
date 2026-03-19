# 🧠 AI RAG API

> A real-time, production-ready Retrieval-Augmented Generation (RAG) system — ask questions, get accurate answers from your own documents. No hallucinations. No API costs. Runs 100% locally.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector--db-orange?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-TinyLlama-purple?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-containerized-blue?style=flat-square&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-deployed-326CE5?style=flat-square&logo=kubernetes)

---

## 📖 What is this project?

Most AI chatbots make things up when they don't know the answer — this is called **hallucination**. RAG (Retrieval-Augmented Generation) fixes that by giving the AI access to a knowledge base *you* control. Before answering, it searches your documents for relevant context, then uses that context to generate a grounded, accurate answer.

This project is a full RAG backend API built from scratch:

- You upload documents (`.txt`, `.md`, `.csv`, etc.)
- They get split into smart, overlapping chunks and stored in a vector database
- When you ask a question, the system finds the most semantically relevant chunks
- Those chunks are fed to a local LLM (TinyLlama via Ollama) to generate the answer
- The answer streams back to you **token by token**, in real time — just like ChatGPT

Everything runs **locally on your machine** — no OpenAI key, no cloud costs, no data leaving your computer.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      React UI (Step 5)                   │
│         Chat panel · Upload panel · Status bar           │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTP + SSE streaming
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│  /health  /query  /query/stream  /ingest/*  /documents   │
└────────┬───────────────────────┬────────────────────────┘
         │                       │
┌────────▼────────┐    ┌─────────▼────────┐
│    ChromaDB     │    │   Ollama (local)  │
│  Vector store   │    │   TinyLlama LLM   │
│  Cosine search  │    │   Streaming gen.  │
└─────────────────┘    └──────────────────┘
```

**How a query flows through the system:**

1. User sends question → FastAPI `/query/stream`
2. FastAPI embeds the question and queries ChromaDB for the top 3 most relevant chunks
3. Those chunks are formatted into a prompt and sent to Ollama with `stream=True`
4. Each token from Ollama is forwarded to the browser immediately via SSE
5. User sees the answer appear word by word in real time

---

## ✨ Features

| Feature | Details |
|---|---|
| **Real-time streaming** | Tokens stream via Server-Sent Events (SSE) — no waiting for the full response |
| **Smart chunking** | Documents split into 500-char overlapping chunks so no context is lost at boundaries |
| **Deduplication** | Content-hashed chunk IDs mean re-ingesting a file never creates duplicates |
| **File upload API** | `POST /ingest/upload` accepts any text file and chunks it automatically |
| **Document management** | List and delete indexed documents via API |
| **Health check** | `/health` exposes Ollama status, available models, and total chunks indexed |
| **Privacy-first** | 100% local — no data sent to external APIs |
| **Zero hallucination** | LLM is instructed to only answer from retrieved context |
| **Docker ready** | Single `docker build` packages everything |
| **Kubernetes deployed** | Manifests included for Minikube/production cluster deployment |

---

## 📁 Project Structure

```
AI_RAG_API/
│
├── backend/
│   ├── app.py          # FastAPI app — all endpoints including SSE streaming
│   ├── embed.py        # Chunking logic + ChromaDB ingestion (reusable module)
│   ├── ingest.py       # Upload/delete/list endpoints (uses embed.py)
│   └── db/             # ChromaDB persistent storage (auto-created)
│
├── frontend/           # React UI (in progress)
│   └── src/
│       ├── App.jsx
│       └── components/
│
├── .env                # Config: model name, chunk size, DB path
├── requirements.txt    # All Python dependencies pinned
├── Dockerfile          # Container definition
├── deployment.yaml     # Kubernetes deployment manifest
├── service.yaml        # Kubernetes NodePort service
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- pip

### 1. Clone and set up

```bash
git clone https://github.com/uditbh123/ai_rag_api.git
cd ai_rag_api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Pull the AI model

```bash
ollama pull tinyllama
```

### 3. Configure environment

Create a `.env` file in the root:

```env
OLLAMA_MODEL=tinyllama
CHROMA_PATH=./db
N_RESULTS=3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### 4. Ingest your documents

```bash
cd backend
python embed.py
```

This reads `k8s.txt`, splits it into overlapping chunks, and stores them in ChromaDB. Add your own `.txt` files to the `files_to_ingest` list in `embed.py`.

### 5. Start the API

```bash
uvicorn app:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI — you can test every endpoint directly in your browser.

---

## 📡 API Reference

### Core endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Check if Ollama is running, list available models and chunk count |
| `POST` | `/query` | Ask a question, get the full answer at once |
| `POST` | `/query/stream` | Ask a question, get the answer streamed token by token (SSE) |
| `GET` | `/documents` | List all indexed chunks |

### Document management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/upload` | Upload a file (`.txt`, `.md`, `.csv`, `.json`, `.py`) — max 10MB |
| `GET` | `/ingest/list` | List all source documents with chunk counts and previews |
| `DELETE` | `/ingest/document/{name}` | Remove all chunks belonging to a document |

### Example: streaming query

```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?", "n_results": 3}'
```

Each SSE event looks like:
```
data: {"sources": ["chunk1...", "chunk2..."], "done": false}
data: {"token": "Kubernetes", "done": false}
data: {"token": " is", "done": false}
data: {"token": " a container", "done": false}
...
data: {"token": ".", "done": true}
```

### Example: upload a document

```bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "file=@my_document.txt"
```

Response:
```json
{
  "message": "Successfully ingested 'my_document.txt'",
  "chunks_stored": 12,
  "filename": "my_document.txt",
  "file_size_kb": 5.3
}
```

---

## 🐳 Docker

The entire application is containerized. Ollama runs on the host machine; the container connects to it via `host.docker.internal`.

```bash
# Build
docker build -t rag-app .

# Run
docker run -p 8000:8000 rag-app
```

The Dockerfile runs `embed.py` at build time so the knowledge base is ready the moment the container starts.

---

## ☸️ Kubernetes

Deployment manifests are included for running in a Minikube cluster.

```bash
# Apply manifests
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Get the service URL
minikube service rag-app-service --url
```

The `deployment.yaml` defines pod scaling and resource limits. The `service.yaml` exposes the API via a NodePort so it's reachable from your local machine.

---

## 🧠 Key Concepts Explained

**Why chunking matters**

If you store a 50-page document as one giant blob, the vector search retrieves the whole document for every query — the LLM drowns in irrelevant context. By splitting into 500-character chunks with 50-character overlap, the search returns only the 2-3 paragraphs that actually answer the question.

**Why overlap matters**

When you split at character 500, a sentence might be cut in half. The 50-character overlap means each chunk shares a small tail with the next one — so no context is ever lost at a boundary.

**Why cosine similarity**

ChromaDB is configured to use cosine similarity instead of euclidean distance. Two sentences can mean the same thing using completely different words — cosine similarity measures the angle between their meaning vectors (direction), not the word-for-word distance. This catches semantic similarity far better.

**Why SSE instead of WebSockets**

WebSockets are bidirectional — both sides can send and receive freely. SSE is one-directional (server pushes to client). For streaming an LLM response, we only need the server to push tokens — SSE is simpler, works over regular HTTP/1.1, and needs no special infrastructure.

---

## 🗺️ Roadmap

This is **Project 1** of a 4-part DevOps series:

- ✅ **Project 1** — Build the RAG API with streaming, chunking, and upload endpoints
- ✅ **Project 2** — Containerize with Docker
- ✅ **Project 3** — Deploy on Kubernetes (Minikube)
- 🔄 **Project 4** — React UI + real-time streaming frontend
- ⏳ **Project 5** — CI/CD with GitHub Actions
- ⏳ **Project 6** — Monitoring with Grafana dashboards

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API framework | FastAPI | Async, fast, auto-generates Swagger docs |
| LLM runtime | Ollama + TinyLlama | Local inference, no API costs |
| Vector database | ChromaDB | Persistent, cosine similarity, easy to use |
| Streaming | Server-Sent Events (SSE) | Simple, HTTP-native, no WebSocket overhead |
| Config | python-dotenv | Keeps secrets and settings out of code |
| Containerization | Docker | Reproducible environments |
| Orchestration | Kubernetes | Production-grade scaling and deployment |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

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