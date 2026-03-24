# Контрольная работа №3 — Технологии разработки серверных приложений

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Структура проекта

Каждое задание — отдельный файл, запускается независимо:

| Файл | Задание | Описание |
|------|---------|----------|
| `task_6_1.py` | 6.1 | HTTP Basic Auth, GET `/login` |
| `task_6_2.py` | 6.2 | Bcrypt-хеширование, Pydantic-модели, POST `/register` + GET `/login` |
| `task_6_3.py` | 6.3 | DEV/PROD управление документацией |
| `task_6_4.py` | 6.4 | JWT-аутентификация (PyJWT) |
| `task_6_5.py` | 6.5 | JWT + регистрация + rate limiter (slowapi) |
| `task_7_1.py` | 7.1 | RBAC (admin/user/guest) + JWT |
| `task_8_1.py` | 8.1 | SQLite, таблица users, POST `/register` |
| `task_8_1_init_db.py` | 8.1 | Скрипт инициализации БД |
| `task_8_2.py` | 8.2 | CRUD Todo с SQLite |

## Запуск

Каждое задание запускается отдельно:

```bash
# Задание 6.1
uvicorn task_6_1:app --reload

# Задание 6.2
uvicorn task_6_2:app --reload

# Задание 6.3 (DEV-режим)
MODE=DEV DOCS_USER=admin DOCS_PASSWORD=secret uvicorn task_6_3:app --reload

# Задание 6.3 (PROD-режим)
MODE=PROD uvicorn task_6_3:app --reload

# Задание 6.4
uvicorn task_6_4:app --reload

# Задание 6.5
uvicorn task_6_5:app --reload

# Задание 7.1
uvicorn task_7_1:app --reload

# Задание 8.1 (сначала создать таблицу)
python task_8_1_init_db.py
uvicorn task_8_1:app --reload

# Задание 8.2
uvicorn task_8_2:app --reload
```

## Тестирование ключевых эндпоинтов

### Задание 6.1

```bash
# Успешный логин
curl -u admin:secret http://localhost:8000/login

# Неверные данные
curl -u wrong:wrong http://localhost:8000/login
```

### Задание 6.2

```bash
# Регистрация
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"correctpass"}' \
  http://localhost:8000/register

# Логин
curl -u user1:correctpass http://localhost:8000/login

# Неверный пароль
curl -u user1:wrongpass http://localhost:8000/login
```

### Задание 6.3

```bash
# DEV: доступ к документации
curl -u admin:secret http://localhost:8000/docs

# PROD: документация недоступна
curl http://localhost:8000/docs  # 404
```

### Задание 6.4

```bash
# Логин (получение JWT)
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"securepassword123"}' \
  http://localhost:8000/login

# Доступ к защищённому ресурсу
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/protected_resource
```

### Задание 6.5

```bash
# Регистрация
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}' \
  http://localhost:8000/register

# Логин
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"qwerty123"}' \
  http://localhost:8000/login

# Защищённый ресурс
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/protected_resource
```

### Задание 7.1

```bash
# Регистрация с ролью admin
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"pass","role":"admin"}' \
  http://localhost:8000/register

# Логин
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"pass"}' \
  http://localhost:8000/login

# Создание ресурса (admin)
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title":"Test","content":"Hello"}' \
  http://localhost:8000/resources

# Чтение ресурсов
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/resources
```

### Задание 8.1

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"12345"}' \
  http://localhost:8000/register
```

### Задание 8.2

```bash
# Создать Todo
curl -X POST -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","description":"Milk, eggs, bread"}' \
  http://localhost:8000/todos

# Получить Todo
curl http://localhost:8000/todos/1

# Обновить Todo
curl -X PUT -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries","description":"Milk, eggs","completed":true}' \
  http://localhost:8000/todos/1

# Удалить Todo
curl -X DELETE http://localhost:8000/todos/1
```

## Переменные окружения

Для задания 6.3 используйте файл `.env` (см. `.env.example`):

- `MODE` — режим работы (`DEV` или `PROD`)
- `DOCS_USER` — логин для доступа к `/docs` (только DEV)
- `DOCS_PASSWORD` — пароль для доступа к `/docs` (только DEV)
