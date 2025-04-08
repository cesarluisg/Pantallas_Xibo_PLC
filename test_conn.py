import faulthandler
faulthandler.enable()

import mysql.connector
import logging

logging.basicConfig(level=logging.INFO)

try:
    conn = mysql.connector.connect(
        host="localhost",
        port=3308,
        user="cms",
        password="Rubol-1234!",
        database="xibo_app",
        charset='utf8mb4'
    )
    logging.info("Conexión a la base de datos establecida correctamente.")
except BaseException as e:
    logging.error(f"Error: {e}")
