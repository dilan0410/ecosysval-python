# Ecosysval Python - Sistema Inteligente Económico

API en Python (FastAPI) para el Sistema Inteligente Económico del proyecto Ecosysval.

## Descripción

Este servicio complementa el backend principal de Ecosysval (NestJS) proporcionando:

- Recopilación de datos económicos desde fuentes externas (INEGI, Banxico)
- Análisis y procesamiento de datos con pandas
- Generación de reportes e insights
- API REST consumible por el frontend de Ecosysval

## Tecnologías

- **Python 3.12**
- **FastAPI** - Framework para APIs REST
- **Uvicorn** - Servidor ASGI
- **Pandas** - Manipulación y análisis de datos
- **Requests** - Consumo de APIs externas
- **Pydantic** - Validación de datos

## Estructura del Proyecto

​```
ecosysval-python/
├── app/
│   ├── api/          # Endpoints (routers)
│   ├── services/     # Lógica de negocio
│   ├── models/       # Modelos de datos (Pydantic)
│   └── core/         # Configuración y utilidades
├── main.py           # Punto de entrada
├── requirements.txt  # Dependencias
├── .env.example      # Plantilla de variables de entorno
└── README.md
​```

## Instalación

### 1. Clonar el repositorio
​```
git clone https://github.com/tu-usuario/ecosysval-python.git
cd ecosysval-python
​```

### 2. Crear entorno virtual
​```
py -3.12 -m venv venv
​```

### 3. Activar entorno virtual
​```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
​```

### 4. Instalar dependencias
​```
pip install -r requirements.txt
​```

### 5. Configurar variables de entorno
​```bash
# Copiar la plantilla
copy .env.example .env

​```

### 6. Ejecutar el servidor
​```
uvicorn main:app --reload
​```

La API estará disponible en: `http://localhost:8000`
Documentación Swagger: `http://localhost:8000/docs`

## Documentación de la API

FastAPI genera documentación automática:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Autor

**Dylan Carvajal** - Practicante SENA - OMEC

## Licencia

Este proyecto es parte de las prácticas profesionales SENA-OMEC.
