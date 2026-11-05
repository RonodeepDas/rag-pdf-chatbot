import os
from typing import Any, Iterable, List

import faiss
import numpy as np
from google import genai
from google.genai.errors import APIError
from google.genai import types
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-3.5-flash-lite"
FALLBACK_LLM_MODEL = "gemini-3.8-flash"
TRANSIENT_GEMINI_CODES = {429, 500, 502, 503, 504}

model = SentenceTransformer(MODEL_NAME)


def load_pdf(path: str) -> List[dict[str, Any]]:
    """Return a list of pages with extracted text."""
    reader = PdfReader(path)
    pages: List[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": page_number, "text": text})
    return pages


def chunk_pages(pages: Iterable[dict[str, Any]], size: int = 800, overlap: int = 150) -> List[dict[str, Any]]:
    """Split text into overlapping chunks while preserving page numbers."""
    chunks: List[dict[str, Any]] = []
    for page in pages:
        text = page["text"]
        start = 0

        while start < len(text):
            piece = text[start : start + size].strip()
            if piece:
                chunks.append({"page": page["page"], "text": piece})
            if len(piece) < size:
                break
            start += size - overlap
    return chunks


def build_index(chunks: List[dict[str, Any]]) -> faiss.IndexFlatIP:
    if not chunks:
        raise ValueError("No chunks available to build the index.")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def retrieve(question: str, index: faiss.IndexFlatIP, chunks: List[dict[str, Any]], k: int = 3) -> List[dict[str, Any]]:
    if not chunks:
        return []

    query_embedding = model.encode([question], normalize_embeddings=True, convert_to_numpy=True)
    query_embedding = np.asarray(query_embedding, dtype="float32")
    top_k = min(k, len(chunks))
    scores, ids = index.search(query_embedding, top_k)

    results: List[dict[str, Any]] = []
    for score, item_id in zip(scores[0], ids[0]):
        if item_id == -1:
            continue
        results.append(chunks[int(item_id)])
    return results


def answer(question: str, retrieved: List[dict[str, Any]]) -> str:
    if not retrieved:
        return "I could not find this in the document."

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to your environment or .env file.")

    client = genai.Client(api_key=api_key)
    context = "\n\n".join(f"[Page {chunk['page']}]\n{chunk['text']}" for chunk in retrieved)
    system_instruction = (
        "You are a helpful assistant that answers questions about a document. "
        "Answer ONLY from the provided context. "
        "If the answer is not in the context, say: 'I could not find this in the document.' "
        "Be concise and mention page numbers when useful."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
    )
    contents = f"Context:\n{context}\n\nQuestion: {question}"

    for model_name in (LLM_MODEL, FALLBACK_LLM_MODEL):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return response.text
        except APIError as exc:
            if model_name == FALLBACK_LLM_MODEL or exc.code not in TRANSIENT_GEMINI_CODES:
                raise
