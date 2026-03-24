"""
Задание 8.1 — SQLite, таблица users, POST /register (без SQLAlchemy).
Запуск:
  1. python task_8_1_init_db.py   (создать таблицу — один раз)
  2. uvicorn task_8_1:app --reload
"""

import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

DATABASE = "task_8_1.db"


class User(BaseModel):
    username: str
    password: str


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаём таблицу, если её ещё нет."""
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/register")
def register(user: User):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (user.username, user.password),
    )
    conn.commit()
    conn.close()
    return {"message": "User registered successfully!"}
