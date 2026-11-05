# RAG PDF Chatbot

A Retrieval-Augmented Generation (RAG) bot that answers questions from uploaded PDFs. It extracts text, splits it into chunks, embeds the chunks with a sentence-transformer model, searches the most relevant passages with FAISS, and uses Gemini to answer only from the retrieved document context.

## Overview

This project is designed for free deployment without paying for Hugging Face PRO. It uses a simple Python backend and a static frontend, so the app can be hosted on a free server while still keeping the Gemini API key secure on the backend.

## Architecture

```text
Browser frontend
   |
   v
Static HTML/JS upload form
   |
   v
FastAPI backend
   |
   v
PDF text extraction -> chunking -> vector search -> Gemini answer
```

## Features

- Upload a PDF from the browser
- Extract text page by page
- Split the document into overlapping chunks
- Search for the top passages with FAISS
- Answer only from the retrieved document context
- Show the source page numbers in the response
- No API key committed in the repo

## Tech stack

- Python
- FastAPI
- Uvicorn
- `pypdf`
- `sentence-transformers`
- `faiss-cpu`
- `google-genai`
- Static HTML/JS frontend

## Repo structure

```text
rag-pdf-chatbot/
  app.py              # FastAPI backend + static file server
  rag.py              # PDF loading, chunking, embedding, retrieval, generation
  static/
    index.html        # frontend page
    app.js            # UI logic
  requirements.txt
  README.md
  .env.example
  sample.pdf
```

## Local setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install requirements.

```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the template.

```bash
copy .env.example .env
```

Then add your key:

```env
GEMINI_API_KEY=your_key_here
```

4. Run the backend.

```bash
python app.py
```

5. Open the browser at:

```text
http://localhost:8000
```

## Free deployment options

This project is intentionally designed for free public deployment by splitting frontend and backend.

### Recommended free setup

- Frontend: static hosting or simple webpage served from the same backend
- Backend: Render, Railway, Fly.io, or another free Python host
- Secrets: store `GEMINI_API_KEY` in the host environment, not in the repo

## Example deployment flow

### Render

1. Push the repo to GitHub.
2. Create a new Web Service on Render.
3. Connect this repository.
4. Render will detect the included `render.yaml` config.
5. Add `GEMINI_API_KEY` as an environment variable.
6. Deploy the service.

The service will run with:

```bash
python app.py
```

7. Use the generated Render URL as the public app URL.

## Limitations

- This is built for text-based PDFs, not scanned image-only PDFs.
- The current app keeps one in-memory index per server instance.
- Query quality depends on the document content and chunk size.
- Gemini API quotas may affect availability.

## License

This project is available under the repository license.
