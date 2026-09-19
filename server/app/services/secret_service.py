import os
import re
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.secret import Secret

class SecretManager:
    """
    AES-256-GCM Zero-Trust Cryptographic Vault Service.
    - Master key generated and persisted in /etc/deploy/master.key
    - Per-project derived keys via PBKDF2-HMAC-SHA256
    - Fresh 96-bit cryptographic nonce for every single secret entry
    - Authenticated encryption with Associated Data (AEAD) bound to project ID
    """

    def __init__(self, key_path: Path | None = None):
        self.key_path = key_path or settings.MASTER_KEY_FILE
        self.master_key = self._load_or_create_master_key()

    def _load_or_create_master_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            return self.key_path.read_bytes()
        
        # Generate fresh 256-bit (32 bytes) master key
        new_key = os.urandom(32)
        self.key_path.write_bytes(new_key)
        try:
            if os.name != "nt":
                os.chmod(self.key_path, 0o400) # Read-only for owner
        except Exception:
            pass
        return new_key

    def _derive_project_key(self, project_id: str) -> bytes:
        """Derives a dedicated 256-bit key per project using PBKDF2-HMAC-SHA256."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=project_id.encode("utf-8"),
            iterations=100_000,
        )
        return kdf.derive(self.master_key)

    def encrypt(self, project_id: str, plaintext: str) -> tuple[str, str]:
        """
        Encrypts a secret using AES-256-GCM.
        Returns (ciphertext_hex, nonce_hex).
        """
        project_key = self._derive_project_key(project_id)
        aesgcm = AESGCM(project_key)
        
        # 96-bit (12 bytes) fresh nonce
        nonce = os.urandom(12)
        associated_data = project_id.encode("utf-8")
        
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data)
        return ciphertext.hex(), nonce.hex()

    def decrypt(self, project_id: str, ciphertext_hex: str, nonce_hex: str) -> str:
        """
        Decrypts an AES-256-GCM ciphertext.
        Raises InvalidTag if data has been altered, corrupted, or replayed across projects.
        """
        project_key = self._derive_project_key(project_id)
        aesgcm = AESGCM(project_key)
        
        nonce = bytes.fromhex(nonce_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        associated_data = project_id.encode("utf-8")
        
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return decrypted_bytes.decode("utf-8")

    async def get_decrypted_env_list(self, project_id: str, db: AsyncSession) -> list[str]:
        """
        In-Memory Process Environment Injection (EPIC-04 / Task 4.3).
        Decrypts secrets in volatile RAM and formats as ["KEY=VALUE", ...].
        Zero disk writes, zero temp files.
        """
        result = await db.execute(select(Secret).where(Secret.project_id == project_id))
        secrets = result.scalars().all()

        env_list = []
        for s in secrets:
            try:
                decrypted_val = self.decrypt(project_id, s.encrypted_value, s.nonce)
                env_list.append(f"{s.key}={decrypted_val}")
            except InvalidTag:
                continue
        return env_list

class SecretRedactor:
    """
    Streaming Log Secret Masking & Redaction Engine (Task 4.4).
    Intercepts logs before persistence or streaming and scrubs all
    known project secrets and standard credential patterns.
    """

    PATTERNS = [
        re.compile(r"ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), # JWT token
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"), # GitHub Token
        re.compile(r"AKIA[0-9A-Z]{16}"), # AWS Access Key
        re.compile(r"(?:postgres|mysql|redis|mongodb):\/\/[^:\s]+:([^@\s]+)@"), # Database URLs with passwords
    ]

    @classmethod
    def redact(cls, text: str, sensitive_values: list[str] | None = None) -> str:
        if not text:
            return ""

        redacted = text

        # 1. Redact project-specific known secrets
        if sensitive_values:
            for val in sensitive_values:
                if val and len(val) >= 4: # Only mask meaningful length strings
                    redacted = redacted.replace(val, "[REDACTED]")

        # 2. Redact standard token patterns
        for pattern in cls.PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)

        return redacted

secret_manager = SecretManager()
