print("Selector de Diapositiva según receta seleccionada en PLC")
print("Versión 1.0")
print("Desarrollado por: César Luis Guzmán - CICAL")
print("Fecha: 2025-03-24")

import time
import json
import logging

from plc_utils import (
    leer_receta_desde_plc, 
    cargar_estado_actual, 
    guardar_estado_actual, 
    cargar_plcs_config)

from xibo_utils import (
    obtener_token_xibo, 
    buscar_layout_por_etiquetas, 
    crear_evento_layout_para_grupo,
    esta_corriendo_layout_en_grupo_ahora
)

# Configuración del log: se escribe en archivo y también se muestra por consola
LOG_FILE = 'main.log'
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler]
)
# Agregar handler para consola si se desea:
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logging.getLogger().addHandler(console_handler)

def cargar_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logging.info("Configuración cargada correctamente.")
            return config
    except Exception as e:
        logging.exception("Error al cargar config.json")
        return None

def ciclo_de_lectura(config, lista_plcs):
    token = obtener_token_xibo(config)
    if not token:
        return

    estado = cargar_estado_actual()
    logging.info("Inicio de ciclo de lectura.")

    for plc in lista_plcs:
        nombre = plc['nombre']
        ip = plc['ip']
        grupo = plc['grupo_pantallas']
        db = plc['db_numero']
        offset = plc['db_offset']
        longitud = plc['longitud']

        logging.info(f"Procesando {nombre} en {ip} (grupo {grupo})")
        receta_actual = leer_receta_desde_plc(ip, db, offset, longitud)
        if not receta_actual:
            logging.warning(f"No se pudo obtener la receta de {nombre}")
            continue

        logging.info(f"Receta activa en {nombre}: {receta_actual}")
        receta_guardada = estado.get(nombre)

        if receta_guardada == receta_actual:
            # La receta no cambió, verificar si el evento está programado
            logging.info(f"Receta sin cambios para {nombre}. Verificando si existe evento...")
            layout_id = buscar_layout_por_etiquetas(config, token, grupo, receta_actual)
            if layout_id:
                # Revisar si ya hay un evento para este layout y grupo
                if esta_corriendo_layout_en_grupo_ahora(config, token, grupo, layout_id):
                    logging.info(f"El layout/campaña {layout_id} ya está corriendo en el grupo '{grupo}'.")
                else:
                    logging.info(f"No está corriendo. Creando evento...")
                    crear_evento_layout_para_grupo(config, token, layout_id, grupo)

            else:
                logging.warning(f"No se encontró layout para {nombre} con receta {receta_actual}.")
        else:
            # Cambió la receta, creamos el evento y actualizamos el estado
            logging.info(f"Receta cambiada para {nombre} (anterior: {receta_guardada} => nueva: {receta_actual}).")
            layout_id = buscar_layout_por_etiquetas(config, token, grupo, receta_actual)
            if layout_id:
                crear_evento_layout_para_grupo(config, token, layout_id, grupo)
                estado[nombre] = receta_actual
                guardar_estado_actual(estado)
            else:
                logging.warning(f"No se encontró layout para {nombre} con receta {receta_actual}.")

    logging.info("Ciclo de lectura terminado.")

def main():
    config = cargar_config()
    if not config:
        return

    intervalo = config.get("intervalo_segundos", 60)
    plcs = cargar_plcs_config()

    while True:
        try:
            ciclo_de_lectura(config, plcs)
        except Exception as e:
            logging.exception("Error durante el ciclo de lectura.")
        time.sleep(intervalo)

if __name__ == "__main__":
    main()