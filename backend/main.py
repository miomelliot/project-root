import os
from fastapi.responses import FileResponse
import httpx
import random
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy.future import select
from models.log_middleware import LogMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from models.models import Favorite, Plant, PlantUpdate, UserCreate, UserCreateAdmin, UserLogin, UserOut, User
from models.token import create_access_token, get_current_user, verify_password, hash_password, router as token_router
from models.database import create_tables, get_db
from models.logger_config import setup_logger
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from loguru import logger

log = setup_logger()

# # Загрузка переменных окружения из файла .env
load_dotenv()

app = FastAPI(docs_url="/api/docs", redoc_url="/api/redoc")
app.include_router(token_router)

# Добавляем CORS middleware для разрешения запросов с других доменов
origins = [ 
    "https://greenbook.space", 
    "http://greenbook.space",
    "https://www.greenbook.space",  # Поддомен www
    "http://www.greenbook.space"   # Если используется HTTP для поддомена
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список допустимых источников
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP методы
    allow_headers=["*"],  # Разрешить все заголовки
)


TREFLE_API_KEY = os.getenv("TREFLE_API_KEY")
TREFLE_API_URL = "https://trefle.io/api/v1/plants"

# Добавляем middleware
app.add_middleware(LogMiddleware)


@app.get("/")
def root():
    return {"message": "Hello, World!"}

# Стартовая инициализация таблиц БД
@app.on_event("startup")
async def startup_event():
    await create_tables()


### --- ПОЛЬЗОВАТЕЛИ --- ###


# Регистрация пользователя с автоматической авторизацией
@logger.catch
@app.post("/api/register", response_model=dict)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверка на уникальность имени пользователя
    result = await db.execute(select(User).filter_by(username=user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Имя пользователя уже занято"
        )

    # Создание нового пользователя с хешированным паролем
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, password=hashed_password)
    db.add(new_user)
    await db.commit()

    # Генерация JWT токена
    access_token = create_access_token(
        data={"sub": str(new_user.id), "role": new_user.role.value}
    )

    # Возвращаем токен, тип токена и роль пользователя
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": new_user.role.value
    }


# Эндпоинт для авторизации
@logger.catch
@app.post("/api/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Проверка существования пользователя
    result = await db.execute(select(User).filter_by(username=user.username))
    db_user = result.scalars().first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    # Генерация токена с добавлением роли пользователя
    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role.value}


# Получить всех пользователей (только для администратора)
@logger.catch
@app.get("/api/admin/users")
async def get_all_users(user_type: str = "admin", db: AsyncSession = Depends(get_db)):
    if user_type != "admin":
        raise HTTPException(
            status_code=403, detail="Только администратор может выполнять данную операцию.")

    users_result = await db.execute(select(User).options(joinedload(User.favorites)))
    users = users_result.unique().scalars().all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "favorites": [favorite.plant_id for favorite in user.favorites],
        }
        for user in users
    ]


# Удалить пользователя по ID (только для администратора)
@logger.catch
@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, user_type: str = "admin", db: AsyncSession = Depends(get_db)):
    if user_type != "admin":
        raise HTTPException(
            status_code=403, detail="Только администратор может выполнять данную операцию.")

    # Проверка, существует ли пользователь
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    # Удаление пользователя
    await db.delete(user)
    await db.commit()

    return {"message": f"Пользователь с ID {user_id} успешно удален."}


# Создания пользователя с определением роли
@logger.catch
@app.post("/api/admin/create", response_model=UserOut)
async def create_user(user: UserCreateAdmin, db: AsyncSession = Depends(get_db)):
    # Проверка на уникальность имени
    result = await db.execute(select(User).filter_by(username=user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Имя пользователя уже занято"
        )
    # Хеширование пароля
    hashed_password = hash_password(user.password)
    # Создаем нового пользователя с указанной ролью
    new_user = User(username=user.username,
                    password=hashed_password,
                    role=user.role)
    db.add(new_user)
    await db.commit()
    return new_user


### --- РАСТЕНИЯ --- ###


# Проверка токена на валидность
@app.get("/api/check_token")
async def check_token():
    """Проверка токена на валидность"""
    async with httpx.AsyncClient() as client:
        try:
            # Делаем запрос к Trefle API с переданным токеном
            response = await client.get(TREFLE_API_URL, params={"token": TREFLE_API_KEY})

            # Если статус ответа не 200, токен неверен
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка проверки токена: {
                        response.status_code} - {response.text}"
                )

            # Если все хорошо, возвращаем успешный ответ
            return {"message": f"Токен действителен", "status_code": response.status_code}

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка при подключении к Trefle API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Неизвестная ошибка: {str(e)}"
            )


