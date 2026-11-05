from pathlib import Path


def escape_pdf_text(value: str) -> str:
    return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def build_page_stream(lines):
    chunks = []
    for line in lines:
        chunks.append(f'({escape_pdf_text(line)}) Tj 0 -18 Td')
    content = 'BT /F1 12 Tf 72 720 Td ' + ' '.join(chunks) + ' ET'
    return content


page_one = [
    'AI Research Summary',
    'This document explains how a PDF chatbot answers questions from a document.',
    'The system uses embeddings and FAISS to find the most relevant passages.'
]

page_two = [
    'Deployment Notes',
    'The app uploads a PDF, indexes the text, and then answers with page references.',
    'The answer is grounded only in the retrieved context from the document.'
]

page_streams = [
    build_page_stream(page_one),
    build_page_stream(page_two),
]

objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 7 0 R >> >> >>',
    f'<< /Length {len(page_streams[0].encode("latin-1"))} >>\nstream\n{page_streams[0]}\nendstream',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 7 0 R >> >> >>',
    f'<< /Length {len(page_streams[1].encode("latin-1"))} >>\nstream\n{page_streams[1]}\nendstream',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
]

pdf = '%PDF-1.4\n'
offsets = [0]
for i, obj in enumerate(objects, start=1):
    offsets.append(len(pdf.encode('latin-1')))
    pdf += f'{i} 0 obj\n{obj}\nendobj\n'

xref_offset = len(pdf.encode('latin-1'))
pdf += f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'
for off in offsets[1:]:
    pdf += f'{off:010d} 00000 n \n'

pdf += f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n'

Path('sample.pdf').write_bytes(pdf.encode('latin-1'))
print('Created sample.pdf')
