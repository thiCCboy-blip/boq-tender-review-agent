from pypdf import PdfWriter

from document_loader import load_document


def test_load_text_document():
    text = load_document("data/sample_tender.txt")

    assert "TENDER SPECIFICATION" in text


def test_load_pdf_document(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as file:
        writer.write(file)

    assert load_document(pdf_path) == "[Page 1]\n"


def test_load_document_rejects_unsupported_type(tmp_path):
    file_path = tmp_path / "sample.docx"
    file_path.write_text("test", encoding="utf-8")

    try:
        load_document(file_path)
    except ValueError as error:
        assert "Unsupported document type" in str(error)
    else:
        raise AssertionError("Expected unsupported document type to fail")
