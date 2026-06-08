from __future__ import annotations

import uuid
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.vacante import (
    EstadoVacante,
    NivelFormacion,
    DisponibilidadHoraria,
    Vacante,
)
from app.repositories.vacante_repository import (
    DocumentoVacanteRepository,
    RequisitoRepository,
    VacanteRepository,
)
from app.schemas.vacante import (
    FiltrosVacante,
    MetricasVacantes,
    PerfilEstudianteMatching,
    VacanteCreate,
    VacanteMatchingResponse,
    VacanteResponse,
    VacanteResumenResponse,
    VacanteUpdate,
)

settings = get_settings()

TIPOS_DOCUMENTO_VALIDOS = {"rut", "camara_comercio", "descripcion_cargo"}


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


async def _subir_archivo_s3(file: UploadFile, key: str) -> str:
    s3 = _s3_client()
    try:
        contenido = await file.read()
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=contenido,
            ContentType=file.content_type or "application/octet-stream",
        )
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al subir el archivo: {str(e)}",
        )


def _calcular_score_matching(vacante: Vacante, perfil: PerfilEstudianteMatching) -> float:
    """Scoring 0–1 basado en cuántos criterios coinciden."""
    criterios = 4
    puntos = 0.0

    if perfil.area_conocimiento and perfil.area_conocimiento.lower() in vacante.area_conocimiento.lower():
        puntos += 1.0
    elif perfil.programa and perfil.programa.lower() in vacante.area_conocimiento.lower():
        puntos += 0.5

    if perfil.nivel_formacion and perfil.nivel_formacion == vacante.nivel_formacion:
        puntos += 1.0

    if perfil.disponibilidad_horaria and perfil.disponibilidad_horaria == vacante.disponibilidad_horaria:
        puntos += 1.0
    elif vacante.disponibilidad_horaria == DisponibilidadHoraria.flexible:
        puntos += 0.5

    if perfil.ciudad and vacante.ciudad and perfil.ciudad.lower() == vacante.ciudad.lower():
        puntos += 1.0
    elif not vacante.ciudad:
        puntos += 0.5

    return round(puntos / criterios, 2)


class VacanteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vacante_repo = VacanteRepository(db)
        self.requisito_repo = RequisitoRepository(db)
        self.documento_repo = DocumentoVacanteRepository(db)

    async def crear_vacante(self, empresa_id: uuid.UUID, datos: VacanteCreate) -> VacanteResponse:
        vacante = await self.vacante_repo.crear(
            empresa_id=empresa_id,
            titulo=datos.titulo,
            descripcion=datos.descripcion,
            area_conocimiento=datos.area_conocimiento,
            nivel_formacion=datos.nivel_formacion,
            modalidad=datos.modalidad,
            disponibilidad_horaria=datos.disponibilidad_horaria,
            ciudad=datos.ciudad,
            salario_min=datos.salario_min,
            salario_max=datos.salario_max,
            vacantes_disponibles=datos.vacantes_disponibles,
            fecha_cierre=datos.fecha_cierre,
        )
        if datos.requisitos:
            await self.requisito_repo.crear_bulk(vacante.id, datos.requisitos)

        vacante = await self.vacante_repo.get_by_id(vacante.id)
        return VacanteResponse.model_validate(vacante)

    async def publicar_vacante(self, vacante_id: uuid.UUID, empresa_id: uuid.UUID) -> VacanteResponse:
        vacante = await self._get_vacante_de_empresa(vacante_id, empresa_id)
        if vacante.estado == EstadoVacante.cerrada:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede publicar una vacante cerrada")
        vacante = await self.vacante_repo.cambiar_estado(vacante, EstadoVacante.publicada)
        return VacanteResponse.model_validate(vacante)

    async def cerrar_vacante(self, vacante_id: uuid.UUID, empresa_id: uuid.UUID) -> VacanteResponse:
        vacante = await self._get_vacante_de_empresa(vacante_id, empresa_id)
        vacante = await self.vacante_repo.cambiar_estado(vacante, EstadoVacante.cerrada)
        return VacanteResponse.model_validate(vacante)

    async def actualizar_vacante(
        self, vacante_id: uuid.UUID, empresa_id: uuid.UUID, datos: VacanteUpdate
    ) -> VacanteResponse:
        vacante = await self._get_vacante_de_empresa(vacante_id, empresa_id)
        if vacante.estado == EstadoVacante.cerrada:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede editar una vacante cerrada")
        await self.vacante_repo.actualizar(vacante, datos.model_dump(exclude_none=True))
        vacante = await self.vacante_repo.get_by_id(vacante_id)
        return VacanteResponse.model_validate(vacante)

    async def get_vacante(self, vacante_id: uuid.UUID) -> VacanteResponse:
        vacante = await self.vacante_repo.get_by_id(vacante_id)
        if not vacante:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")
        return VacanteResponse.model_validate(vacante)

    async def listar_vacantes(self, filtros: FiltrosVacante) -> List[VacanteResumenResponse]:
        offset = (filtros.page - 1) * filtros.page_size
        vacantes = await self.vacante_repo.listar(
            estado=EstadoVacante.publicada,
            area_conocimiento=filtros.area_conocimiento,
            nivel_formacion=filtros.nivel_formacion,
            modalidad=filtros.modalidad,
            disponibilidad_horaria=filtros.disponibilidad_horaria,
            ciudad=filtros.ciudad,
            salario_min=filtros.salario_min,
            offset=offset,
            limit=filtros.page_size,
        )
        return [VacanteResumenResponse.model_validate(v) for v in vacantes]

    async def mis_vacantes(self, empresa_id: uuid.UUID) -> List[VacanteResumenResponse]:
        vacantes = await self.vacante_repo.listar_por_empresa(empresa_id)
        return [VacanteResumenResponse.model_validate(v) for v in vacantes]

    async def matching(
        self, perfil: PerfilEstudianteMatching
    ) -> List[VacanteMatchingResponse]:
        filtros = FiltrosVacante(
            nivel_formacion=perfil.nivel_formacion,
            disponibilidad_horaria=perfil.disponibilidad_horaria,
            ciudad=perfil.ciudad,
            page_size=50,
        )
        vacantes = await self.listar_vacantes(filtros)

        scored = []
        for v in vacantes:
            vacante_orm = await self.vacante_repo.get_by_id(v.id)
            score = _calcular_score_matching(vacante_orm, perfil)
            if score > 0:
                scored.append(
                    VacanteMatchingResponse(**v.model_dump(), score_matching=score)
                )

        scored.sort(key=lambda x: x.score_matching, reverse=True)
        return scored[:20]

    async def subir_documento(
        self, vacante_id: uuid.UUID, empresa_id: uuid.UUID, tipo: str, file: UploadFile
    ) -> str:
        if tipo not in TIPOS_DOCUMENTO_VALIDOS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo inválido. Opciones: {list(TIPOS_DOCUMENTO_VALIDOS)}",
            )
        await self._get_vacante_de_empresa(vacante_id, empresa_id)
        key = f"vacantes/{vacante_id}/{tipo}/{file.filename}"
        url = await _subir_archivo_s3(file, key)
        await self.documento_repo.crear(vacante_id, tipo, url, file.filename)
        return url

    async def get_metricas(self) -> MetricasVacantes:
        por_estado = await self.vacante_repo.contar_por_estado()
        por_area = await self.vacante_repo.contar_por_campo(Vacante.area_conocimiento)
        por_modalidad = await self.vacante_repo.contar_por_campo(Vacante.modalidad)
        por_nivel = await self.vacante_repo.contar_por_campo(Vacante.nivel_formacion)
        por_disp = await self.vacante_repo.contar_por_campo(Vacante.disponibilidad_horaria)

        return MetricasVacantes(
            total_publicadas=por_estado.get("publicada", 0),
            total_cerradas=por_estado.get("cerrada", 0),
            total_cubiertas=por_estado.get("cubierta", 0),
            total_borradores=por_estado.get("borrador", 0),
            por_area=por_area,
            por_modalidad=por_modalidad,
            por_nivel_formacion=por_nivel,
            por_disponibilidad=por_disp,
        )

    async def _get_vacante_de_empresa(self, vacante_id: uuid.UUID, empresa_id: uuid.UUID) -> Vacante:
        vacante = await self.vacante_repo.get_by_id(vacante_id)
        if not vacante:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacante no encontrada")
        if vacante.empresa_id != empresa_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso sobre esta vacante")
        return vacante
