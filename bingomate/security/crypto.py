from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class MemoryCipher:
    prefix = "enc:v1:"

    def __init__(self, secret: str) -> None:
        if not secret.strip():
            raise ValueError("Memory encryption secret cannot be empty.")
        self._fernet = Fernet(_derive_fernet_key(secret.strip()))

    def encrypt_text(self, value: str) -> str:
        token = self._fernet.encrypt(value.encode("utf-8")).decode("ascii")
        return f"{self.prefix}{token}"

    def decrypt_text(self, value: str) -> str:
        if not value.startswith(self.prefix):
            return value
        token = value[len(self.prefix) :].encode("ascii")
        try:
            return self._fernet.decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt memory with the configured key.") from exc


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)
