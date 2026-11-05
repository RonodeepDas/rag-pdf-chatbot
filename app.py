import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from rag import answer, build_index, chunk_pages, load_pdf, retrieve

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="RAG PDF Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {"index": None, "chunks": []}


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_pdf(file: UploadFile = File(...)):
    if file.filename is None or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    upload_bytes = await file.read()
    if not upload_bytes:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

    temp_file = BASE_DIR / "temp_upload.pdf"
    temp_file.write_bytes(upload_bytes)

    try:
        pages = load_pdf(str(temp_file))
        if not pages:
            raise HTTPException(status_code=400, detail="No extractable text found. The PDF may be scanned or image-based.")

        chunks = chunk_pages(pages)
        state["chunks"] = chunks
        state["index"] = build_index(chunks)
        return {"message": "Ready", "pages": len(pages), "chunks": len(chunks)}
    finally:
        if temp_file.exists():
            temp_file.unlink()


@app.post("/api/ask")
def ask(payload: AskRequest):
    if state["index"] is None:
        raise HTTPException(status_code=400, detail="Upload and process a PDF first.")

    try:
        hits = retrieve(payload.question, state["index"], state["chunks"])
        if not hits:
            return {"answer": "I could not find this in the document.", "pages": []}

        response = answer(payload.question, hits)
        pages = sorted({chunk["page"] for chunk in hits})
        return {"answer": response, "pages": pages}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
