"""Auth utilities: JWT creation/validation and password hashing."""
import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "holkos-fatura-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    pwd = (password[:72] if len(password.encode("utf-8")) > 72 else password).encode("utf-8")
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd = (plain_password[:72] if len(plain_password.encode("utf-8")) > 72 else plain_password).encode("utf-8")
        return bcrypt.checkpw(pwd, hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_username_from_token(credentials) -> str | None:
    if not credentials or credentials.credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    if payload and "sub" in payload:
        return payload["sub"]
    return None
