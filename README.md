# RAG PDF Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that lets you upload a PDF and ask questions about its contents. The app extracts text from the PDF, splits it into overlapping chunks, embeds the chunks with a sentence-transformer model, retrieves the best matches with FAISS, and answers using Gemini as the language model.

## Overview

This project demonstrates a practical GenAI workflow in a compact app:

- Upload a PDF in the browser
- Extract the text page by page
- Chunk the document while keeping page metadata
- Embed chunks with `all-MiniLM-L6-v2`
- Search the most relevant passages with FAISS
- Send only the retrieved context to Gemini
- Return grounded answers with source page references

## Goals

- Accept a PDF upload and answer questions from it
- Keep answers grounded only in the document
- Refuse out-of-context questions politely
- Offer a simple Gradio interface for quick demos
- Run locally with free-tier-friendly tools

## Non-goals for v1

- Multi-PDF support
- Persistent user sessions
- OCR support for scanned PDFs
- Enterprise-scale security or multi-user auth
- Fine-tuning the model

## System architecture

```text
PDF upload
  |
  v
Extract text per page (pypdf)
  |
  v
Chunk text into overlapping blocks
  |
  v
Embed chunks with sentence-transformers
  |
  v
Store vectors in FAISS
  |
  v
User asks a question
  |
  v
Embed question and retrieve top-3 chunks
  |
  v
Prompt Gemini with context + question
  |
  v
Answer + page references
```

## Tech stack

- Python 3.10+
- `pypdf` for PDF text extraction
- `sentence-transformers` for embeddings
- `faiss-cpu` for vector search
- `google-genai` for Gemini
- `gradio` for the chat UI
- `python-dotenv` for local environment management

## Repository structure

```text
rag-pdf-chatbot/
  app.py
  rag.py
  requirements.txt
  README.md
  .gitignore
  .env.example
```

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create a Gemini API key at Google AI Studio.
5. Copy `.env.example` to `.env` and set your key.

```bash
copy .env.example .env
```

Then edit `.env`:

```env
GEMINI_API_KEY=your_key_here
```

## Run the app

```bash
python app.py
```

Open the local Gradio URL shown in the terminal, upload a PDF, and ask questions about it.

## Hugging Face Spaces deployment

1. Create a public Hugging Face Space.
2. Choose the Gradio SDK.
3. In the Space settings, add a secret named `GEMINI_API_KEY`.
4. Upload or push these files:
   - `app.py`
   - `rag.py`
   - `requirements.txt`
   - `.env.example` (optional for repo reference, not required on Spaces)
   - `sample.pdf` for testing
5. Keep the app running on port 7860, which is the default for Gradio on Spaces.

This project is already configured to run correctly in a Hugging Face Gradio Space with `server_name="0.0.0.0"` and `server_port=7860`.

## How it works

### 1. Load the PDF

The app reads every page using `pypdf` and keeps only pages with extracted text.

### 2. Chunk the text

Text is broken into chunks of roughly 800 characters with a 150-character overlap to preserve context across boundaries.

### 3. Embed and index

Each chunk is encoded with `all-MiniLM-L6-v2` and added to a FAISS index for semantic search.

### 4. Retrieve the most relevant passages

When the user asks a question, the app embeds the question and retrieves the top 3 chunks by similarity.

### 5. Generate the answer

The prompt includes:

- the retrieved document chunks
- the user question
- strict instructions to answer only from the context
- a fallback response when the answer is missing

## Example questions

- What is the main conclusion of the document?
- Which page describes the key assumptions?
- What are the payment terms mentioned in the report?
- Summarize the most important findings.

## Expected behavior

- If a question is covered by the document, the app answers using the relevant passages.
- If the answer is not present, the app responds with: `I could not find this in the document.`
- If the PDF has no extractable text, the app shows a friendly error message.
- If the API key is missing, the app explains the issue instead of crashing.

## Limitations

- This is designed for text-based PDFs, not scanned image-only PDFs.
- The state is kept in a module-level dictionary, which is acceptable for a demo but not production-grade session management.
- Query quality depends on the chunk size and the clarity of the document text.
- Gemini API quotas and rate limits may affect availability.

## Development notes

This repository follows the core flow described in the PRD:

- `rag.py` contains the indexing, retrieval, and generation logic
- `app.py` contains the Gradio interface and app wiring
- `.env.example` keeps the API key out of version control

## License

This project is available under the terms of the repository license.
