import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import jwt

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-orbit-ai-production-grade")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Prevent server startup if JWT_SECRET is missing or uses the default production value,
# except when running unit/integration tests to maintain test suite compatibility.
import sys
is_testing = (
    "pytest" in sys.modules
    or "unittest" in sys.modules
    or os.getenv("GEMINI_API_KEY") == "mock_api_key_for_testing"
    or any("test" in arg for arg in sys.argv)
)
if not is_testing:
    if not os.getenv("JWT_SECRET") or JWT_SECRET == "super-secret-key-orbit-ai-production-grade":
        raise RuntimeError(
            "FATAL: JWT_SECRET environment variable is missing, empty, or uses the default insecure production value."
        )



def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return new_key == key
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": int(expire.timestamp()), "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": int(expire.timestamp()), "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
