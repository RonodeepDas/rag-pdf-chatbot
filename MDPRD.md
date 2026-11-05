# MDPRD: RAG PDF Chatbot (Gemini Edition)

Estimated build time: about 2 hours.

Stack: Python, sentence-transformers, FAISS, Gemini free API, Gradio, Hugging Face Spaces.

## 1. Overview

A web app where a user uploads a PDF and asks questions about it. The app finds the most relevant passages in the PDF and sends only those passages, plus the question, to an LLM. The LLM answers strictly from that context, and says so when the answer is not in the document. This pattern is called Retrieval-Augmented Generation (RAG).

Why this project: it demonstrates GenAI, NLP and embeddings, prompt engineering, vector search, and deployment in one small, shippable artifact.

## 2. Goals and Non-Goals

### Goals

- Upload a PDF and chat with it in a browser.
- Answers grounded only in the PDF, with page references.
- Public live demo on Hugging Face Spaces and a clean GitHub repo.
- Works on free tiers only.

### Non-goals (v1)

- Multi-PDF libraries, user accounts, or persistent storage.
- OCR for scanned PDFs.
- Fine-tuning any model.
- Production-grade auth or scaling.

## 3. Users and Use Cases

- Student: uploads a textbook chapter and asks "What is the definition of X?"
- Professional: uploads a report or contract and asks "What are the payment terms?"
- Recruiter or reviewer: opens the demo link and judges the project in under two minutes.

## 4. Functional Requirements

| ID  | Requirement                                                                    | Priority |
| --- | ------------------------------------------------------------------------------ | -------- |
| F1  | Accept a PDF upload and extract text page by page                              | Must     |
| F2  | Split text into overlapping chunks, keeping page numbers as metadata           | Must     |
| F3  | Embed chunks with sentence-transformers and index them in FAISS                | Must     |
| F4  | For each question, retrieve the top 3 chunks by similarity                     | Must     |
| F5  | Prompt Gemini to answer only from the retrieved context                        | Must     |
| F6  | If the context lacks the answer, reply "I could not find this in the document" | Must     |
| F7  | Gradio chat UI with file upload and a status message                           | Must     |
| F8  | Show the source chunks or page numbers under each answer                       | Should   |
| F9  | Handle errors: empty PDF, no text layer, API failure, missing key              | Should   |
| F10 | Conversation memory for follow-up questions                                    | Could    |

## 5. Non-Functional Requirements

- Latency: answer in under 5 seconds for a typical PDF of 50 pages or fewer.
- Cost: zero. Embeddings run locally, the LLM uses the Gemini free tier.
- Security: API key stored as an environment variable or HF Space secret, never committed.
- Reproducibility: pinned requirements.txt, README with setup steps.

## 6. System Architecture

```text
PDF upload
   |
   v
Extract text per page (pypdf)
   |
   v
Chunk text (~800 chars, 150 overlap)
   |
   v
Embed chunks (all-MiniLM-L6-v2) --> FAISS index (in memory)

User question
   |
   v
Embed question --> FAISS top-3 search --> chunks + page numbers
   |
   v
Prompt = rules + context + question --> Gemini LLM
   |
   v
Answer + sources shown in Gradio
```

## 7. Tech Stack

| Layer        | Choice                                      | Reason                             |
| ------------ | ------------------------------------------- | ---------------------------------- |
| PDF parsing  | pypdf                                       | Simple, pure Python                |
| Embeddings   | sentence-transformers with all-MiniLM-L6-v2 | Small, fast, runs on CPU           |
| Vector store | faiss-cpu                                   | Standard, no server needed         |
| LLM          | Google Gemini via the google-genai SDK      | Free tier, fast                    |
| UI           | Gradio                                      | Native fit for Hugging Face Spaces |
| Hosting      | Hugging Face Spaces (Gradio SDK)            | Free, public link                  |

## 8. Repository Structure

