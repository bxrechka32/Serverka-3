"""
Скрипт создания таблицы users для задания 8.1.
Запуск: python task_8_1_init_db.py
"""

import sqlite3

DATABASE = "task_8_1.db"

conn = sqlite3.connect(DATABASE)
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

print("Таблица 'users' создана успешно.")