# Загрузка растений с пагинацией
@logger.catch
@app.get("/api/plants")
async def get_plants(
    offset: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """Загрузка растений с пагинацией"""
    log.info(f"offset: {offset} limit: {limit}")
    result = await db.execute(
        select(Plant).order_by(Plant.id).offset(offset).limit(limit)
    )
    plants = result.scalars().all()
    return plants


# Получение 5 случайных растений
@logger.catch
@app.get("/api/random_plants")
async def get_random_plants(db: AsyncSession = Depends(get_db)):
    """Получает случайные 5 растений с произвольной страницы API и сохраняет изображения локально"""
    try:
        async with httpx.AsyncClient() as client:
            # Случайная страница
            random_page = random.randint(1, 24468)

            # Запрос данных с этой страницы
            response = await client.get(
                TREFLE_API_URL,
                params={"page": random_page, "token": TREFLE_API_KEY},
            )

            if response.status_code != 200:
                log.error(f"Ошибка API: {response.status_code}")
                raise HTTPException(status_code=501, detail="Ошибка API")

            plants_data = response.json().get("data", [])
            added_plants = []
            image_dir = Path("./image")
            image_dir.mkdir(parents=True, exist_ok=True)

            # Разделяем растения на две группы: с изображениями и без
            plants_with_images = []
            plants_without_images = []

            for plant in plants_data:
                # Проверяем наличие растения в базе
                existing_plant = await db.execute(
                    select(Plant).where(Plant.trefle_id == plant["id"])
                )
                if existing_plant.scalar_one_or_none():
                    continue

                # Разделяем растения в зависимости от наличия изображения
                image_url = plant.get("image_url", "")
                if image_url:
                    plants_with_images.append(plant)
                else:
                    plants_without_images.append(plant)

            # Сначала обрабатываем растения с изображениями
            for plant in plants_with_images:
                image_url = plant.get("image_url", "")
                log.info(image_url)
                local_image_path = ""

                if image_url:
                    image_name = f"{plant['id']}.jpg"
                    local_image_path = image_dir / image_name

                    try:
                        headers = {
                            "Accept": "image/jpeg",  # Указание, что хотим получить изображение
                            "User-Agent": "Mozilla/5.0"
                        }
                        image_response = await client.get(image_url, headers=headers)

                        # Логирование статуса и заголовков
                        log.info(f"Попытка загрузки изображения {image_url} с статусом {image_response.status_code}")
                        log.debug(f"Заголовки ответа: {image_response.headers}")

                        content_type = image_response.headers.get(
                            "Content-Type", "")
                        log.debug(f"Content-Type: {content_type}")

                        # Проверка контента и сохранение изображения, несмотря на octet-stream
                        if image_response.status_code == 200:
                            if "image" in content_type or "octet-stream" in content_type:
                                with open(local_image_path, "wb") as img_file:
                                    img_file.write(image_response.content)
                                log.info(f"Изображение успешно сохранено: {local_image_path}")
                            else:
                                log.warning(f"Ошибка загрузки изображения {image_url}. Неверный Content-Type: {content_type}")
                                continue
                        else:
                            log.warning(f"Ошибка загрузки изображения {image_url}. Статус: {image_response.status_code}")
                    except httpx.RequestError as e:
                        log.error(f"Ошибка при запросе изображения {image_url}: {e}")
                    except Exception as e:
                        log.error(f"Неизвестная ошибка при загрузке изображения {image_url}: {str(e)}")

                # Создание нового растения с изображением
                new_plant = Plant(
                    trefle_id=plant["id"],
                    scientific_name=plant["scientific_name"],
                    common_name=plant.get(
                        "common_name", "Неизвестно") or plant["scientific_name"],
                    family=plant.get("family", "Неизвестно"),
                    genus=plant.get("genus", "Неизвестно"),
                    rank=plant.get("rank", "Неизвестно"),
                    author=plant.get("author", "Неизвестно"),
                    bibliography=plant.get("bibliography", "Неизвестно"),
                    year=plant.get("year", 0),
                    slug=plant["slug"],
                    status=plant.get("status", "Неизвестно"),
                    image_url=str(
                        local_image_path) if local_image_path else "",
                    plant_link=plant["links"].get("plant", ""),
                    genus_link=plant["links"].get("genus", ""),
                    self_link=plant["links"].get("self", ""),
                )

                # Сохраняем растение в БД
                db.add(new_plant)
                added_plants.append(new_plant)

                if len(added_plants) >= 5:
                    break

            # Если нам нужно добавить еще растения без изображений
            if len(added_plants) < 5:
                for plant in plants_without_images:
                    # Создание нового растения без изображения
                    new_plant = Plant(
                        trefle_id=plant["id"],
                        scientific_name=plant["scientific_name"],
                        common_name=plant.get(
                            "common_name", "Неизвестно") or plant["scientific_name"],
                        family=plant.get("family", "Неизвестно"),
                        genus=plant.get("genus", "Неизвестно"),
                        rank=plant.get("rank", "Неизвестно"),
                        author=plant.get("author", "Неизвестно"),
                        bibliography=plant.get("bibliography", "Неизвестно"),
                        year=plant.get("year", 0),
                        slug=plant["slug"],
                        status=plant.get("status", "Неизвестно"),
                        image_url="",  # Без изображения
                        plant_link=plant["links"].get("plant", ""),
                        genus_link=plant["links"].get("genus", ""),
                        self_link=plant["links"].get("self", ""),
                    )

                    # Сохраняем растение в БД
                    db.add(new_plant)
                    added_plants.append(new_plant)

                    if len(added_plants) >= 5:
                        break

            await db.commit()

            # Преобразуем данные в тот же формат, что и в API пагинации
            plants_response = [
                {
                    "id": plant.id,
                    "scientific_name": plant.scientific_name,
                    "common_name": plant.common_name,
                    "family": plant.family,
                    "genus": plant.genus,
                    "rank": plant.rank,
                    "author": plant.author,
                    "bibliography": plant.bibliography,
                    "year": plant.year,
                    "slug": plant.slug,
                    "status": plant.status,
                    "image_url": plant.image_url,
                    "plant_link": plant.plant_link,
                    "genus_link": plant.genus_link,
                    "self_link": plant.self_link,
                }
                for plant in added_plants
            ]

            return {
                "page": random_page,
                "message": "Растения успешно добавлены.",
                "plants": plants_response,
            }

    except Exception as e:
        log.error(f"Ошибка: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения случайных растений"
        )



# Добавление растения в избранное
@logger.catch
@app.post("/api/favorites/{id}")
async def add_to_favorites(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли растение
    plant = await db.execute(select(Plant).where(Plant.id == id))
    plant = plant.scalars().first()
    if not plant:
        raise HTTPException(status_code=404, detail="Растение не найдено")

    # Проверяем, есть ли оно уже в избранном
    favorite_check = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.plant_id == id
        )
    )
    if favorite_check.scalars().first():
        raise HTTPException(status_code=400, detail="Растение уже в избранном")

    # Добавляем в избранное
    new_favorite = Favorite(user_id=current_user.id, plant_id=id)
    db.add(new_favorite)
    await db.commit()
    return {"message": "Растение добавлено в избранное"}