```text
rag-pdf-chatbot/
  app.py              # Gradio UI and wiring
  rag.py              # load, chunk, embed, index, retrieve, generate
  requirements.txt
  README.md
  .gitignore          # include .env
  .env.example        # GEMINI_API_KEY=your_key_here
  sample.pdf          # small test document
```

## 9. Where to Start: Setup (about 15 minutes)

Create a GitHub repo named rag-pdf-chatbot and clone it.

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install pypdf sentence-transformers faiss-cpu google-genai gradio python-dotenv
pip freeze > requirements.txt
```

Get a free Gemini API key at aistudio.google.com/apikey: sign in with a Google account and click Create API key.

Create `.env` with `GEMINI_API_KEY=...` and add `.env` to `.gitignore`.

Put a small PDF (5 to 10 pages) in the repo as `sample.pdf` for testing.

## 10. Workflow and Time Plan

| Phase | Task                                     | Time   |
| ----- | ---------------------------------------- | ------ |
| 0     | Setup, key, sample PDF                   | 15 min |
| 1     | Load PDF and chunk                       | 20 min |
| 2     | Embed and index with FAISS               | 20 min |
| 3     | Retrieval                                | 10 min |
| 4     | Gemini call and prompt                   | 20 min |
| 5     | Gradio UI                                | 20 min |
| 6     | Deploy to Hugging Face Spaces and README | 15 min |

Build and test each phase in a Python script before moving on. Do not start the UI until the command-line version answers a question correctly.

## 11. Step-by-Step Implementation

### Phase 1: Load and chunk

```python
from pypdf import PdfReader

def load_pdf(path):
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i, "text": text})
    return pages

def chunk_pages(pages, size=800, overlap=150):
    chunks = []
    for p in pages:
        text, start = p["text"], 0
        while start < len(text):
            piece = text[start:start + size].strip()
            if piece:
                chunks.append({"page": p["page"], "text": piece})
            start += size - overlap
    return chunks
```

Check: print the number of chunks and read two of them. If you get zero, the PDF is probably scanned images and needs OCR (out of scope).

### Phase 2: Embed and index

```python
import numpy as np, faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_index(chunks):
    texts = [c["text"] for c in chunks]
    emb = model.encode(texts, normalize_embeddings=True)
    emb = np.asarray(emb, dtype="float32")
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    return index
```

### Phase 3: Retrieve top 3

```python
def retrieve(question, index, chunks, k=3):
    q = model.encode([question], normalize_embeddings=True)
    q = np.asarray(q, dtype="float32")
    scores, ids = index.search(q, k)
    return [chunks[i] for i in ids[0] if i != -1]
```

Check: ask a question you know the answer to and confirm the right page appears in the top 3.

### Phase 4: Prompt and Gemini call

```python
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM = (
    "You are a helpful assistant that answers questions about a document. "
    "Answer ONLY from the provided context. "
    "If the answer is not in the context, say: 'I could not find this in the document.' "
    "Be concise and mention page numbers when useful."
)

def answer(question, retrieved):
    context = "\n\n".join(f"[Page {c['page']}]\n{c['text']}" for c in retrieved)
    prompt = f"Context:\n{context}\n\nQuestion: {question}"
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            temperature=0.1,
        ),
    )
    return resp.text
```

Quick key test before wiring this in:

```bash
python -c "from google import genai; print(genai.Client(api_key='YOUR_KEY').models.generate_content(model='gemini-2.5-flash', contents='Say hi').text)"
```

If it prints a greeting, your key and model name work.

### Phase 5: Gradio UI (app.py)

```python
import gradio as gr
from dotenv import load_dotenv
load_dotenv()
from rag import load_pdf, chunk_pages, build_index, retrieve, answer

state = {"index": None, "chunks": None}

