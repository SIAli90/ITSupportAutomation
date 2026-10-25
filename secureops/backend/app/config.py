import os


def database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./secure_it_ops.db")


def signing_key() -> str:
    key = os.getenv("JWT_SECRET", "")
    if len(key) < 32 or key.startswith("CHANGE_ME_"):
        raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    return key


def access_token_minutes() -> int:
    value = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    if not 1 <= value <= 1440:
        raise RuntimeError("ACCESS_TOKEN_MINUTES must be from 1 to 1440")
    return value
