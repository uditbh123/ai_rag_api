
# IMPORTS

from fastapi import APIRouter, UploadFile, File, HTTPException
# APIRouter → like a mini FastAPI app — lets us group related endpoints
# together and then plug them into the main app.py
# app.py is the main building, routers are floors

# UploadFile → FastAPI's special type for handling file uploads
# It gives us the filename, content type, and the actual file data
# File → used as a default value marker to tell FastAPI "this is a form field"

import chromadb
import os
import tempfile
# tempfile → creates temporary files that auto-delete when we're done
# When the user uploads a file, we don't save it permanently to disk
# We write it to a temp location, process it, then it disappears

from dotenv import load_dotenv
from embed import ingest_file
# This imports the ingest_file() function we just built in embed.py
# This is WHY we added the if __name__ == "__main__" guard —
# so we can import just the function without running the whole script

# SETUP


load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./db")

# Supported file types — we only handle plain text for now
# In the future we will add PDF, DOCX etc.
ALLOWED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv"}

# APIRouter lets us define endpoints here and register them in app.py
# prefix="/ingest" means all routes here start with /ingest
# tags=["ingest"] groups them together in the /docs UI
router = APIRouter(prefix="/ingest", tags=["ingest"])

# SHARED DB CONNECTION


# Connect to the same ChromaDB collection as app.py
# Both files talk to the same database on disk
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"}
)

# ENDPOINTS

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts a file upload from the React UI, chunks it,
    and stores it in ChromaDB.

    The full URL will be: POST /ingest/upload
    (because of the prefix="/ingest" on the router above)

    How file uploads work in HTTP:
    - Normal JSON requests:  Content-Type: application/json
    - File upload requests:  Content-Type: multipart/form-data
      The file is sent in "parts" — like an email with an attachment
      FastAPI's UploadFile handles all the parsing for us
    """

    # ── Validate file extension ──────────────────────────────
    # os.path.splitext("report.txt") → ("report", ".txt")
    # [1] gives us the extension part
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()   # normalize: ".TXT" → ".txt"

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # ── Validate file size (max 10MB) ────────────────────────
    # file.read() loads the entire file into memory as bytes
    content = await file.read()
    # await is needed because file.read() is async (non-blocking)
    # "async" means: start reading, let other requests run meanwhile,
    # come back when reading is done — important for a real server

    max_size = 10 * 1024 * 1024   # 10MB in bytes (10 * 1024 * 1024 = 10,485,760)
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is 10MB, got {len(content) / 1024 / 1024:.1f}MB"
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Write to a temp file and ingest ─────────────────────
    # Why a temp file? Because ingest_file() expects a filepath string.
    # We could refactor it to accept raw text, but using a temp file
    # is simpler and keeps ingest_file() reusable for both cases.

    # tempfile.NamedTemporaryFile creates a file like /tmp/tmpXXXXXX.txt
    # delete=False → don't auto-delete when closed (we delete manually below)
    # suffix=ext   → keep the original extension so the filename looks right
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=ext,
            mode="wb"    # "wb" = write bytes mode
        ) as tmp:
            tmp.write(content)   # write the uploaded bytes to disk
            tmp_path = tmp.name  # save the path e.g. "/tmp/tmpABC123.txt"

        # Now call the ingest_file() function from embed.py
        # We pass the original filename so metadata shows "k8s.txt"
        # not the ugly temp path "/tmp/tmpABC123.txt"
        result = ingest_file(
            filepath=tmp_path,
            collection=collection,
            display_name=file.filename   
        )

        return {
            "message":      f"Successfully ingested '{file.filename}'",
            "chunks_stored": result["chunks_stored"],
            "filename":     file.filename,
            "file_size_kb": round(len(content) / 1024, 1)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )
    finally:
        # finally block ALWAYS runs — even if an exception was raised above
        # This guarantees we clean up the temp file no matter what
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)   # os.unlink() = delete a file


@router.delete("/document/{doc_source}")
def delete_document(doc_source: str):
    """
    Deletes all chunks belonging to a specific source document.

    The React UI's document list will have a delete button per file.
    Clicking it calls: DELETE /ingest/document/k8s.txt

    {doc_source} is a path parameter — FastAPI extracts it from the URL
    e.g. /ingest/document/k8s.txt → doc_source = "k8s.txt"
    """
    try:
        # ChromaDB's .get() with a where filter finds all chunks
        # where metadata["source"] == doc_source
        # This is why we stored "source" in the metadata in embed.py!
        results = collection.get(
            where={"source": doc_source}
        )

        if not results["ids"]:
            raise HTTPException(
                status_code=404,
                detail=f"No document found with source '{doc_source}'"
            )

        # Delete all the chunks that belong to this file
        collection.delete(ids=results["ids"])

        return {
            "message":        f"Deleted '{doc_source}' from the knowledge base",
            "chunks_deleted":  len(results["ids"])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def list_documents():
    """
    Returns a clean list of unique source documents (not individual chunks).

    The raw ChromaDB .get() returns one entry per chunk —
    so a 10-page PDF might return 40 entries all from the same file.
    We deduplicate here so the UI shows one row per file, not per chunk.
    """
    try:
        results = collection.get()

        if not results["ids"]:
            return {"documents": [], "total_chunks": 0}

        # Group chunks by their source file
        # seen_sources is a dict: { "k8s.txt": { chunks: 3, index: 0 } }
        seen_sources = {}

        for i, metadata in enumerate(results["metadatas"] or []):
            source = metadata.get("source", "unknown")

            if source not in seen_sources:
                seen_sources[source] = {
                    "source":       source,
                    "chunk_count":  0,
                    "preview":      results["documents"][i][:120] + "..."
                    # show the first 120 chars of the first chunk as a preview
                }

            seen_sources[source]["chunk_count"] += 1

        return {
            "documents":    list(seen_sources.values()),
            "total_chunks": len(results["ids"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))