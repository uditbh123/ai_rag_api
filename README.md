# AI RAG API

A production-ready Retrieval-Augmented Generation (RAG) API built with FastAPI that enables semantic search and question-answering capabilities over custom documents.

## 🌟 Overview

This project implements a RAG (Retrieval-Augmented Generation) system that makes AI smarter by giving it access to your own custom knowledge base. Built with FastAPI, it uses local AI models (Ollama + TinyLlama) and vector databases (ChromaDB) to provide accurate, context-aware answers based on your specific documents—without expensive API costs or privacy concerns.

**Part 1 of the NextWork AI DevOps Series** - This is the foundational RAG API that will be containerized, automated, and monitored in future projects.

## 🚀 Features

- **Local AI Models**: Uses Ollama with TinyLlama to run AI locally—no expensive API costs
- **Vector Database**: ChromaDB stores embeddings for semantic search based on meaning, not just keywords
- **Document Ingestion**: Convert text documents into vector embeddings for your knowledge base
- **Intelligent Querying**: Ask questions and get accurate answers based on your specific documents
- **FastAPI Backend**: High-performance async API with automatic Swagger UI documentation
- **No Hallucinations**: AI responses are grounded in your actual documents, preventing made-up answers
- **Privacy-First**: All data stays local on your machine

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed locally
- pip for package management
- Basic understanding of REST APIs

## 🛠️ Installation

1. **Install Ollama**
   
   Download and install Ollama from [https://ollama.ai/](https://ollama.ai/)
   
   Pull the TinyLlama model:
   ```bash
   ollama pull tinyllama
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/uditbh123/ai_rag_api.git
   cd ai_rag_api
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install fastapi uvicorn chromadb ollama langchain
   ```

## 🎯 Usage

### The RAG Workflow

This project follows a two-step process:

1. **Ingestion**: Embed your documents into ChromaDB
2. **Query**: Ask questions and get AI-generated answers based on your documents

### Step 1: Embed Documents

First, create your knowledge base. For example, create a file `k8s.txt` with information about Kubernetes, then run:

```bash
python embed.py
```

This converts your text into vector embeddings and stores them in ChromaDB.

### Step 2: Start the API

Start the FastAPI server:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Step 3: Query Your Knowledge Base

**Using curl:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Kubernetes?"}'
```

**Using Swagger UI:**

Visit `http://localhost:8000/docs` for an interactive interface where you can test queries directly in your browser.

### How It Works

1. **User asks a question** via the `/query` endpoint
2. **ChromaDB retrieves** the most relevant text snippets from your documents
3. **Context is sent** to TinyLlama along with the question
4. **AI generates** an accurate answer based on your specific knowledge base

### Example: Before vs After RAG

**Without RAG (Hallucination):**
- Question: "What is Kubernetes?"
- Answer: "A type of dessert" ❌

**With RAG (Accurate):**
- Question: "What is Kubernetes?"  
- Answer: "Kubernetes is an open-source container orchestration platform..." ✅

## 📁 Project Structure

```
ai_rag_api/
├── app.py          # Main FastAPI application with /query endpoint
├── embed.py        # Script to embed documents into ChromaDB
├── k8s.txt         # Example knowledge base document (Kubernetes info)
├── .gitignore      # Git ignore rules
└── README.md       # Project documentation
```

## 🔮 Future Roadmap

This is **Project 1** in a 4-part series:

- ✅ **Project 1**: Build the RAG API (Current)
- ⏳ **Project 2**: Containerize with Docker
- ⏳ **Project 3**: Automate with GitHub Actions  
- ⏳ **Project 4**: Monitor with Grafana dashboards

## 🧪 Testing

Test your API to ensure it's working correctly:

1. **Health Check**: Visit `http://localhost:8000` in your browser
2. **Interactive Testing**: Use Swagger UI at `http://localhost:8000/docs`
3. **Command Line**: Use curl commands to test the `/query` endpoint

## 🛠️ Tech Stack

- **FastAPI**: Modern web framework for building APIs
- **Ollama + TinyLlama**: Local AI model for generation
- **ChromaDB**: Vector database for storing embeddings
- **LangChain**: Framework for building LLM applications
- **Python**: Programming language

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and API info |
| `/query` | POST | Query the RAG system with a question |
| `/docs` | GET | Interactive Swagger UI documentation |

## 💡 Key Concepts

**RAG (Retrieval-Augmented Generation)**  
Instead of the AI making things up, RAG grounds responses in your actual documents. It retrieves relevant information first, then generates an answer.

**Vector Embeddings**  
Your text is converted into numerical representations that capture meaning, allowing semantic search (searching by concept, not just keywords).

**Local AI**  
Using Ollama and TinyLlama means no API costs, better privacy, and full control over your AI stack.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐳 Project 2: Containerization with Docker

This stage of the project involved packaging the entire FastAPI + ChromaDB application into a portable Docker image. This ensures that the RAG API works identically across different environments (Windows, macOS, or Linux) without manual dependency setup.

### 🏗️ Docker Architecture
The container encapsulates the Python 3.11 environment, all library dependencies, and the pre-computed vector database. It communicates with the host machine to access the AI models running via Ollama.



### 🛠️ Docker Implementation
- **Base Image**: `python:3.11-slim` (Optimized for size and security)
- **Dependency Management**: Integrated installation of `fastapi`, `uvicorn`, `chromadb`, and `ollama`
- **Automation**: The `Dockerfile` automatically runs `embed.py` during the build process to ensure the database is ready upon startup.

### 🚀 How to Run with Docker

1. **Build the Image**
   ```bash
   docker build -t rag-app .

2. **Run the Container**
   ```bash
   docker run -p 8000:8000 rag-app

### 📡 Technical Challenge: Container Networking
A key challenge during containerization was enabling the API inside the Docker container to talk to the Ollama service running on the host machine.

- **The Solution**: Configured the application to use `http://host.docker.internal:11434` instead of `localhost`, allowing the container to bypass its own isolated network and reach the host's AI engine.

## 📁 Project Structure

```
ai_rag_api/
├── app.py
├── embed.py
├── k8s.txt
├── Dockerfile
├── .dockerignore  
├── .gitignore
└── README.md
```

---
## ☸️ Phase 3: Kubernetes Orchestration
I successfully deployed the containerized RAG API into a **Minikube** cluster. This transition highlights the application's readiness for a production-scale environment.

### Deployment Details:
- **Orchestrator:** Kubernetes (via Minikube)
- **Manifests:** - `deployment.yaml`: Defines pod scaling and container resource limits.
    - `service.yaml`: Uses a **NodePort** to expose the API to the local machine.
- **Networking:** Leveraged `minikube service` to tunnel traffic from the host to the cluster.

### Commands to Deploy:
```powershell
# Apply configurations
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Access the API
minikube service rag-app-service --url