import snap7
from snap7.util import get_string
import logging

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
        except:
            pass
