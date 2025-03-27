print("Selector de Diapositiva según receta seleccionada en PLC")
print("Versión 1.0")
print("Desarrollado por: César Luis Guzmán - CICAL")
print("Fecha: 2025-03-24")

import time
import json
import logging

from plc_utils import leer_receta_desde_plc
from xibo_utils import obtener_token_xibo, buscar_layout_por_etiquetas, asignar_layout_a_grupo

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

def ciclo_de_lectura(config, lista_plcs):
    token = obtener_token_xibo(config)
    if not token:
        return

    logging.info("Inicio de ciclo de lectura.")
    for plc in lista_plcs:
        nombre = plc['nombre']
        ip = plc['ip']
        grupo = plc['grupo_pantallas']
        db = plc['db_numero']
        offset = plc['db_offset']
        longitud = plc['longitud']
        display_group_id = plc.get('xibo_display_group_id')

        logging.info(f"Procesando {nombre} en {ip} (grupo {grupo})")
        receta = leer_receta_desde_plc(ip, db, offset, longitud)
        if receta:
            logging.info(f"Receta activa en {nombre}: {receta}")
            layout_id = buscar_layout_por_etiquetas(config, token, grupo, receta)
            if layout_id and display_group_id:
                asignar_layout_a_grupo(config, token, layout_id, display_group_id)
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