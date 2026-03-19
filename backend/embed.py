# IMPORTS

import chromadb
import os
from dotenv import load_dotenv

# hashlib lets us create a unique fingerprint (hash) for each chunk of text
# We use this to avoid storing the same chunk twice if we run the script again
import hashlib

# CONFIG FROM .env

load_dotenv()

CHROMA_PATH  = os.getenv("CHROMA_PATH",  "./db")
CHUNK_SIZE   = int(os.getenv("CHUNK_SIZE",   "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# THE CHUNKING FUNCTION — heart of this file

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits a long text into smaller overlapping chunks.

    How it works step by step:
      text = "ABCDEFGHIJ"  chunk_size=4  overlap=1

      Step 1: start=0  → chunk = text[0:4]   = "ABCD"
      Step 2: start=3  → chunk = text[3:7]   = "DEFG"  (moved by 4-1=3)
      Step 3: start=6  → chunk = text[6:10]  = "GHIJ"
      Step 4: start=9  → 9 >= len("ABCDEFGHIJ")=10? No, but text[9:13]="J" → still added
      Done!

    The step size is (chunk_size - overlap).
    Smaller step = more overlap = more chunks = better context preservation
    but also more storage and slower retrieval.
    """
    chunks = []

    # step = how far we move forward after each chunk
    # e.g. chunk_size=500, overlap=50 → step=450
    # so chunk 1 is chars 0-500, chunk 2 is chars 450-950 (shares 50 with chunk 1)
    step = chunk_size - overlap

    start = 0
    while start < len(text):
        end = start + chunk_size          # where this chunk ends
        chunk = text[start:end].strip()   # .strip() removes leading/trailing whitespace

        if chunk:                         # don't store empty chunks
            chunks.append(chunk)

        start += step                     # move forward by step size

    return chunks

# THE DEDUPLICATION FUNCTION

def make_chunk_id(source_filename: str, chunk_text: str) -> str:
    """
    Creates a unique, stable ID for a chunk.

    Why? If we ran embed.py twice on the same file, we don't want
    duplicate entries in ChromaDB. By hashing the content, we get
    the same ID for the same text — ChromaDB will just update it
    instead of creating a duplicate.

    hashlib.md5() creates a short fingerprint of any string.
    hexdigest() converts it to a readable hex string like "a3f9b2c1..."
    [:8] takes only the first 8 characters — enough to be unique
    """
    content_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
    # ID format: "k8s.txt_chunk_a3f9b2c1"
    return f"{source_filename}_chunk_{content_hash}"


# THE INGEST FUNCTION — reusable for any file

def ingest_file(filepath: str, collection) -> dict:
    """
    Reads a text file, chunks it, and stores it in ChromaDB.

    Returns a summary dict so the caller knows what happened.

    Why a function instead of just running code directly?
    Because in Step 3, we'll call this same function from our
    FastAPI /ingest endpoint when the user uploads a file via the UI.
    Reusable code = less duplication = fewer bugs.
    """

    # os.path.basename turns "/some/path/k8s.txt" → "k8s.txt"
    filename = os.path.basename(filepath)

    print(f"Reading {filename}...")

    # Read the full file content
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        print(f"WARNING: {filename} is empty, skipping.")
        return {"filename": filename, "chunks": 0, "status": "skipped"}

    print(f"File has {len(text)} characters")

    # Split into chunks
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # Build parallel lists for ChromaDB
    # ChromaDB's .add() takes three lists that must be the same length:
    #   ids        = ["id1", "id2", ...]        unique identifier per chunk
    #   documents  = ["text1", "text2", ...]    the actual chunk text
    #   metadatas  = [{"key": "val"}, ...]      extra info we can filter on later

    ids       = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = make_chunk_id(filename, chunk)

        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "source":      filename,   # which file this came from
            "chunk_index": i,          # which chunk number (0, 1, 2...)
            "total_chunks": len(chunks) # how many total chunks in this file
        })

    # Store in ChromaDB
    # .upsert() = "update if exists, insert if not"
    # This is how we handle deduplication — same ID = update, not duplicate
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Stored {len(chunks)} chunks from '{filename}' in ChromaDB")

    return {
        "filename":     filename,
        "chunks_stored": len(chunks),
        "status":       "success"
    }


# MAIN — runs when we execute: python embed.py

if __name__ == "__main__":
    """
    The   if __name__ == "__main__":   guard means:
      - This block runs ONLY when we directly run: python embed.py
      - It does NOT run when embed.py is imported by another file (like ingest.py)

    It keeps the script usable both
    as a standalone tool AND as an importable module.
    """

    # Connect to ChromaDB — same settings as app.py
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="docs",
        metadata={"hnsw:space": "cosine"}
    )

    print(f"Connected to ChromaDB at: {CHROMA_PATH}")
    print(f"Chunks before: {collection.count()}")

    # List of files to ingest — add more here as needed
    # Later, the UI's upload panel will call ingest_file() directly
    files_to_ingest = [
        "./k8s.txt",
    ]

    results = []
    for filepath in files_to_ingest:
        if os.path.exists(filepath):
            result = ingest_file(filepath, collection)
            results.append(result)
        else:
            print(f"WARNING: File not found: {filepath}")

    print(f"\nDone! Chunks after: {collection.count()}")
    print("\nSummary:")
    for r in results:
        print(f"  {r['filename']}: {r.get('chunks_stored', 0)} chunks ({r['status']})")