# Удаление растения из избранного
@logger.catch
@app.delete("/api/favorites/{id}")
async def remove_from_favorites(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли запись в избранном
    favorite = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id, Favorite.plant_id == id
        )
    )
    favorite = favorite.scalars().first()
    if not favorite:
        raise HTTPException(
            status_code=404, detail="Растение отсутствует в избранном")

    # Удаляем из избранного
    await db.delete(favorite)
    await db.commit()
    return {"message": "Растение удалено из избранного"}


# Получить список избранного
@logger.catch
@app.get("/api/favorites")
async def get_favorite(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Запрашиваем список избранных растений с предварительной загрузкой
    result = await db.execute(
        select(Favorite)
        .options(joinedload(Favorite.plant))
        .where(Favorite.user_id == current_user.id)
    )
    favorites = result.scalars().all()

    # Формируем ответ с заполнением всех полей
    return [
        {
            "id": favorite.plant.id,
            "scientific_name": favorite.plant.scientific_name or 'Неизвестно',
            "common_name": favorite.plant.common_name or 'Неизвестно',
            "family": favorite.plant.family or 'Неизвестно',
            "genus": favorite.plant.genus or 'Неизвестно',
            "rank": favorite.plant.rank or '',
            "author": favorite.plant.author or '',
            "bibliography": favorite.plant.bibliography or '',
            "year": favorite.plant.year or 0,
            "image_url": favorite.plant.image_url or '',
        }
        for favorite in favorites
    ]


# Обновление данных растения
@logger.catch
@app.put("/api/plants/{id}", response_model=dict)
async def update_plant(
    id: int,
    plant_data: PlantUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Ищем растение в базе данных
    result = await db.execute(select(Plant).where(Plant.id == id))
    plant = result.scalars().first()

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Растение не найдено",
        )

    # Обновляем только переданные значения
    for key, value in plant_data.dict(exclude_unset=True).items():
        setattr(plant, key, value)

    # Сохраняем изменения
    await db.commit()
    await db.refresh(plant)

    return {"message": "Данные растения успешно обновлены"}


# Удаление растения по его ID с удалением связанного изображения
@logger.catch
@app.delete("/api/plants/{plant_id}", response_model=dict)
async def delete_plant(
    plant_id: int, db: AsyncSession = Depends(get_db)
):
    # Проверяем существование растения
    result = await db.execute(select(Plant).where(Plant.id == plant_id))
    plant = result.scalars().first()

    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Растение не найдено",
        )

    # Удаляем изображение, если оно существует
    if plant.image_url:
        image_path = plant.image_url
        if os.path.exists(image_path):
            os.remove(image_path)
            log.info(f"Изображение {image_path} удалено.")
        else:
            log.warning(f"Изображение {image_path} не найдено.")

    # Удаляем растение
    await db.delete(plant)
    await db.commit()

    return {"message": f"Растение с ID {plant_id} и его изображение удалено"}


