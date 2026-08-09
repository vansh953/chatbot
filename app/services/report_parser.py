import os

import pdfplumber


def extract_text_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def extract_text_from_image(path: str) -> str:
    """OCR for scanned/photographed reports. Requires system package `tesseract-ocr`
    and the `pytesseract` + `Pillow` pip packages (see requirements.txt).
    Returns an empty string gracefully if OCR isn't available, instead of crashing."""
    try:
        import pytesseract
        from PIL import Image

        return pytesseract.image_to_string(Image.open(path)).strip()
    except Exception:
        return ""


def extract_text(path: str, content_type: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if content_type == "application/pdf" or ext == ".pdf":
        return extract_text_from_pdf(path)
    if content_type and content_type.startswith("image/"):
        return extract_text_from_image(path)
    if ext in (".txt",):
        with open(path, "r", errors="ignore") as f:
            return f.read()
    return ""
