"""
Задание 7.1 — RBAC (управление доступом на основе ролей) + JWT.
Роли: admin, user, guest.
Запуск: uvicorn task_7_1:app --reload
"""

import jwt
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext

app = FastAPI()
bearer_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "my-super-secret-jwt-key-7-1-32bytes!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# --------------- Роли и разрешения ---------------

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


ROLE_PERMISSIONS = {
    Role.ADMIN: {"create", "read", "update", "delete"},
    Role.USER: {"read", "update"},
    Role.GUEST: {"read"},
}


# --------------- Модели ---------------

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Role = Role.GUEST


class LoginRequest(BaseModel):
    username: str
    password: str


class ResourceCreate(BaseModel):
    title: str
    content: str


class ResourceUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


# --------------- In-memory БД ---------------

users_db: dict[str, dict] = {}  # username -> {"hashed_password": ..., "role": ...}

resources_db: dict[int, dict] = {}
resource_counter = 0


# --------------- Утилиты JWT ---------------

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")
    if username is None or username not in users_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {"username": username, "role": users_db[username]["role"]}


# --------------- Фабрика зависимостей для проверки разрешений ---------------

def require_permission(permission: str):
    def checker(current_user: dict = Depends(get_current_user)):
        role = current_user["role"]
        if permission not in ROLE_PERMISSIONS.get(role, set()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' does not have '{permission}' permission",
            )
        return current_user
    return checker


# --------------- Эндпоинты: регистрация и логин ---------------

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    for existing in users_db:
        if secrets.compare_digest(existing, req.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    users_db[req.username] = {
        "hashed_password": pwd_context.hash(req.password),
        "role": req.role,
    }
    return {"message": "New user created", "role": req.role}


@app.post("/login")
def login(req: LoginRequest):
    stored: dict | None = None
    found_name: str | None = None
    for uname, udata in users_db.items():
        if secrets.compare_digest(uname, req.username):
            stored = udata
            found_name = uname
            break

    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not pwd_context.verify(req.password, stored["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")

    token = create_access_token(data={"sub": found_name, "role": stored["role"]})
    return {"access_token": token, "token_type": "bearer"}


# --------------- Защищённый ресурс (общий доступ для admin/user) ---------------

@app.get("/protected_resource")
def protected_resource(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    if role not in (Role.ADMIN, Role.USER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return {"message": f"Access granted for '{current_user['username']}' with role '{role}'"}


# --------------- CRUD-эндпоинты с проверкой ролей ---------------

@app.post("/resources", status_code=status.HTTP_201_CREATED)
def create_resource(
    resource: ResourceCreate,
    current_user: dict = Depends(require_permission("create")),
):
    global resource_counter
    resource_counter += 1
    resources_db[resource_counter] = {
        "id": resource_counter,
        "title": resource.title,
        "content": resource.content,
        "owner": current_user["username"],
    }
    return resources_db[resource_counter]


@app.get("/resources")
def list_resources(current_user: dict = Depends(require_permission("read"))):
    return list(resources_db.values())


@app.get("/resources/{resource_id}")
def get_resource(resource_id: int, current_user: dict = Depends(require_permission("read"))):
    if resource_id not in resources_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resources_db[resource_id]


@app.put("/resources/{resource_id}")
def update_resource(
    resource_id: int,
    resource: ResourceUpdate,
    current_user: dict = Depends(require_permission("update")),
):
    if resource_id not in resources_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    existing = resources_db[resource_id]
    if resource.title is not None:
        existing["title"] = resource.title
    if resource.content is not None:
        existing["content"] = resource.content
    return existing


@app.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    current_user: dict = Depends(require_permission("delete")),
):
    if resource_id not in resources_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    del resources_db[resource_id]
    return {"message": "Resource deleted successfully"}
