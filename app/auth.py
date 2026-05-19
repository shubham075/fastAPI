import base64
import hashlib
import hmac
import os
import secrets
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

COOKIE_NAME = "fastapi_crud_session"


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "change-this-secret-key")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return (
        base64.urlsafe_b64encode(salt).decode("ascii")
        + "$"
        + base64.urlsafe_b64encode(password_hash).decode("ascii")
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_text, hash_text = stored_hash.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected_hash = base64.urlsafe_b64decode(hash_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(actual_hash, expected_hash)


def create_session_token(user_id: int) -> str:
    message = str(user_id)
    signature = hmac.new(get_secret_key().encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{message}.{signature}"


def read_session_token(token: Optional[str]) -> Optional[int]:
    if not token or "." not in token:
        return None

    user_id_text, signature = token.split(".", 1)
    expected_signature = hmac.new(get_secret_key().encode("utf-8"), user_id_text.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        return int(user_id_text)
    except ValueError:
        return None
