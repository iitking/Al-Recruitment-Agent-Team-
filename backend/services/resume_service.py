import hashlib
import re
from pathlib import Path
from typing import Tuple, Optional
from pypdf import PdfReader
from docx import Document

class ResumeService:
    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def extract_text(file_path: Path, file_type: str) -> Tuple[str, Optional[str]]:
        """
        Extracts plain text from PDF, DOCX, or text files.
        Returns (extracted_text, error_message).
        """
        try:
            file_type = file_type.lower().strip(".")
            if file_type == "pdf":
                reader = PdfReader(str(file_path))
                text_parts = []
                for page_idx, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)
                full_text = "\n".join(text_parts).strip()
                if not full_text:
                    return "", "PDF contained no extractable text (may be scanned or image-only)."
                return ResumeService.sanitize_untrusted_input(full_text), None

            elif file_type in ("docx", "doc"):
                doc = Document(str(file_path))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                # Also include table text
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            paragraphs.append(row_text)
                full_text = "\n".join(paragraphs).strip()
                if not full_text:
                    return "", "DOCX contained no readable text."
                return ResumeService.sanitize_untrusted_input(full_text), None

            elif file_type in ("txt", "text", "md"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    full_text = f.read().strip()
                return ResumeService.sanitize_untrusted_input(full_text), None

            else:
                return "", f"Unsupported file extension: {file_type}. Supported: pdf, docx, txt."

        except Exception as e:
            return "", f"Error reading {file_type} file: {str(e)}"

    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        """
        Defensive prompt-injection mitigation:
        - Removes dangerous control tokens or system delimiters.
        - Trims excessive whitespace.
        - Neutralizes phrases attempting to overwrite prompt instructions.
        """
        if not text:
            return ""
        
        # Replace null bytes and non-printable control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Flag/neutralize overt system instruction overrides
        override_patterns = [
            r"ignore previous instructions",
            r"disregard all prior instructions",
            r"you are now in developer mode",
            r"system prompt override",
        ]
        for pattern in override_patterns:
            sanitized = re.sub(pattern, "[FLAGGED_OVERRIDE_ATTEMPT]", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()
