from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator

from app.models.vacante import EstadoVacante, Modalidad, NivelFormacion, DisponibilidadHoraria, TipoOferta


# --- Requisitos ---

class RequisitoCreate(BaseModel):
    descripcion: str = Field(max_length=500)
    obligatorio: bool = True


class RequisitoResponse(RequisitoCreate):
    id: uuid.UUID
    vacante_id: uuid.UUID

    model_config = {"from_attributes": True}


# --- Documentos ---

class DocumentoVacanteResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    url: str
    nombre_archivo: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# --- Vacante ---

class VacanteCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str = Field(min_length=10)
    tipo_oferta: TipoOferta = TipoOferta.empleo
    area_conocimiento: str = Field(max_length=100)
    habilidades: List[str] = []
    nivel_formacion: NivelFormacion
    modalidad: Modalidad
    disponibilidad_horaria: DisponibilidadHoraria
    ciudad: Optional[str] = None
    salario_min: Optional[float] = Field(None, ge=0)
    salario_max: Optional[float] = Field(None, ge=0)
    vacantes_disponibles: int = Field(1, ge=1)
    fecha_cierre: Optional[datetime] = None
    requisitos: List[RequisitoCreate] = []

    @model_validator(mode="after")
    def salarios_coherentes(self) -> VacanteCreate:
        if self.salario_min and self.salario_max and self.salario_min > self.salario_max:
            raise ValueError("salario_min no puede ser mayor que salario_max")
        return self


class VacanteUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=10)
    tipo_oferta: Optional[TipoOferta] = None
    area_conocimiento: Optional[str] = Field(None, max_length=100)
    habilidades: Optional[List[str]] = None
    nivel_formacion: Optional[NivelFormacion] = None
    modalidad: Optional[Modalidad] = None
    disponibilidad_horaria: Optional[DisponibilidadHoraria] = None
    ciudad: Optional[str] = None
    salario_min: Optional[float] = Field(None, ge=0)
    salario_max: Optional[float] = Field(None, ge=0)
    vacantes_disponibles: Optional[int] = Field(None, ge=1)
    fecha_cierre: Optional[datetime] = None


class VacanteResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    titulo: str
    descripcion: str
    tipo_oferta: TipoOferta
    area_conocimiento: str
    habilidades: List[str] = []
    nivel_formacion: NivelFormacion
    modalidad: Modalidad
    disponibilidad_horaria: DisponibilidadHoraria
    ciudad: Optional[str] = None
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    vacantes_disponibles: int
    estado: EstadoVacante
    fecha_publicacion: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    requisitos: List[RequisitoResponse] = []
    documentos: List[DocumentoVacanteResponse] = []

    model_config = {"from_attributes": True}


class VacanteResumenResponse(BaseModel):
    id: uuid.UUID
    empresa_id: uuid.UUID
    titulo: str
    tipo_oferta: TipoOferta
    area_conocimiento: str
    habilidades: List[str] = []
    nivel_formacion: NivelFormacion
    modalidad: Modalidad
    disponibilidad_horaria: DisponibilidadHoraria
    ciudad: Optional[str] = None
    salario_min: Optional[float] = None
    salario_max: Optional[float] = None
    estado: EstadoVacante
    fecha_publicacion: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Filtros ---

class FiltrosVacante(BaseModel):
    tipo_oferta: Optional[TipoOferta] = None
    area_conocimiento: Optional[str] = None
    nivel_formacion: Optional[NivelFormacion] = None
    modalidad: Optional[Modalidad] = None
    disponibilidad_horaria: Optional[DisponibilidadHoraria] = None
    ciudad: Optional[str] = None
    salario_min: Optional[float] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# --- Matching ---

class PerfilEstudianteMatching(BaseModel):
    programa: Optional[str] = None
    area_conocimiento: Optional[str] = None
    nivel_formacion: Optional[NivelFormacion] = None
    disponibilidad_horaria: Optional[DisponibilidadHoraria] = None
    ciudad: Optional[str] = None


class VacanteMatchingResponse(VacanteResumenResponse):
    score_matching: float = Field(ge=0.0, le=1.0)


# --- Métricas ---

class MetricasVacantes(BaseModel):
    total_publicadas: int
    total_cerradas: int
    total_cubiertas: int
    total_borradores: int
    por_area: dict
    por_modalidad: dict
    por_nivel_formacion: dict
    por_disponibilidad: dict


# --- Upload doc ---

class DocumentoUploadResponse(BaseModel):
    vacante_id: uuid.UUID
    tipo: str
    url: str
    mensaje: str
