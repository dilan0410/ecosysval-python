"""
==========================================
ECOSYSVAL PYTHON API - Punto de entrada
==========================================
Sistema Inteligente Económico
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # NUEVO
from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.api import recomendaciones, empresas


# ==========================================
# CREAR LA APLICACIÓN FASTAPI
# ==========================================
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==========================================
# CONFIGURAR CORS
# ==========================================
# Lista de dominios permitidos (frontend que puede consumir la API)
origenes_permitidos = [
    "http://localhost:3000",           # React en desarrollo
    "http://localhost:3001",
    "http://localhost:5173",           # Vite (por si acaso)
    "https://ecosysval-app.vercel.app", # Producción de Ecosysval
]

# Agregar orígenes desde variable de entorno (para producción)
import os
extra_origins = os.getenv("EXTRA_CORS_ORIGINS", "")
if extra_origins:
    origenes_permitidos.extend(extra_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,     # Dominios permitidos
    allow_credentials=True,                 # Permitir cookies/auth
    allow_methods=["*"],                    # Métodos: GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                    # Todos los headers
)


# ==========================================
# INCLUIR ROUTERS
# ==========================================
app.include_router(recomendaciones.router)
app.include_router(empresas.router)


# ==========================================
# ENDPOINTS BASE
# ==========================================
@app.get("/", tags=["Base"])
def raiz():
    """Endpoint raíz - verifica que la API funciona."""
    return {
        "mensaje": f"¡Bienvenido a {APP_NAME}!",
        "version": APP_VERSION,
        "documentacion": "/docs",
        "endpoints_principales": {
            "sectores": "/recomendaciones/sectores",
            "estadisticas": "/recomendaciones/estadisticas",
            "recomendaciones": "/recomendaciones/{codigo}",
            "empresas": "/empresas",
            "socios": "/empresas/socios/{codigo}",
        }
    }


@app.get("/health", tags=["Base"])
def health_check():
    """Verifica el estado de salud del servicio."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION
    }