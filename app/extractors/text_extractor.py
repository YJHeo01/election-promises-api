from pathlib import Path


class TextExtractor:
    """Extract text from downloaded official PDFs."""

    def extract_pdf_text(self, path: str | Path) -> list[dict[str, int | str]]:
        # TODO: Add OCR fallback for scanned PDFs.
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for PDF text extraction.") from exc

        document = fitz.open(str(path))
        pages: list[dict[str, int | str]] = []
        try:
            for page_index, page in enumerate(document, start=1):
                pages.append({"page": page_index, "text": page.get_text("text")})
        finally:
            document.close()
        return pages

