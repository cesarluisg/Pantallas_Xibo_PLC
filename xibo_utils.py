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
            tags = layout.get("tags", [])
            if grupo_pantallas in tags and receta in tags:
                logging.info(f"Layout encontrado: ID {layout['layoutId']} - {layout['name']}")
                return layout["layoutId"]

        logging.warning(f"No se encontró layout con tags: {grupo_pantallas} y {receta}")
        return None

    except Exception as e:
        logging.exception("Error al buscar layouts en Xibo.")
        return None

def asignar_layout_a_grupo(config, token, layout_id, display_group_id):
    base_url = config['xibo']['base_url']
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "eventTypeId": 1,
        "isPriority": 0,
        "displayGroupIds": [display_group_id],
        "fromDt": int(time.time()),
        "toDt": int(time.time()) + 10 * 365 * 24 * 60 * 60,
        "layoutId": layout_id
    }

    try:
        response = requests.post(f"{base_url}/api/schedule", headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Layout {layout_id} asignado al grupo {display_group_id} con reproducción infinita.")
        return True
    except Exception as e:
        logging.exception("Error al asignar layout a grupo.")
        return False
