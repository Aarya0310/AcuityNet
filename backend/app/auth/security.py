import os
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

import jwt


ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 3600
_DEFAULT_JWT_SECRET = "dev-secret-key-at-least-32-chars-long!!!"


def jwt_secret() -> str:
    secret = os.environ.get("ACUITYNET_JWT_SECRET")
    if not secret:
        secret = os.environ.setdefault("ACUITYNET_JWT_SECRET", _DEFAULT_JWT_SECRET)
    return secret


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_hex, digest_hex = encoded.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expires = datetime.now(timezone.utc) + (expires_delta or timedelta(seconds=TOKEN_TTL_SECONDS))
    return jwt.encode({"sub": subject, "exp": expires}, jwt_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, jwt_secret(), algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid subject")
    return subject