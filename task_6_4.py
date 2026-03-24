"""
Задание 6.4 — JWT-аутентификация (PyJWT).
Запуск: uvicorn task_6_4:app --reload
"""

import jwt
import random
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()
bearer_scheme = HTTPBearer()

SECRET_KEY = "my-super-secret-jwt-key-needs-32-bytes!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# --------------- Модели ---------------

class LoginRequest(BaseModel):
    username: str
    password: str


# --------------- Функция-заглушка аутентификации ---------------

def authenticate_user(username: str, password: str) -> bool:
    """Заглушка — в реальном приложении проверяется по БД."""
    return random.choice([True, False])


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# --------------- Эндпоинты ---------------

@app.post("/login")
def login(request: LoginRequest):
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token}


@app.get("/protected_resource")
def protected_resource(payload: dict = Depends(verify_token)):
    return {"message": "Access granted"}
