import json
from pathlib import Path
from typing import Tuple, Dict
import pdfplumber
from app.core.security import PrivacySanitizer, encrypt_credential

class ResumeService:
    @classmethod
    def extract_and_sanitize_pdf(
        cls,
        pdf_path: Path,
        candidate_name: str = "",
        university: str = ""
    ) -> Tuple[str, str, str, Dict[str, str]]:
        """从 PDF 简历提取纯文本并在本地执行严格脱敏

        Returns:
            (raw_text, masked_text, encrypted_token_map, token_map)
        """
        if str(pdf_path).lower().endswith(".txt"):
            with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read().strip()
        else:
            raw_pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        raw_pages.append(text)
            raw_text = "\n".join(raw_pages).strip()

        # 本地脱敏算子
        masked_text, token_map = PrivacySanitizer.sanitize_resume(
            raw_text=raw_text,
            candidate_name=candidate_name,
            university=university
        )

        # 加密序列化 token_map 供本地安全回填
        encrypted_token_map = encrypt_credential(json.dumps(token_map, ensure_ascii=False))

        return raw_text, masked_text, encrypted_token_map, token_map
