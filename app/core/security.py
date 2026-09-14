import re
import base64
import hashlib
from typing import Tuple, Dict
from cryptography.fernet import Fernet

def _get_derived_key() -> bytes:
    """基于固定盐与系统标识派生本地安全密钥"""
    seed = "campus-job-agent-local-secret-salt-2026"
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

_CIPHER = Fernet(_get_derived_key())

def encrypt_credential(plain_text: str) -> str:
    """加密本地敏感凭据 (如 SMTP 授权码, API Key)"""
    if not plain_text:
        return ""
    return _CIPHER.encrypt(plain_text.encode("utf-8")).decode("utf-8")

def decrypt_credential(cipher_text: str) -> str:
    """解密本地敏感凭据"""
    if not cipher_text:
        return ""
    try:
        return _CIPHER.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""

class PrivacySanitizer:
    """本地隐私脱敏沙箱算子 (Local Privacy Sandbox Engine)

    采用精确正则与占位符映射机制:
    真实姓名 -> [CANDIDATE_NAME]
    手机号   -> [PHONE_1]
    电子邮箱 -> [EMAIL_1]
    院校名称 -> [UNIVERSITY_1]

    外发至 LLM 前执行脱敏; 界面渲染或生成最终建议时由本地映射表反向回填。
    """

    PHONE_PATTERN = re.compile(r'(?<!\d)(?:(?:\+86)|(?:86))?1[3-9]\d{9}(?!\d)')
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    ID_CARD_PATTERN = re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)')

    @classmethod
    def sanitize_resume(
        cls,
        raw_text: str,
        candidate_name: str = "",
        university: str = ""
    ) -> Tuple[str, Dict[str, str]]:
        token_map = {}
        sanitized = raw_text

        # 1. 脱敏身份证号
        id_matches = cls.ID_CARD_PATTERN.findall(sanitized)
        for idx, item in enumerate(set(id_matches), start=1):
            token = f"[ID_CARD_{idx}]"
            token_map[token] = item
            sanitized = sanitized.replace(item, token)

        # 2. 脱敏手机号
        phone_matches = cls.PHONE_PATTERN.findall(sanitized)
        for idx, item in enumerate(set(phone_matches), start=1):
            token = f"[PHONE_{idx}]"
            token_map[token] = item
            sanitized = sanitized.replace(item, token)

        # 3. 脱敏邮箱
        email_matches = cls.EMAIL_PATTERN.findall(sanitized)
        for idx, item in enumerate(set(email_matches), start=1):
            token = f"[EMAIL_{idx}]"
            token_map[token] = item
            sanitized = sanitized.replace(item, token)

        # 4. 脱敏真实姓名
        if candidate_name and len(candidate_name.strip()) >= 2:
            name = candidate_name.strip()
            token = "[CANDIDATE_NAME]"
            token_map[token] = name
            sanitized = sanitized.replace(name, token)

        # 5. 脱敏大学院校
        if university and len(university.strip()) >= 3:
            uni = university.strip()
            token = "[UNIVERSITY_1]"
            token_map[token] = uni
            sanitized = sanitized.replace(uni, token)

        return sanitized, token_map

    @classmethod
    def restore_text(cls, sanitized_text: str, token_map: Dict[str, str]) -> str:
        """根据脱敏字典还原文本"""
        restored = sanitized_text
        for token, real_val in token_map.items():
            restored = restored.replace(token, real_val)
        return restored
