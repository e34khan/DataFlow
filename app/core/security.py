from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings


# bcrypt ignores/rejects input beyond 72 bytes; truncate explicitly so behavior is predictable
# rather than silently dependent on the installed bcrypt version.
def _truncate_for_bcrypt(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(_truncate_for_bcrypt(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_truncate_for_bcrypt(plain_password), hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
    return payload.get("sub")
