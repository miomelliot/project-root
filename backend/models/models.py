from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
import enum

Base = declarative_base()
# Инициализация bcrypt контекста для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Модель для ответа с токеном
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Pydantic-модель для регистрации
class UserCreate(BaseModel):
    username: str
    password: str


# Модель для обновления пользователя
class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


# Pydantic-модель для валидации входа
class UserLogin(BaseModel):
    username: str
    password: str


# Перечисление для ролей пользователей
class UserRole(enum.Enum):
    admin = "admin"
    user = "user"


# Pydantic модель для представления пользователя
class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole

    class Config:
        from_attributes = True


# Модель создания пользователя
class UserCreateAdmin(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user


# Pydantic модель для обновления растения
class PlantUpdate(BaseModel):
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    rank: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    slug: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None


# Таблица растений
class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    trefle_id = Column(Integer, unique=True, nullable=False)
    scientific_name = Column(String(255), nullable=False)
    common_name = Column(String(255))
    family = Column(String(255))
    genus = Column(String(255))
    genus_id = Column(Integer)
    rank = Column(String(100))
    author = Column(String(255))
    bibliography = Column(Text)
    year = Column(Integer)
    slug = Column(String(255), nullable=False, unique=True)
    status = Column(String(100))
    image_url = Column(Text)
    plant_link = Column(Text)
    genus_link = Column(Text)
    self_link = Column(Text)

    # Связь с избранным
    favorites = relationship("Favorite", back_populates="plant", cascade="all, delete-orphan")


# Таблица пользователей
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)

    # Связь с избранным
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(password, self.password)

    def set_password(self, password: str):
        """Хеширование пароля"""
        self.password = pwd_context.hash(password)


# Таблица избранного
class Favorite(Base):
    __tablename__ = "favorites"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), primary_key=True)

    # Связь с растениями
    plant = relationship("Plant", back_populates="favorites")

    # Связь с пользователями
    user = relationship("User", back_populates="favorites")