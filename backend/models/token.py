import os
from datetime import datetime, timedelta
from loguru import logger
from fastapi import Depends, HTTPException, status, Form, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from models.models import User
from models.database import get_db
from passlib.context import CryptContext
from pydantic import BaseModel

# Загрузка переменных окружения
load_dotenv()

# Переменные JWT
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инструмент OAuth2 для Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Хэширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Роутер для /token
router = APIRouter()


# Модель для JWT респонса
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Создание JWT токена с ролью пользователя
@logger.catch
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Эндпоинт для генерации токена
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Проверка существования пользователя
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерация JWT токена
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


# Проверка токена и получение текущего пользователя
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Декодирование токена
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_role: str = payload.get("role")

        if user_id is None or user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Запрос к базе данных для поиска пользователя
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Добавление роли в возвращаемый объект пользователя
        user.role = user_role
        return user

    except JWTError as e:
        logger.error(f"Ошибка декодирования токена: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Хэширование пароля
def hash_password(password: str) -> str:
    """Хэширование пароля с использованием bcrypt."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


# Проверка пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнение хэшированного и plain паролей."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)
