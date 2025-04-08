print("Selector de Diapositiva según receta seleccionada en PLC")
print("Versión 1.0")
print("Desarrollado por: César Luis Guzmán - CICAL")
print("Fecha: 2025-03-24")

import time
import json

from plc_utils import PLCManager

from xibo_utils import XiboManager

from persis_utils import PersistenceManager

from logger_config import logger

from docker_restart import restart_xibo_containers


#logging.basicConfig(
#    level=logging.INFO,
#    format='%(asctime)s [%(levelname)s] %(message)s',
#    handlers=[
#        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
#        logging.StreamHandler()
#    ]
#)


def cargar_config():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logger.info("Configuración cargada correctamente.")
            return config
    except Exception as e:
        logger.exception("Error al cargar config.json")
        return None

def ciclo_de_lectura(plc_manager, persistence_manager, xibo_manager):
    # Obtener el token de Xibo
    token = xibo_manager.obtener_token()
    if not token:
        logger.error("No se pudo obtener el token de Xibo, abortando el ciclo.")
        return

    logger.info("Inicio de ciclo de lectura.")

    # Iterar sobre cada PLC configurado
    for plc in plc_manager.plcs:
        nombre = plc.get('nombre')
        grupo = plc.get('grupo_pantallas')
        logger.info(f"Procesando PLC: {nombre} (Grupo: {grupo})")

        # Leer la receta actual desde el PLC
        receta_actual = plc_manager.leer_receta(plc)
        logger.info(f"Receta actual en {nombre}: {receta_actual}")

        if not receta_actual:
            logger.warning(f"No se pudo obtener la receta para {nombre}")
            continue

        # Actualizar el estado del PLC individualmente usando PersistenceManager
        plc_manager.actualizar_estado(nombre, receta_actual, persistence_manager)

        # Consultar en Xibo el layout que tenga las etiquetas requeridas (grupo y receta)
        layout_id = xibo_manager.buscar_layout_por_etiquetas(grupo, receta_actual)
        if layout_id:
            if not xibo_manager.esta_corriendo_layout_en_grupo_ahora(grupo, layout_id):
                xibo_manager.crear_evento_layout_para_grupo(layout_id, grupo)
            else:
                logger.info(f"El layout/campaña {layout_id} ya está corriendo en el grupo '{grupo}'.")
        else:
            logger.warning(f"No se encontró layout para {nombre} con receta {receta_actual}.")

    logger.info("Ciclo de lectura terminado.")

def main():
    full_config = cargar_config()
    if not full_config:
        return

    persist_config = full_config.get("persistencia", {})
    xibo_config = full_config.get("xibo", {})
    intervalo = full_config.get("intervalo_segundos", 60)

    persistence_manager = PersistenceManager(persist_config)
    plc_manager = PLCManager("plcs_config.json")
    xibo_manager = XiboManager(xibo_config)

    #Reiniciar contenedor para que arranque bien
    logger.info("Reiniciando Contenedor Xibo")
    restart_xibo_containers()

    #esperar que arranque el contenedor
    logger.info("Esperando Reinicio de Contenedor Xibo")
    time.sleep(30)


    while True:
        try:
            ciclo_de_lectura(plc_manager, persistence_manager, xibo_manager)
        except Exception as e:
            logger.exception("Error durante el ciclo de lectura.")
        time.sleep(intervalo)

if __name__ == "__main__":
    main()