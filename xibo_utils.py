import time
import requests
import logging

def obtener_token_xibo(config):
    base_url = config['xibo']['base_url']
    client_id = config['xibo']['client_id']
    client_secret = config['xibo']['client_secret']

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        response = requests.post(f"{base_url}/api/authorize/access_token", data=payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        logging.info("Token de Xibo obtenido correctamente.")
        return token
    except Exception as e:
        logging.exception("Error al obtener el token de Xibo.")
        return None

def buscar_layout_por_etiquetas(config, token, grupo_pantallas, receta):
    base_url = config['xibo']['base_url']
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(f"{base_url}/api/layout", headers=headers)
        response.raise_for_status()
        layouts = response.json()

        for layout in layouts:
            tags = [t['tag'] for t in layout.get("tags", [])]
            if grupo_pantallas in tags and receta in tags:

                logging.info(f"Layout encontrado: ID {layout['layoutId']} - {layout['layout']}")
                return layout["layoutId"]

        logging.warning(f"No se encontró layout con tags: {grupo_pantallas} y {receta}")
        return None

    except Exception as e:
        logging.exception("Error al buscar layouts en Xibo.")
        return None

def crear_evento_layout_para_grupo(config, token, layout_id, grupo_pantallas):
    base_url = config['xibo']['base_url']
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Paso 1: buscar el ID del grupo de pantallas por nombre
    try:
        response = requests.get(f"{base_url}/api/displaygroup", headers=headers)
        response.raise_for_status()
        grupos = response.json()
        grupo = next((g for g in grupos if g['displayGroup'] == grupo_pantallas), None)

        if not grupo:
            logging.warning(f"No se encontró el grupo de pantallas con nombre: {grupo_pantallas}")
            return False

        grupo_id = grupo['displayGroupId']
    except Exception as e:
        logging.exception("Error al buscar grupo de pantallas.")
        return False

    # Paso 2: crear el evento "para siempre"
    payload = {
        "eventTypeId": 1,  # Evento de tipo layout
        "isPriority": 0,
        "displayGroupIds": [grupo_id],
        "fromDt": 0,
        "toDt": 2147483647,
        "isAlways": 1,
        "layoutId": layout_id
    }

    try:
        response = requests.post(f"{base_url}/api/schedule", headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Evento creado: layout {layout_id} → grupo '{grupo_pantallas}' (ID {grupo_id})")
        return True
    except Exception as e:
        logging.exception("Error al crear evento de layout.")
        return False
