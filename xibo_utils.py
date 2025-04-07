# xibo_utils.py
from datetime import datetime, timedelta
import requests
from logger_config import logger

class XiboManager:
    def __init__(self, xibo_config):
        """
        Inicializa el administrador de Xibo usando la configuración recibida.
        Se espera que xibo_config tenga las claves:
          - base_url
          - client_id
          - client_secret
        """
        self.base_url = xibo_config.get("base_url")
        self.client_id = xibo_config.get("client_id")
        self.client_secret = xibo_config.get("client_secret")
        self.token = None  # Se actualizará al obtenerlo
        # Endpoints
        self.AUTH_ENDPOINT = "/api/authorize/access_token"
        self.LAYOUT_ENDPOINT = "/api/layout"
        self.DISPLAYGROUP_ENDPOINT = "/api/displaygroup"
        self.SCHEDULE_ENDPOINT = "/api/schedule"
        logger.info("XiboManager inicializado.")

    def obtener_token(self):
        """
        Obtiene y almacena en self.token el token de acceso a Xibo.
        """
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(f"{self.base_url}{self.AUTH_ENDPOINT}", data=payload)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            logger.info("Token de Xibo obtenido correctamente.")
            return self.token
        except Exception as e:
            logger.exception("Error al obtener el token de Xibo.")
            return None

    def buscar_layout_por_etiquetas(self, grupo_pantallas, receta):
        """
        Busca un layout que tenga entre sus etiquetas tanto el grupo de pantallas como la receta.
        Devuelve el campaignId del layout si lo encuentra, o None en caso contrario.
        """
        if not self.token:
            logger.error("Token no disponible para buscar layouts.")
            return None

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(f"{self.base_url}{self.LAYOUT_ENDPOINT}", headers=headers)
            response.raise_for_status()
            layouts = response.json()

            logger.info("Buscando layout con los tags:")
            logger.info(f"  - Grupo de pantallas: {grupo_pantallas}")
            logger.info(f"  - Receta: {receta}")
            logger.info("-" * 80)

            for layout in layouts:
                layout_id = layout.get("layoutId")
                layout_name = layout.get("layout")
                campaign_id = layout.get("campaignId")
                tags = [t['tag'] for t in layout.get("tags", [])]

                logger.info(f"LayoutID: {layout_id}, CampaignID: {campaign_id}, Nombre: {layout_name}, Tags: {tags}")

                if grupo_pantallas in tags and receta in tags:
                    logger.info("-" * 80)
                    logger.info(f"Layout seleccionado → LayoutID: {layout_id}  CampaignID: {campaign_id}  Nombre: '{layout_name}'")
                    return campaign_id

            logger.info("-" * 80)
            logger.info("No se encontró ningún layout con ambos tags.")
            return None

        except Exception as e:
            logger.exception("Error al buscar layouts en Xibo.")
            return None

    def crear_evento_layout_para_grupo(self, layout_id, grupo_pantallas):
        """
        Crea un evento para el layout (campaign) especificado en el grupo de pantallas dado.
        """
        if not self.token:
            logger.error("Token no disponible para crear evento.")
            return False

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Paso 1: Buscar el ID del grupo de pantallas
        try:
            response = requests.get(f"{self.base_url}{self.DISPLAYGROUP_ENDPOINT}", headers=headers)
            response.raise_for_status()
            grupos = response.json()
            grupo = next((g for g in grupos if g['displayGroup'] == grupo_pantallas), None)

            if not grupo:
                logger.warning(f"No se encontró el grupo de pantallas con nombre: {grupo_pantallas}")
                return False

            grupo_id = grupo['displayGroupId']
        except Exception as e:
            logger.exception("Error al buscar grupo de pantallas.")
            return False

        # Paso 2: Crear el evento "para siempre" (configurado, por ejemplo, para 1 año)
        from_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        to_dt = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "eventTypeId": 1,
            "isPriority": 0,
            "displayGroupIds": [grupo_id],
            "fromDt": from_dt,
            "toDt": to_dt,
            "isAlways": 1,
            "layoutId": layout_id,  # Aunque en realidad se toma el campaignId
            "campaignId": layout_id,
        }

        try:
            response = requests.post(f"{self.base_url}{self.SCHEDULE_ENDPOINT}", headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Evento creado: layout {layout_id} → grupo '{grupo_pantallas}' (ID {grupo_id})")
            return True
        except Exception as e:
            logger.error("Error al crear evento de layout.")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Respuesta de Xibo: {response.text}")
            return False

    def esta_corriendo_layout_en_grupo_ahora(self, grupo_pantallas, layout_id):
        """
        Verifica si en este momento hay un evento activo para el layout (campaign) en el grupo de pantallas.
        Retorna True si se encuentra activo, False en caso contrario.
        """
        if not self.token:
            logger.error("Token no disponible para consultar eventos.")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            # 1) Obtener el displayGroupId del grupo
            resp_grupos = requests.get(f"{self.base_url}{self.DISPLAYGROUP_ENDPOINT}", headers=headers)
            resp_grupos.raise_for_status()
            grupos = resp_grupos.json()
            grupo = next((g for g in grupos if g['displayGroup'] == grupo_pantallas), None)
            if not grupo:
                logger.warning(f"No se encontró el grupo de pantallas con nombre: {grupo_pantallas}")
                return False
            grupo_id = grupo['displayGroupId']

            # 2) Consultar eventos activos en el grupo a la hora actual
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            url = f"{self.base_url}{self.SCHEDULE_ENDPOINT}/{grupo_id}/events"
            params = {"date": date_str}

            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            eventos = data.get("events", [])

            # 3) Verificar si algún evento corresponde al layout buscado
            for ev in eventos:
                if ev.get("eventTypeId") == 1 and ev.get("campaignId") == layout_id:
                    return True
            return False

        except Exception as e:
            logger.exception("Error al consultar eventos actuales para el grupo.")
            return False
