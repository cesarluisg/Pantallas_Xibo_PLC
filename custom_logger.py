import os
import logging
from logging.handlers import RotatingFileHandler

class CustomRotatingHandler(RotatingFileHandler):
    """
    Handler personalizado que, al alcanzar el tamaño máximo, 
    rota el log guardándolo con un nombre numerado (por ejemplo, main001.log, main002.log, etc.).
    Además, elimina el archivo de log dos rotaciones atrás para mantener solo el archivo actual y el inmediatamente anterior.
    """
    def __init__(self, baseFilename, maxBytes, encoding=None, delay=False):
        # Guarda la ruta base y separa la base y la extensión
        self.baseFilenameBase = baseFilename
        self.base, self.ext = os.path.splitext(baseFilename)
        # Inicializamos el contador en 1
        self.counter = 1
        # No usaremos backupCount, lo manejaremos manualmente
        super().__init__(baseFilename, mode='a', maxBytes=maxBytes, backupCount=0, encoding=encoding, delay=delay)

    def doRollover(self):
        """
        Realiza el proceso de rotación:
          - Cierra el stream actual.
          - Renombra el archivo actual a "base{counter:03d}.ext".
          - Incrementa el contador.
          - Borra el archivo que corresponde a dos rotaciones atrás, para conservar sólo el log actual y el inmediatamente anterior.
          - Reabre el stream de escritura.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Nombre del nuevo archivo rotado
        new_filename = f"{self.base}{self.counter:03d}{self.ext}"
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, new_filename)
        self.counter += 1

        # Borra el archivo de log de dos rotaciones atrás
        old_file = f"{self.base}{self.counter - 2:03d}{self.ext}"
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
            except Exception as e:
                logging.error("Error al borrar archivo antiguo %s: %s", old_file, e)

        # Reabre el stream de escritura para el nuevo archivo
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
