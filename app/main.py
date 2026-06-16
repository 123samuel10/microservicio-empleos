from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.controllers.vacante_controller import router as vacante_router

settings = get_settings()

DESCRIPTION = """
## Microservicio de Empleos

Gestiona las vacantes de práctica publicadas por las empresas en **Emplea Humboldt**.

### Funcionalidades principales
- **Empresas** pueden crear, publicar, actualizar y cerrar vacantes.
- **Estudiantes** pueden listar vacantes con filtros y obtener recomendaciones por matching de perfil.
- Subida de documentos adjuntos a vacantes (convocatorias, requisitos) a S3.
- Métricas agregadas de vacantes para el panel de administración.

### Estados de una vacante
`BORRADOR` → `PUBLICADA` → `CERRADA`
"""

TAGS_METADATA = [
    {
        "name": "Vacantes",
        "description": "CRUD de vacantes, publicación, cierre, matching y métricas.",
    },
    {
        "name": "Health",
        "description": "Verificación del estado del servicio.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El esquema de la BD lo gestiona Alembic (entrypoint.sh -> alembic upgrade head), no create_all.
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    root_path="/empleos",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vacante_router, prefix="/api/v1")


@app.get("/health", tags=["Health"], summary="Estado del servicio")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        tags=TAGS_METADATA,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT obtenido en el microservicio de autenticación.",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
