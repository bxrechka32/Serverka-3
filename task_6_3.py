"""
Задание 6.3 — Управление документацией (DEV/PROD), защита /docs базовой аутентификацией.
Запуск:
  DEV:  MODE=DEV DOCS_USER=admin DOCS_PASSWORD=secret uvicorn task_6_3:app --reload
  PROD: MODE=PROD uvicorn task_6_3:app --reload
"""

import os
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext

# Пытаемся загрузить .env (если есть python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MODE = os.getenv("MODE", "DEV").upper()
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "password")

if MODE not in ("DEV", "PROD"):
    raise ValueError(f"Invalid MODE: '{MODE}'. Allowed values: DEV, PROD")

# --------------- Настройка FastAPI в зависимости от MODE ---------------

if MODE == "PROD":
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
else:
    # DEV — отключаем стандартные docs, будем делать кастомные
    app = FastAPI(docs_url=None, redoc_url=None)

security_basic = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------- Pydantic-модели (из 6.2) ---------------

class UserBase(BaseModel):
    username: str


class User(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


fake_users_db: dict[str, UserInDB] = {}


# --------------- Auth зависимость для пользовательского API ---------------

def auth_user(credentials: HTTPBasicCredentials = Depends(security_basic)) -> UserInDB:
    user: UserInDB | None = None
    for stored_username, stored_user in fake_users_db.items():
        if secrets.compare_digest(credentials.username, stored_username):
            user = stored_user
            break

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user


# --------------- Auth зависимость для документации (DEV) ---------------

def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security_basic)):
    correct_user = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_pass = secrets.compare_digest(credentials.password, DOCS_PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid docs credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# --------------- Кастомные маршруты документации (DEV) ---------------

if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="Docs")

    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi(credentials: HTTPBasicCredentials = Depends(verify_docs_credentials)):
        return app.openapi()


# --------------- PROD: 404 на docs (уже отключены через FastAPI params) ---------------
# FastAPI автоматически вернёт 404 при docs_url=None, redoc_url=None, openapi_url=None


# --------------- Бизнес-эндпоинты ---------------

@app.post("/register")
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = pwd_context.hash(user.password)
    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db[user.username] = user_in_db
    return {"message": f"User '{user.username}' registered successfully"}


@app.get("/login")
def login(user: UserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}
