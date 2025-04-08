# docker_restart.py
import subprocess
import logging

YML_PATH = "/opt/xibo/xibo-docker-4.2.0/docker-compose.yml"  # Ajusta al nombre correcto


def restart_xibo_containers():
    try:
        # Ejecuta el comando en WSL para reiniciar todos los contenedores usando docker-compose
        # Nota: Ajusta la ruta si es diferente.
        result = subprocess.run(
            ["wsl", "docker-compose", "-f", YML_PATH, "restart"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logging.info("Salida del reinicio: %s", result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error("Error reiniciando contenedores: %s", e.stderr)