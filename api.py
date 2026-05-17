from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import threading

from main import AnalystChatbot

app = FastAPI(title="AuxoAI Financial Analyst API")

# Global state for indexing
indexing_complete = False
chatbot = None

def run_indexing():
    global chatbot, indexing_complete
    
    if os.getenv("SKIP_INGESTION") == "true":
        print("⚡ SKIP_INGESTION is true. Initializing chatbot and skipping indexing...")
        chatbot = AnalystChatbot()
        indexing_complete = True
        return
        
    print("🚀 Background indexing started...")
    chatbot = AnalystChatbot()
    if chatbot.retriever.bm25 is not None:
        print("✅ Pre-built BM25 index found. Skipping document ingestion entirely to start instantly!")
    else:
        print("📝 No pre-built BM25 index found. Running local ingestion...")
        chatbot.ingest_documents()
    indexing_complete = True
    print("✅ Background indexing finished!")

# Start indexing in a separate thread immediately
threading.Thread(target=run_indexing, daemon=True).start()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.get("/api/status")
async def get_status():
    return {"status": "ready" if indexing_complete else "indexing"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not indexing_complete:
        return {"answer": "I am still indexing the financial documents. Please give me a minute to finish processing the reports!"}
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        response = chatbot.chat(request.query)
        if response.get("file_path"):
            filename = os.path.basename(response["file_path"])
            response["file_url"] = f"/api/files/{filename}"
        else:
            response["file_url"] = None
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(os.getcwd(), "output", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)

# Serve the Vite build
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
