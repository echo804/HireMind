import hashlib
from pathlib import Path


def parse_file(file_path: str) -> tuple[str, str]:
    """Parse resume file and return (text_content, content_hash)"""
    path = Path(file_path)
    ext = path.suffix.lower()
    text = ""

    if ext == ".pdf":
        import fitz
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    elif ext == ".docx":
        from docx import Document
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    text = text.strip()
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    return text, content_hash
