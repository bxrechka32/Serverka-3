"""
Задание 6.2 — Хеширование паролей (passlib + bcrypt), Pydantic-модели, /register и /login.
Запуск: uvicorn task_6_2:app --reload
"""

import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from passlib.context import CryptContext

app = FastAPI()
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --------------- Pydantic-модели ---------------

class UserBase(BaseModel):
    username: str


class User(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


# --------------- In-memory БД ---------------

fake_users_db: dict[str, UserInDB] = {}


# --------------- Зависимость аутентификации ---------------

def auth_user(credentials: HTTPBasicCredentials = Depends(security)) -> UserInDB:
    # Ищем пользователя, сравнивая username через secrets.compare_digest
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


# --------------- Эндпоинты ---------------

@app.post("/register")
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    hashed_password = pwd_context.hash(user.password)
    user_in_db = UserInDB(username=user.username, hashed_password=hashed_password)
    fake_users_db[user.username] = user_in_db
    return {"message": f"User '{user.username}' registered successfully"}


@app.get("/login")
def login(user: UserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}