# Очистка таблицы растений с каскадным удалением изображений
@logger.catch
@app.delete("/api/plants", response_model=dict)
async def delete_all_plants(
    db: AsyncSession = Depends(get_db)
):
    # Получаем все растения и их изображения
    result = await db.execute(select(Plant))
    plants = result.scalars().all()

    # Удаляем изображения каждого растения
    
    for plant in plants:
        if plant.image_url:
            image_path = plant.image_url
            if os.path.exists(image_path):
                os.remove(image_path)
                log.info(f"Изображение {image_path} удалено.")
            else:
                log.warning(f"Изображение {image_path} не найдено.")
            
    # Удаление всех растений
    await db.execute(delete(Plant))
    await db.commit()

    return {"message": "Все растения и их изображения удалены"}


# Отправить изображение
@logger.catch
@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    # Исправил на правильный путь к папке изображений
    image_path = os.path.join("image", image_name)
    log.info(f"Пытаемся вернуть изображение: {image_path}")

    if os.path.exists(image_path):
        # Возвращаем файл с правильным типом контента
        # Задайте нужный тип изображения, например "image/jpeg" или "image/png"
        return FileResponse(image_path, media_type="image/jpeg")
    else:
        # Если файл не найден, выбрасываем HTTPException с кодом 404
        raise HTTPException(status_code=404, detail="Image not found")
