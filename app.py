import os

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from rag import answer, build_index, chunk_pages, load_pdf, retrieve

state = {"index": None, "chunks": []}


def process_pdf(file):
    if file is None:
        return "Please upload a PDF."

    file_path = file.name if hasattr(file, "name") else file
    pages = load_pdf(file_path)
    if not pages:
        return "No extractable text found. The PDF may be scanned or image-based."

    chunks = chunk_pages(pages)
    state["chunks"] = chunks
    state["index"] = build_index(chunks)
    return f"Ready. Indexed {len(chunks)} chunks from {len(pages)} pages."


def chat(message, history):
    if state["index"] is None:
        return "Upload and process a PDF first."

    try:
        hits = retrieve(message, state["index"], state["chunks"])
        if not hits:
            return "I could not find this in the document."

        reply = answer(message, hits)
        pages = sorted({chunk["page"] for chunk in hits})
        return f"{reply}\n\n*Sources: pages {', '.join(map(str, pages))}*"
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"


with gr.Blocks() as demo:
    gr.Markdown("# Chat with your PDF")
    file_input = gr.File(label="Upload PDF", file_types=[".pdf"])
    status = gr.Textbox(label="Status", interactive=False)
    file_input.change(process_pdf, file_input, status)
    gr.ChatInterface(fn=chat, title="PDF Assistant")


if __name__ == "__main__":
    demo.launch()
