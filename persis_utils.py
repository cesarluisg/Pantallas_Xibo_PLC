# persis_utils.py
import os
import json
from logger_config import logger
from db_utils import get_db_connection

FILE_ESTADO = "plcs_estado.json"

class PersistenceManager:
    def __init__(self, persist_config):
        """
        Inicializa la capa de persistencia usando la configuración recibida.
        Se espera que persist_config tenga, por ejemplo:
          {
             "modo": "db",   # o "file"
             "db": { ... }   # si se usa el modo DB
          }
        """
        self.mode = persist_config.get("modo", "file")
        if self.mode == "db":
            self.db_config = persist_config.get("db", {})
        logger.info(f"Persistencia inicializada en modo: {self.mode}")

    def cargar_estado_plcs(self, valid_plcs):
        """
        Carga el estado de los PLCs. 'valid_plcs' es un conjunto de nombres válidos.
        Devuelve un diccionario { plc_name: receta }.
        """
        estado = {}
        if self.mode == "db":
            conn = get_db_connection(self.db_config)
            if not conn:
                logger.error("No se pudo conectar a la base de datos, se devuelve estado vacío.")
                return {}
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT plc_name, receta FROM plc_state")
                rows = cursor.fetchall()
                for plc_name, receta in rows:
                    if plc_name in valid_plcs:
                        estado[plc_name] = receta
            except Exception as e:
                logger.error(f"Error en la consulta a DB: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            if os.path.exists(FILE_ESTADO):
                try:
                    with open(FILE_ESTADO, "r", encoding="utf-8") as f:
                        estado = json.load(f)
                except Exception as e:
                    logger.error(f"Error al cargar archivo de estado: {e}")
        # Inicializa con None aquellos PLC válidos que no estén en el estado
        for plc in valid_plcs:
            if plc not in estado:
                estado[plc] = None
        return estado

    def guardar_estado_plcs(self, estado):
        """
        Guarda el estado completo de los PLCs.
        'estado' es un diccionario de la forma { plc_name: receta }.
        """
        if self.mode == "db":
            conn = get_db_connection(self.db_config)
            if not conn:
                logger.error("No se pudo conectar a la base de datos, no se guarda el estado.")
                return
            try:
                cursor = conn.cursor()
                for plc_name, receta in estado.items():
                    sql = """
                        INSERT INTO plc_state (plc_name, receta)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE receta = VALUES(receta)
                    """
                    cursor.execute(sql, (plc_name, receta))
                conn.commit()
            except Exception as e:
                logger.error(f"Error guardando en DB: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            try:
                with open(FILE_ESTADO, "w", encoding="utf-8") as f:
                    json.dump(estado, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error guardando en archivo: {e}")

    def guardar_estado_plc(self, plc_name, receta):
        """
        Actualiza únicamente el estado de un PLC (su receta).
        """
        if self.mode == "db":
            conn = get_db_connection(self.db_config)
            if not conn:
                logger.error("No se pudo conectar a la base de datos, no se actualiza el estado.")
                return
            try:
                cursor = conn.cursor()
                sql = """
                    INSERT INTO plc_state (plc_name, receta)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE receta = VALUES(receta)
                """
                cursor.execute(sql, (plc_name, receta))
                conn.commit()
            except Exception as e:
                logger.error(f"Error actualizando en DB: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            state = {}
            if os.path.exists(FILE_ESTADO):
                try:
                    with open(FILE_ESTADO, "r", encoding="utf-8") as f:
                        state = json.load(f)
                except Exception as e:
                    logger.error(f"Error al cargar archivo de estado: {e}")
            state[plc_name] = receta
            try:
                with open(FILE_ESTADO, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error guardando en archivo: {e}")

    def cargar_estado_plc(self, plc_name):
        """
        Carga el estado (la receta) de un único PLC dado su nombre.
        Devuelve la receta si existe o None en caso contrario.
        """
        if self.mode == "db":
            conn = get_db_connection(self.db_config)
            if not conn:
                logger.error("No se pudo conectar a la base de datos, se devuelve None.")
                return None
            try:
                cursor = conn.cursor()
                sql = "SELECT receta FROM plc_state WHERE plc_name = %s"
                cursor.execute(sql, (plc_name,))
                row = cursor.fetchone()
                return row[0] if row else None
            except Exception as e:
                logger.error(f"Error al cargar estado de DB para {plc_name}: {e}")
                return None
            finally:
                cursor.close()
                conn.close()
        else:
            if os.path.exists(FILE_ESTADO):
                try:
                    with open(FILE_ESTADO, "r", encoding="utf-8") as f:
                        state = json.load(f)
                        return state.get(plc_name, None)
                except Exception as e:
                    logger.error(f"Error al cargar estado del archivo para {plc_name}: {e}")
                    return None
            else:
                return None
