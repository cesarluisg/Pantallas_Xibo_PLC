# logger_config.py
import logging
from custom_logger import setup_custom_logger

# Configuración del log: se escribe en archivo y también se muestra por consola
LOGGER_NAME = "Logger"
LOG_FILE_BASE = 'main.log'
MAX_FILE_SIZE_BYTES = 1024 * 1024


# Configura el logger una sola vez y lo exporta
logger = setup_custom_logger(LOGGER_NAME, LOG_FILE_BASE, max_bytes=MAX_FILE_SIZE_BYTES, level=logging.DEBUG)
