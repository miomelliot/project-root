from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from models.logger_config import setup_logger
import time

logger = setup_logger()


# Middleware для логирования запросов
class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Логируем начало запроса
        logger.info(f"Входящий запрос: {request.method} {request.url} Headers: {dict(request.headers)}")
        # Обработка запроса
        response = await call_next(request)

        # Время обработки
        process_time = time.time() - start_time
        logger.info(f"Статус ответа: {
                    response.status_code} - Затраченное время: {process_time:.4f}s")

        return response
