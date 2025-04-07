# plc_utils.py
import snap7
from snap7.util import get_string
import json
import os
import logging

class PLCManager:
    def __init__(self, config_path="plcs_config.json"):
        self.config_path = config_path
        self.plcs = self.cargar_plcs_config()

    def cargar_plcs_config(self):
        if not os.path.exists(self.config_path):
            logging.error(f"[ERROR] No se encontró {self.config_path}")
            return []
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                plcs = json.load(f)
                logging.info(f"{len(plcs)} PLCs cargados desde {self.config_path}.")
                return plcs
        except Exception as e:
            logging.exception(f"Error al cargar {self.config_path}: {e}")
            return []

    def leer_receta(self, plc):
        """
        Lee la receta de un PLC utilizando snap7.
        'plc' es un diccionario que debe incluir:
          - ip
          - db_numero
          - db_offset
          - longitud
          - nombre (identificador del PLC)
        """
        client = snap7.client.Client()
        try:
            client.connect(plc['ip'], 0, 1)
            if not client.get_connected():
                logging.warning(f"No se pudo conectar a PLC en {plc['ip']}")
                return None
            data = client.db_read(plc['db_numero'], plc['db_offset'], plc['longitud'])
            receta = get_string(data, 0)
            logging.info(f"Receta leída desde {plc['ip']}: {receta}")
            return receta
        except Exception as e:
            logging.warning(f"Error al conectar o leer desde {plc['ip']}: {e}")
            return None
        finally:
            try:
                client.disconnect()
            except Exception:
                pass

    def actualizar_estado(self, plc_name, nueva_receta, persistence_manager):
        """
        Carga el estado actual (la receta) del PLC usando persistence_manager,
        lo compara con la nueva receta y, si es distinto, actualiza únicamente ese registro.
        """
        receta_guardada = persistence_manager.cargar_estado_plc(plc_name)
        if receta_guardada != nueva_receta:
            logging.info(f"Receta cambiada para {plc_name} (anterior: {receta_guardada} => nueva: {nueva_receta}).")
            persistence_manager.guardar_estado_plc(plc_name, nueva_receta)
        else:
            logging.info(f"Receta sin cambios para {plc_name}.")
