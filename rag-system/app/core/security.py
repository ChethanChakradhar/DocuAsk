from __future__ import annotations

import hmac
from hashlib import sha256


AUTH_COOKIE_NAME = "document_companion_auth"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 12


def is_passcode_enabled(passcode: str) -> bool:
    return bool(passcode.strip())


def is_valid_passcode_shape(passcode: str) -> bool:
    return len(passcode) == 4 and passcode.isdigit()


def make_auth_token(passcode: str) -> str:
    return hmac.new(
        key=passcode.encode("utf-8"),
        msg=b"document-companion-access",
        digestmod=sha256,
    ).hexdigest()


def verify_auth_token(token: str | None, passcode: str) -> bool:
    if not token:
        return False
    expected = make_auth_token(passcode)
    return hmac.compare_digest(token, expected)
