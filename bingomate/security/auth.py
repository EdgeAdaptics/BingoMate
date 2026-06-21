from __future__ import annotations

import secrets


class LocalAuth:
    def __init__(self, token: str = "") -> None:
        self.token = token.strip()

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    def verify(self, authorization: str | None = None, header_token: str | None = None) -> bool:
        if not self.enabled:
            return True
        candidate = self._extract_bearer_token(authorization) or (header_token or "").strip()
        return bool(candidate) and secrets.compare_digest(candidate, self.token)

    @staticmethod
    def _extract_bearer_token(authorization: str | None) -> str:
        if not authorization:
            return ""
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() != "bearer":
            return ""
        return value.strip()
