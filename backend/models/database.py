import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

# Загрузка переменных окружения из файла .env
load_dotenv()

# Строка подключения к базе данных из .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Асинхронный движок базы данных
engine = create_async_engine(DATABASE_URL, echo=True)

# Сессия для работы с базой данных
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Создание таблиц и начальной записи (root user)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Получение сессии
async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session  # Возвращаем сессию
    finally:
        await session.close()  # Закрываем сессию
