from pathlib import Path

from pypdf import PdfReader


def load_document(file_path):
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            pages.append(f"[Page {page_number}]\n{page.extract_text() or ''}")
        return "\n\n".join(pages)

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported document type: {suffix}")
