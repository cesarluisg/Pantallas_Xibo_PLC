import snap7
from snap7.util import get_string
import logging
import json
import os

# Constantes con los nombres de archivo para persistencia y configuración
ESTADO_FILE_NAME = "estado_actual.json"
PLCS_CONFIG_FILE_NAME = "plcs_config.json"

def leer_receta_desde_plc(ip, db_numero, db_offset, longitud):
    client = snap7.client.Client()
    try:
        client.connect(ip, 0, 1)
        if not client.get_connected():
            logging.warning(f"No se pudo conectar a PLC en {ip}")
            return None

        data = client.db_read(db_numero, db_offset, longitud)
        receta = get_string(data, 0)
        logging.info(f"Receta leída desde {ip}: {receta}")
        return receta
    except Exception as e:
        logging.warning(f"Error al conectar o leer desde {ip}: {e}")
        return None
    finally:
        try:
            client.disconnect()
        except Exception:
            pass

def cargar_estado_actual():
    if not os.path.exists(ESTADO_FILE_NAME):
        return {}
    try:
        with open(ESTADO_FILE_NAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"[ERROR] No se pudo leer {ESTADO_FILE_NAME}: {e}")
        return {}

def guardar_estado_actual(estado):
    try:
        with open(ESTADO_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"[ERROR] No se pudo guardar {ESTADO_FILE_NAME}: {e}")

def cargar_plcs_config():
    if not os.path.exists(PLCS_CONFIG_FILE_NAME):
        logging.error(f"[ERROR] No se encontró {PLCS_CONFIG_FILE_NAME}")
        return []
    try:
        with open(PLCS_CONFIG_FILE_NAME, 'r', encoding='utf-8') as f:
            plcs = json.load(f)
            logging.info(f"{len(plcs)} PLCs cargados desde {PLCS_CONFIG_FILE_NAME}.")
            return plcs
    except Exception as e:
        logging.exception(f"Error al cargar {PLCS_CONFIG_FILE_NAME}: {e}")
        return []