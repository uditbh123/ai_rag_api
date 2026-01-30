from fastapi import FastAPI
import chromadb
import ollama

app = FastAPI()
chroma = chromadb.PersistentClient(path="./db")
collection = chroma.get_or_create_collection("docs")

@app.post("/query")
def query(q: str):
    results = collection.query(query_texts=[q], n_results=1)
    
    # NECESSARY CHANGE: Check if the inner list has the document
    # results["documents"] looks like [['actual text here']]
    if results["documents"] and len(results["documents"][0]) > 0:
        context = results["documents"][0][0]
    else:
        context = "No context found"

    answer = ollama.generate(
        model="tinyllama",
        prompt=f"Context:\n{context}\n\nQuestion: {q}\n\nAnswer clearly and concisely:"
    )
    
    return {
        "answer": answer["response"],
        "debug_context": context # This helps you see if the DB actually worked
    }