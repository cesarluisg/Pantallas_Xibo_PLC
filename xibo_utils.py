from datetime import datetime, timedelta
import requests
import logging

# Constantes para los endpoints de la API de Xibo
XIBO_AUTH_ENDPOINT = "/api/authorize/access_token"
XIBO_LAYOUT_ENDPOINT = "/api/layout"
XIBO_DISPLAYGROUP_ENDPOINT = "/api/displaygroup"
XIBO_SCHEDULE_ENDPOINT = "/api/schedule"

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
        response = requests.post(f"{base_url}{XIBO_AUTH_ENDPOINT}", data=payload)
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
        response = requests.get(f"{base_url}{XIBO_LAYOUT_ENDPOINT}", headers=headers)
        response.raise_for_status()
        layouts = response.json()

        logging.info("\nBuscando layout con los tags:")
        logging.info(f"  - Grupo de pantallas: {grupo_pantallas}")
        logging.info(f"  - Receta: {receta}")
        logging.info("-"*80)
        logging.info(f"{'ID':<6} {'Nombre':<35} {'CampaignID':<12} {'Tags'}")
        logging.info("-"*80)

        for layout in layouts:
            layout_id = layout.get("layoutId")
            layout_name = layout.get("layout")
            campaign_id = layout.get("campaignId")
            tags = [t['tag'] for t in layout.get("tags", [])]

            logging.info(f"{layout_id:<10} {campaign_id:<12} {layout_name:<35} {tags}")

            if grupo_pantallas in tags and receta in tags:
                logging.info("-"*80)
                logging.info(f"Layout seleccionado → LayoutID: {layout_id}  CampaignID: {campaign_id}  Nombre: '{layout_name}'")
                return campaign_id

        logging.info("-"*80)
        logging.info("No se encontró ningún layout con ambos tags.")
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

    # Paso 1: Buscar el ID del grupo de pantallas por nombre
    try:
        response = requests.get(f"{base_url}{XIBO_DISPLAYGROUP_ENDPOINT}", headers=headers)
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

    # Paso 2: Crear el evento "para siempre" (en este ejemplo, configurado para 1 año)
    from_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_dt = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "eventTypeId": 1,
        "isPriority": 0,
        "displayGroupIds": [grupo_id],
        "fromDt": from_dt,
        "toDt": to_dt,
        "isAlways": 1,
        "layoutId": layout_id,    # aunque en realidad se toma el campaignId
        "campaignId": layout_id,
    }

    try:
        response = requests.post(f"{base_url}{XIBO_SCHEDULE_ENDPOINT}", headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Evento creado: layout {layout_id} → grupo '{grupo_pantallas}' (ID {grupo_id})")
        return True
    except requests.exceptions.HTTPError as e:
        logging.error("Error al crear evento de layout.")
        logging.error(f"Status code: {response.status_code}")
        logging.error(f"Respuesta de Xibo: {response.text}")
        return False
    except Exception as e:
        logging.exception("Excepción inesperada al crear evento de layout.")
        return False

def esta_corriendo_layout_en_grupo_ahora(config, token, group_name, layout_id):
    """
    Verifica si en este momento (fecha/hora actual) hay un evento activo para el
    layout/campaign 'layout_id' en el grupo de pantallas 'group_name'.
    Usa el endpoint /api/schedule/{displayGroupId}/events?date=YYYY-MM-DD HH:MM:SS
    para que Xibo devuelva sólo los eventos vigentes a esa hora.
    """
    base_url = config['xibo']['base_url']
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 1) Obtener el displayGroupId según el nombre 'group_name'
    try:
        resp_grupos = requests.get(f"{base_url}/api/displaygroup", headers=headers)
        resp_grupos.raise_for_status()
        grupos = resp_grupos.json()

        grupo = next((g for g in grupos if g['displayGroup'] == group_name), None)
        if not grupo:
            logging.warning(f"No se encontró el grupo de pantallas con nombre: {group_name}")
            return False

        grupo_id = grupo['displayGroupId']
    except Exception as e:
        logging.exception("Error al buscar grupo de pantallas.")
        return False

    # 2) Llamar a /api/schedule/{displayGroupId}/events?date=YYYY-MM-DD HH:MM:SS con la hora actual
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"{base_url}/api/schedule/{grupo_id}/events"
    params = {"date": date_str}

    try:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()

        data = resp.json()
        # El JSON tiene la clave "events", que es la lista de eventos activos
        eventos = data.get("events", [])

        # 3) Si algún evento tiene eventTypeId=1 (layout) y campaignId=layout_id, está activo
        for ev in eventos:
            if ev.get("eventTypeId") == 1 and ev.get("campaignId") == layout_id:
                return True

        return False

    except Exception as e:
        logging.exception("Error al consultar eventos actuales para el grupo.")
        return False

def _convertir_a_datetime(valor):
    """
    Convierte un valor devuelto por Xibo en un objeto datetime.
    Puede ser int (timestamp) o str con formato "YYYY-MM-DD HH:MM:SS".
    Devuelve None si no se pudo parsear.
    """
    try:
        if isinstance(valor, int):
            # Interpretamos como timestamp UNIX
            return datetime.utcfromtimestamp(valor)
        elif isinstance(valor, str):
            # Interpretamos como string "YYYY-MM-DD HH:MM:SS"
            return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
        else:
            return None
    except:
        return None