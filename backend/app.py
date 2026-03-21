# IMPORTS

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import chromadb
import ollama
import json
import logging
from dotenv import load_dotenv   
import os         
from ingest import router as ingest_router               

# SETUP

load_dotenv()  # reads the .env file first thing

# all config comes from .env now
MODEL_NAME   = os.getenv("OLLAMA_MODEL",  "tinyllama")
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(BASE_DIR, "db"))
N_RESULTS    = int(os.getenv("N_RESULTS", "3"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG API",
    description="Real-time RAG with streaming",
    version="1.0.0"
)

# CORS MIDDLEWARE

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
# This plugs in all the /ingest/* endpoints
# Now app.py has: /health, /query, /query/stream, /documents, /ingest/upload, /ingest/list, /ingest/document/{name}

# DATABASE CONNECTION

chroma = chromadb.PersistentClient(path=CHROMA_PATH)  #  uses .env value

collection = chroma.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"}
)

# REQUEST / RESPONSE MODELS


class QueryRequest(BaseModel):
    question: str
    n_results: int = N_RESULTS   #  uses .env value as default

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    model: str


# HELPER FUNCTION

def build_prompt(context_chunks: list[str], question: str) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return f"""You are a helpful assistant. Answer the question using ONLY the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."
Do not make up information.

Context:
{context}

Question: {question}

Answer:"""

# ENDPOINTS


@app.get("/health")
def health_check():
    try:
        models = ollama.list()
        available_models = [
            m.get("model") or m.get("name", "unknown")
            for m in models.get("models", [])
        ]
        return {
            "status": "ok",
            "ollama": "connected",
            "available_models": available_models,
            "docs_indexed": collection.count()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Ollama not reachable")


@app.post("/query")
def query(request: QueryRequest):
    logger.info(f"Query received: {request.question}")
    try:
        results = collection.query(
            query_texts=[request.question],
            n_results=request.n_results
        )
        chunks = results["documents"][0] if results["documents"] else []

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No documents indexed yet. Please upload some documents first."
            )

        prompt = build_prompt(chunks, request.question)

        response = ollama.generate(
            model=MODEL_NAME,   # uses .env value
            prompt=prompt
        )

        logger.info("Query answered successfully")

        return QueryResponse(
            answer=response["response"],
            sources=chunks,
            model=MODEL_NAME    #  uses .env value
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/query/stream")
def query_stream(request: QueryRequest):

    def generate():
        try:
            results = collection.query(
                query_texts=[request.question],
                n_results=request.n_results
            )
            chunks = results["documents"][0] if results["documents"] else []

            if not chunks:
                yield f"data: {json.dumps({'error': 'No documents indexed yet'})}\n\n"
                return

            yield f"data: {json.dumps({'sources': chunks, 'done': False})}\n\n"

            prompt = build_prompt(chunks, request.question)

            stream = ollama.generate(
                model=MODEL_NAME,   #  uses .env value
                prompt=prompt,
                stream=True
            )

            for chunk in stream:
                token = chunk.get("response", "")
                is_done = chunk.get("done", False)
                yield f"data: {json.dumps({'token': token, 'done': is_done})}\n\n"
                if is_done:
                    break

        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@app.get("/documents")
def list_documents():
    try:
        results = collection.get()
        return {
            "total_chunks": len(results["ids"]),
            "documents": [
                {
                    "id": results["ids"][i],
                    "preview": results["documents"][i][:100] + "...",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                }
                for i in range(len(results["ids"]))
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))