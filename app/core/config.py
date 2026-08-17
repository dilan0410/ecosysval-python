"""
==========================================
CONFIGURACIÓN GLOBAL
==========================================
Rutas y constantes usadas en todo el proyecto.
"""

import os

# ==========================================
# RUTAS DE ARCHIVOS
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

RUTA_MIP = os.path.join(DATA_DIR, "MIP_2013.xlsx")
RUTA_CLASIFICACION = os.path.join(DATA_DIR, "clasificacion_2024.xlsx")

# ==========================================
# CONFIGURACIÓN DE LA MIP
# ==========================================
FILA_ENCABEZADOS_MIP = 4

# ==========================================
# CONFIGURACIÓN DE LA CLASIFICACIÓN
# ==========================================
HOJAS_CATEGORIAS = [
    "Clave",
    "Articulador",
    "Multicadena impulsor",
    "Potenciales",
    "Multicadenas",
    "ARTICULADOS GRISES",
    "NO ARTICULADO",
]

# ==========================================
# PARÁMETROS DE RECOMENDACIÓN
# ==========================================
TOP_N_DEFAULT = 5
TOP_N_MAX = 20

# ==========================================
# INFO DE LA APP
# ==========================================
APP_NAME = "Ecosysval Python API"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = "Sistema Inteligente Económico - Recomendaciones basadas en MIP 2013 + Clasificación 2024"