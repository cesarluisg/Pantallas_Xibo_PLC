import os
import logging
import re
from logging.handlers import RotatingFileHandler

class CustomRotatingHandler(RotatingFileHandler):
    """
    Handler personalizado que, al alcanzar el tamaño máximo,
    rota el log guardándolo con un nombre numerado (por ejemplo, main001.log, main002.log, etc.),
    y elimina el archivo de log dos rotaciones atrás para mantener solo el log actual y el inmediatamente anterior.
    """
    def __init__(self, baseFilename, maxBytes, encoding=None, delay=False):
        self.baseFilename = baseFilename
        self.base, self.ext = os.path.splitext(baseFilename)
        # Calcula el contador a partir de los archivos existentes:
        self.counter = self._get_initial_counter()
        super().__init__(baseFilename, mode='a', maxBytes=maxBytes, backupCount=0, encoding=encoding, delay=delay)

    def _get_initial_counter(self):
        """
        Revisa el directorio del archivo base para encontrar archivos que coincidan con el patrón
        (ej. mainNNN.log) y devuelve el contador siguiente (valor máximo + 1) o 1 si no hay ninguno.
        """
        dir_name = os.path.dirname(self.baseFilename)
        if not dir_name:
            dir_name = "."
        pattern = re.compile(re.escape(self.base) + r'(\d{3})' + re.escape(self.ext))
        max_counter = 0
        try:
            for file in os.listdir(dir_name):
                match = pattern.match(file)
                if match:
                    num = int(match.group(1))
                    if num > max_counter:
                        max_counter = num
        except Exception as e:
            logging.error("Error al calcular el contador inicial: %s", e)
        return max_counter + 1
    
    def doRollover(self):
        """
        Realiza el proceso de rotación:
          - Cierra el stream actual.
          - Renombra el archivo actual a "base{counter:03d}.ext" (elimina el archivo destino si ya existe).
          - Incrementa el contador.
          - Borra el archivo que corresponde a dos rotaciones atrás.
          - Reabre el stream de escritura.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Nombre del nuevo archivo rotado
        new_filename = f"{self.base}{self.counter:03d}{self.ext}"
        if os.path.exists(self.baseFilename):
            if os.path.exists(new_filename):
                try:
                    os.remove(new_filename)
                except Exception as e:
                    logging.error("Error al borrar el archivo existente %s: %s", new_filename, e)
            os.rename(self.baseFilename, new_filename)
        self.counter += 1

        # Borra el archivo de log de dos rotaciones atrás
        old_file = f"{self.base}{self.counter - 2:03d}{self.ext}"
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
            except Exception as e:
                logging.error("Error al borrar archivo antiguo %s: %s", old_file, e)

        self.mode = 'a'
        self.stream = self._open()
        
def setup_custom_logger(logger_name, log_filename, max_bytes, level=logging.DEBUG):
    """
    Configura un logger con el CustomRotatingHandler.
    
    Parámetros:
      - logger_name: nombre del logger.
      - log_filename: nombre del archivo base de log (ej. "main.log").
      - max_bytes: tamaño máximo del archivo de log antes de rotar.
      - level: nivel de logging (por defecto, DEBUG).
      
    Retorna el logger configurado.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    # Limpia cualquier handler existente
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Desactiva la propagación para evitar duplicados
    logger.propagate = False

    # Handler para archivo
    handler = CustomRotatingHandler(
        log_filename, 
        max_bytes, 
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
