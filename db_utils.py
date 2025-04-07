# db_utils.py
import mysql.connector
import logging

def get_db_connection(config):
    """
    Devuelve una conexión a la base de datos MySQL usando los datos
    en config['db'].
    """
    try:
        conn = mysql.connector.connect(
            host=config["db"]["host"],
            user=config["db"]["user"],
            password=config["db"]["password"],
            database=config["db"]["database"]
        )
        return conn
    except Exception as e:
        logging.error(f"Error al conectar con la base de datos: {e}")
        return None

def cargar_estado_actual(config, plcs_validos):
    """
    Lee de la tabla plc_state las recetas guardadas para cada PLC.
    Devuelve un dict con la forma { plc_name: receta }.
    Sólo devuelve los PLC que estén en la lista/conjunto plcs_validos.
    """
    conn = get_db_connection(config)
    if not conn:
        logging.error("No se pudo obtener conexión a la base de datos. Se devuelve estado vacío.")
        return {}

    estado = {}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT plc_name, receta FROM plc_state")
        rows = cursor.fetchall()

        for (plc_name, receta) in rows:
            # Filtrar para que solo cargue PLCs válidos
            if plc_name in plcs_validos:
                estado[plc_name] = receta
    except Exception as e:
        logging.error(f"Error al consultar la tabla plc_state: {e}")
    finally:
        cursor.close()
        conn.close()

    # Inicializar con None aquellos PLC válidos que no están en la BD
    for plc in plcs_validos:
        if plc not in estado:
            estado[plc] = None

    return estado

def guardar_estado_actual(config, estado):
    """
    Guarda el estado de cada PLC en la tabla plc_state.  
    `estado` es un dict { plc_name: receta }.
    Utiliza un 'upsert' para que si el registro existe, lo actualice,
    y si no existe, lo inserte.
    """
    conn = get_db_connection(config)
    if not conn:
        logging.error("No se pudo obtener conexión a la base de datos. No se guarda el estado.")
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
        logging.error(f"Error al guardar estado en la tabla plc_state: {e}")
    finally:
        cursor.close()
        conn.close()
