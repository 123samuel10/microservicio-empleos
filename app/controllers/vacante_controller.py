from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.deps import UsuarioToken, get_current_user, require_empresa, require_estudiante
from app.database import get_db
from app.schemas.vacante import (
    DocumentoUploadResponse,
    FiltrosVacante,
    MetricasVacantes,
    PerfilEstudianteMatching,
    VacanteCreate,
    VacanteMatchingResponse,
    VacanteResponse,
    VacanteResumenResponse,
    VacanteUpdate,
)
from app.services.vacante_service import VacanteService

router = APIRouter(prefix="/vacantes", tags=["Vacantes"])


@router.post("", response_model=VacanteResponse, status_code=status.HTTP_201_CREATED)
async def crear_vacante(
    datos: VacanteCreate,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    service = VacanteService(db)
    return await service.crear_vacante(usuario.id, datos)


@router.get("", response_model=List[VacanteResumenResponse])
async def listar_vacantes(
    tipo_oferta: str = Query(None),
    area_conocimiento: str = Query(None),
    nivel_formacion: str = Query(None),
    modalidad: str = Query(None),
    disponibilidad_horaria: str = Query(None),
    ciudad: str = Query(None),
    salario_min: float = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filtros = FiltrosVacante(
        tipo_oferta=tipo_oferta,
        area_conocimiento=area_conocimiento,
        nivel_formacion=nivel_formacion,
        modalidad=modalidad,
        disponibilidad_horaria=disponibilidad_horaria,
        ciudad=ciudad,
        salario_min=salario_min,
        page=page,
        page_size=page_size,
    )
    service = VacanteService(db)
    return await service.listar_vacantes(filtros)


@router.get("/mis-vacantes", response_model=List[VacanteResumenResponse])
async def mis_vacantes(
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    service = VacanteService(db)
    return await service.mis_vacantes(usuario.id)


@router.post("/matching", response_model=List[VacanteMatchingResponse])
async def matching_vacantes(
    perfil: PerfilEstudianteMatching,
    db: AsyncSession = Depends(get_db),
    _: UsuarioToken = Depends(require_estudiante),
):
    service = VacanteService(db)
    return await service.matching(perfil)


@router.get("/metricas", response_model=MetricasVacantes)
async def metricas(
    db: AsyncSession = Depends(get_db),
    _: UsuarioToken = Depends(get_current_user),
):
    service = VacanteService(db)
    return await service.get_metricas()


@router.get("/{vacante_id}", response_model=VacanteResponse)
async def get_vacante(
    vacante_id: str,
    db: AsyncSession = Depends(get_db),
):
    import uuid
    service = VacanteService(db)
    return await service.get_vacante(uuid.UUID(vacante_id))


@router.put("/{vacante_id}", response_model=VacanteResponse)
async def actualizar_vacante(
    vacante_id: str,
    datos: VacanteUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    import uuid
    service = VacanteService(db)
    return await service.actualizar_vacante(uuid.UUID(vacante_id), usuario.id, datos)


@router.post("/{vacante_id}/publicar", response_model=VacanteResponse)
async def publicar_vacante(
    vacante_id: str,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    import uuid
    service = VacanteService(db)
    return await service.publicar_vacante(uuid.UUID(vacante_id), usuario.id)


@router.post("/{vacante_id}/cerrar", response_model=VacanteResponse)
async def cerrar_vacante(
    vacante_id: str,
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    import uuid
    service = VacanteService(db)
    return await service.cerrar_vacante(uuid.UUID(vacante_id), usuario.id)


@router.post("/{vacante_id}/documentos/{tipo}", response_model=DocumentoUploadResponse)
async def subir_documento(
    vacante_id: str,
    tipo: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: UsuarioToken = Depends(require_empresa),
):
    import uuid
    service = VacanteService(db)
    url = await service.subir_documento(uuid.UUID(vacante_id), usuario.id, tipo, file)
    return DocumentoUploadResponse(
        vacante_id=uuid.UUID(vacante_id),
        tipo=tipo,
        url=url,
        mensaje="Documento subido correctamente",
    )
