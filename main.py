print("Selector de Diapositiva según receta seleccionada en PLC")
print("Versión 1.0")
print("Desarrollado por: César Luis Guzmán - CICAL")
print("Fecha: 2025-03-24")

import time
import json
import logging
import snap7
from snap7.util import get_string

# Configuración del log
log_file = 'main.log'

file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler]
)

def cargar_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logging.info("Configuración cargada correctamente.")
            return config
    except Exception as e:
        logging.exception("Error al cargar config.json")
        return None

def cargar_plcs_config():
    try:
        with open('plcs_config.json', 'r', encoding='utf-8') as f:
            plcs = json.load(f)
            logging.info(f"{len(plcs)} PLCs cargados desde plcs_config.json.")
            return plcs
    except Exception as e:
        logging.exception("Error al cargar plcs_config.json")
        return []

def leer_receta_desde_plc(ip, db_numero, db_offset, longitud):
    client = snap7.client.Client()
    try:
        client.connect(ip, 0, 1)
        if not client.get_connected():
            logging.warning(f"No se pudo conectar a PLC en {ip}")
            return None
        
        data = client.db_read(db_numero, db_offset, longitud)
        receta = get_string(data, 0, longitud)
        logging.info(f"Receta leída desde {ip}: {receta}")
        return receta
    except Exception as e:
        logging.warning(f"Error al conectar o leer desde {ip}: {e}")
        return None
    finally:
        try:
            client.disconnect()
        except:
            pass

def ciclo_de_lectura(config, lista_plcs):
    logging.info("Inicio de ciclo de lectura.")
    for plc in lista_plcs:
        nombre = plc['nombre']
        ip = plc['ip']
        grupo = plc['grupo_pantallas']
        db = plc['db_numero']
        offset = plc['db_offset']
        longitud = plc['longitud']

        logging.info(f"Procesando {nombre} en {ip} (grupo {grupo})")
        receta = leer_receta_desde_plc(ip, db, offset, longitud)
        if receta:
            logging.info(f"Receta activa en {nombre}: {receta}")
        else:
            logging.warning(f"No se pudo obtener la receta de {nombre}")
    logging.info("Ciclo de lectura terminado.")

def main():
    config = cargar_config()
    if not config:
        return

    intervalo = config.get("intervalo_segundos", 60)
    lista_plcs = cargar_plcs_config()

    while True:
        try:
            ciclo_de_lectura(config, lista_plcs)
        except Exception as e:
            logging.exception("Error durante el ciclo de lectura.")
        time.sleep(intervalo)

if __name__ == "__main__":
    main()