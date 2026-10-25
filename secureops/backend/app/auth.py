"""Password storage, short-lived access tokens, and RBAC dependencies."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import access_token_minutes, signing_key
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        method, iterations, salt, expected = stored.split("$")
        if method != "pbkdf2_sha256" or not 100_000 <= int(iterations) <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": str(user.id), "iat": now, "nbf": now,
        "exp": now + timedelta(minutes=access_token_minutes()),
        "jti": secrets.token_hex(12),
    }, signing_key(), algorithm="HS256")


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauth = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    if not creds or creds.scheme.lower() != "bearer":
        raise unauth
    try:
        payload = jwt.decode(creds.credentials, signing_key(), algorithms=["HS256"])
        uid = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise unauth from None
    user = db.get(User, uid)
    if user is None:
        raise unauth
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
