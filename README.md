# Pantallas_Xibo_PLC

Este proyecto ejecuta un script en Python que:
- Consulta una lista de PLCs S7-1200.
- Lee la receta activa de cada uno.
- Consulta los diseños disponibles en Xibo.
- Asigna el diseño correspondiente al grupo de pantallas según la receta.

---

## 🧰 Requisitos

- Python **3.10.15**
- Virtualenv (`python -m venv venv`)
- Librerías listadas en `requirements.txt`

---

## 📁 Estructura del Proyecto

```
C:\Scripts\
├── main.py               # Script principal
├── config.json           # Parámetros de configuración
├── plc_ips.csv           # Lista de PLCs a consultar
├── requirements.txt      # Librerías con versiones
├── runtime.txt           # Versión de Python utilizada
├── venv\                # Entorno virtual (no compartir)
└── lanzador.bat          # Script para ejecutar todo automáticamente
```

---

## ▶️ Uso

### 1. Crear entorno virtual

```bash
cd C:\Scripts
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Ejecutar manualmente

```bash
cd C:\Scripts
call venv\Scripts\activate.bat
python main.py
```

### 3. Ejecutar automáticamente al iniciar Windows

Copiar `lanzador.bat` a:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 🔄 Mantenimiento

- Actualizar dependencias:
  ```bash
  pip freeze > requirements.txt
  ```

- Guardar versión de Python:
  ```bash
  echo python-3.10.15 > runtime.txt
  ```

---

## ✍️ Autor

César — Proyecto de sincronización entre PLCs Siemens y Xibo

