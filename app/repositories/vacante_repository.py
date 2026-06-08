from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from app.models.vacante import (
    Vacante,
    RequisitoVacante,
    DocumentoVacante,
    EstadoVacante,
    NivelFormacion,
    Modalidad,
    DisponibilidadHoraria,
)


class VacanteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, vacante_id: uuid.UUID) -> Optional[Vacante]:
        result = await self.db.execute(
            select(Vacante)
            .options(
                selectinload(Vacante.requisitos),
                selectinload(Vacante.documentos),
            )
            .where(Vacante.id == vacante_id)
        )
        return result.scalar_one_or_none()

    async def listar(
        self,
        estado: EstadoVacante = EstadoVacante.publicada,
        area_conocimiento: Optional[str] = None,
        nivel_formacion: Optional[NivelFormacion] = None,
        modalidad: Optional[Modalidad] = None,
        disponibilidad_horaria: Optional[DisponibilidadHoraria] = None,
        ciudad: Optional[str] = None,
        salario_min: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Vacante]:
        query = (
            select(Vacante)
            .options(selectinload(Vacante.requisitos), selectinload(Vacante.documentos))
            .where(Vacante.estado == estado)
        )
        if area_conocimiento:
            query = query.where(Vacante.area_conocimiento.ilike(f"%{area_conocimiento}%"))
        if nivel_formacion:
            query = query.where(Vacante.nivel_formacion == nivel_formacion)
        if modalidad:
            query = query.where(Vacante.modalidad == modalidad)
        if disponibilidad_horaria:
            query = query.where(Vacante.disponibilidad_horaria == disponibilidad_horaria)
        if ciudad:
            query = query.where(Vacante.ciudad.ilike(f"%{ciudad}%"))
        if salario_min is not None:
            query = query.where(Vacante.salario_min >= salario_min)

        query = query.order_by(Vacante.fecha_publicacion.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def listar_por_empresa(self, empresa_id: uuid.UUID) -> List[Vacante]:
        result = await self.db.execute(
            select(Vacante)
            .options(selectinload(Vacante.requisitos), selectinload(Vacante.documentos))
            .where(Vacante.empresa_id == empresa_id)
            .order_by(Vacante.created_at.desc())
        )
        return list(result.scalars().all())

    async def crear(
        self,
        empresa_id: uuid.UUID,
        titulo: str,
        descripcion: str,
        area_conocimiento: str,
        nivel_formacion: NivelFormacion,
        modalidad: Modalidad,
        disponibilidad_horaria: DisponibilidadHoraria,
        **kwargs,
    ) -> Vacante:
        vacante = Vacante(
            empresa_id=empresa_id,
            titulo=titulo,
            descripcion=descripcion,
            area_conocimiento=area_conocimiento,
            nivel_formacion=nivel_formacion,
            modalidad=modalidad,
            disponibilidad_horaria=disponibilidad_horaria,
            **kwargs,
        )
        self.db.add(vacante)
        await self.db.flush()
        await self.db.refresh(vacante)
        return vacante

    async def actualizar(self, vacante: Vacante, datos: dict) -> Vacante:
        for campo, valor in datos.items():
            if valor is not None:
                setattr(vacante, campo, valor)
        await self.db.flush()
        await self.db.refresh(vacante)
        return vacante

    async def cambiar_estado(self, vacante: Vacante, nuevo_estado: EstadoVacante) -> Vacante:
        vacante.estado = nuevo_estado
        if nuevo_estado == EstadoVacante.publicada and not vacante.fecha_publicacion:
            vacante.fecha_publicacion = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(vacante)
        return vacante

    async def contar_por_estado(self) -> dict:
        result = await self.db.execute(
            select(Vacante.estado, func.count(Vacante.id)).group_by(Vacante.estado)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def contar_por_campo(self, campo) -> dict:
        result = await self.db.execute(
            select(campo, func.count(Vacante.id)).group_by(campo)
        )
        return {str(row[0]): row[1] for row in result.all()}


class RequisitoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_bulk(self, vacante_id: uuid.UUID, requisitos: list) -> None:
        for r in requisitos:
            req = RequisitoVacante(
                vacante_id=vacante_id,
                descripcion=r.descripcion,
                obligatorio=r.obligatorio,
            )
            self.db.add(req)
        await self.db.flush()

    async def eliminar_por_vacante(self, vacante_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(RequisitoVacante).where(RequisitoVacante.vacante_id == vacante_id)
        )
        for req in result.scalars().all():
            await self.db.delete(req)
        await self.db.flush()


class DocumentoVacanteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear(
        self, vacante_id: uuid.UUID, tipo: str, url: str, nombre_archivo: Optional[str] = None
    ) -> DocumentoVacante:
        doc = DocumentoVacante(
            vacante_id=vacante_id, tipo=tipo, url=url, nombre_archivo=nombre_archivo
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc
