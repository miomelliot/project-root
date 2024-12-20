import os
import sys
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

def setup_logger():
    log_file_name = os.getenv("LOG_FILE_NAME", "app.log")
    rotation_size = os.getenv("LOG_ROTATION_SIZE", "50 MB")
    level = os.getenv("LOG_LEVEL", "INFO")
    retention_days = os.getenv("LOG_RETENTION_DAYS", "7 days")
    compression = os.getenv("LOG_COMPRESSION", "zip")

    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file_name)

    log_format = ("<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                  "<level>{level: <8}</level>| <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    logger.remove()
    logger.add(
        log_file_path,
        rotation=rotation_size,
        retention=retention_days,
        compression=compression,
        format=log_format,
        level=level
    )
    logger.add(sys.stderr, format=log_format, level="ERROR")
    return logger
