"""
Задание 6.5 — JWT + регистрация + rate limiter (slowapi).
Запуск: uvicorn task_6_5:app --reload
"""

import jwt
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --------------- Настройка приложения ---------------

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests"},
    )


bearer_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "my-super-secret-jwt-key-6-5-32bytes!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# --------------- Модели ---------------

class UserRequest(BaseModel):
    username: str
    password: str


# --------------- In-memory БД ---------------

fake_users_db: dict[str, str] = {}  # username -> hashed_password


# --------------- Утилиты JWT ---------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# --------------- Эндпоинты ---------------

@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
def register(request: Request, user: UserRequest):
    # Проверяем, есть ли уже такой пользователь (через secrets.compare_digest)
    for existing_username in fake_users_db:
        if secrets.compare_digest(existing_username, user.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )
    fake_users_db[user.username] = pwd_context.hash(user.password)
    return {"message": "New user created"}


@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserRequest):
    # Ищем пользователя
    stored_hash: str | None = None
    found_username: str | None = None
    for existing_username, hashed_pw in fake_users_db.items():
        if secrets.compare_digest(existing_username, user.username):
            stored_hash = hashed_pw
            found_username = existing_username
            break

    if stored_hash is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not pwd_context.verify(user.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed",
        )

    access_token = create_access_token(data={"sub": found_username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected_resource")
def protected_resource(payload: dict = Depends(verify_token)):
    return {"message": "Access granted"}
