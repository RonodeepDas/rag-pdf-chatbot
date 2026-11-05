from rag import build_index, chunk_pages, load_pdf, retrieve


if __name__ == "__main__":
    pages = load_pdf("sample.pdf")
    chunks = chunk_pages(pages, size=200, overlap=50)
    index = build_index(chunks)
    hits = retrieve("What does the system use to find the most relevant passages?", index, chunks)
    print(f"pages={len(pages)}")
    print(f"chunks={len(chunks)}")
    print(f"hit_pages={[chunk['page'] for chunk in hits]}")