def process(file):
    if file is None:
        return "Please upload a PDF."
    pages = load_pdf(file.name if hasattr(file, "name") else file)
    if not pages:
        return "No extractable text found. The PDF may be scanned."
    state["chunks"] = chunk_pages(pages)
    state["index"] = build_index(state["chunks"])
    return f"Ready. Indexed {len(state['chunks'])} chunks from {len(pages)} pages."

def chat(message, history):
    if state["index"] is None:
        return "Upload and process a PDF first."
    try:
        hits = retrieve(message, state["index"], state["chunks"])
        reply = answer(message, hits)
        pages = sorted({h["page"] for h in hits})
        return f"{reply}\n\n*Sources: pages {', '.join(map(str, pages))}*"
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks() as demo:
    gr.Markdown("# Chat with your PDF")
    f = gr.File(label="Upload PDF", file_types=[".pdf"])
    status = gr.Textbox(label="Status", interactive=False)
    f.change(process, f, status)
    gr.ChatInterface(chat)

demo.launch()
```

Note: a module-level state dict is shared by every visitor. That is fine for a demo, but mention it in the README as a known limitation (use `gr.State` per session for a fix).

### Phase 6: Deploy to Hugging Face Spaces

Create a Hugging Face account and click New Space.

Choose Gradio as the SDK and Public visibility.

In the Space Settings > Variables and secrets, add `GEMINI_API_KEY` as a secret.

Push `app.py`, `rag.py`, and `requirements.txt` to the Space repo (via git or the web uploader). Leave out `.env`.

Wait for the build, then open the live URL and test with `sample.pdf`.

Push the same code to GitHub and add the Space link to the README.

## 12. Test Plan

| Test                                 | Expected result                         |
| ------------------------------------ | --------------------------------------- |
| Question clearly answered in the PDF | Correct answer with the right page      |
| Question not covered by the PDF      | "I could not find this in the document" |
| Empty or scanned PDF                 | Friendly error message                  |
| Missing or wrong API key             | Error shown, app does not crash         |
| Ask before uploading                 | Prompt to upload first                  |

Write 5 to 10 Q&A pairs for your sample PDF and check them manually. Put 2 or 3 of them in the README as examples.

## 13. Risks and Mitigations

| Risk                                        | Mitigation                                                          |
| ------------------------------------------- | ------------------------------------------------------------------- |
| Scanned PDF returns no text                 | Detect and show a message; list OCR as future work                  |
| Model hallucinates beyond context           | Strict system prompt, low temperature, show sources                 |
| Free API rate limits                        | Catch errors, show a retry message                                  |
| Slow first load on Spaces                   | Expected on first run; mention in README                            |
| Chunk too small or large gives poor answers | Tune size (500 to 1000) and overlap (100 to 200) on your sample PDF |
| Model name deprecated                       | Check the current model list in Google AI Studio                    |

## 14. Deliverables and Definition of Done

- GitHub repo with code, `requirements.txt`, `.gitignore`, `.env.example`
- README with overview, architecture diagram or description, setup, usage, example Q&A, limitations, and the live demo link
- Live Hugging Face Space that answers questions on an uploaded PDF
- Out-of-context questions are refused correctly
- No API keys in the repo history

## 15. Stretch Goals (after the 2 hours)

- Conversation memory for follow-up questions
- Multiple PDFs with per-file filtering
- Per-session state using `gr.State`
- Reranking with a cross-encoder for better retrieval
- Retrieval evaluation (hit rate on a small question set)
- OCR support for scanned PDFs
- Streaming responses

## 16. How to Present It (resume and interview)

One-line pitch: "Built a RAG chatbot that answers questions from PDFs using sentence-transformer embeddings, FAISS retrieval, and Google's Gemini LLM, deployed on Hugging Face Spaces."

Be ready to explain:

- why chunk overlap matters
- why normalized embeddings with inner product work
- what top-k controls
- how the prompt reduces hallucination
- the limitations you know about

---

Claude finished the response.
