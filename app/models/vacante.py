from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, Enum, Text, Integer, Numeric, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class TipoOferta(str, enum.Enum):
    empleo = "empleo"
    practica = "practica"


class EstadoVacante(str, enum.Enum):
    borrador = "borrador"
    publicada = "publicada"
    cerrada = "cerrada"
    cubierta = "cubierta"


class Modalidad(str, enum.Enum):
    presencial = "presencial"
    remoto = "remoto"
    hibrido = "hibrido"


class NivelFormacion(str, enum.Enum):
    tecnico = "tecnico"
    tecnologo = "tecnologo"
    universitario = "universitario"
    posgrado = "posgrado"


class DisponibilidadHoraria(str, enum.Enum):
    tiempo_completo = "tiempo_completo"
    medio_tiempo = "medio_tiempo"
    fines_de_semana = "fines_de_semana"
    flexible = "flexible"


class Vacante(Base):
    __tablename__ = "vacantes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    # Tipo de oferta: empleo o práctica. Por defecto "empleo".
    tipo_oferta: Mapped[TipoOferta] = mapped_column(
        Enum(TipoOferta, name="tipo_oferta_enum"),
        default=TipoOferta.empleo,
        server_default="empleo",
        nullable=False,
        index=True,
    )
    area_conocimiento: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Habilidades/skills requeridas. Lista de strings; por defecto vacía ('{}').
    habilidades: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}"
    )
    nivel_formacion: Mapped[NivelFormacion] = mapped_column(
        Enum(NivelFormacion, name="nivel_formacion_enum"), nullable=False
    )
    modalidad: Mapped[Modalidad] = mapped_column(
        Enum(Modalidad, name="modalidad_enum"), nullable=False
    )
    disponibilidad_horaria: Mapped[DisponibilidadHoraria] = mapped_column(
        Enum(DisponibilidadHoraria, name="disponibilidad_horaria_enum"), nullable=False
    )
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    salario_min: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    salario_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    vacantes_disponibles: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    estado: Mapped[EstadoVacante] = mapped_column(
        Enum(EstadoVacante, name="estado_vacante_enum"),
        default=EstadoVacante.borrador,
        nullable=False,
        index=True,
    )
    fecha_publicacion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    requisitos: Mapped[List[RequisitoVacante]] = relationship(
        back_populates="vacante", cascade="all, delete-orphan"
    )
    documentos: Mapped[List[DocumentoVacante]] = relationship(
        back_populates="vacante", cascade="all, delete-orphan"
    )


class RequisitoVacante(Base):
    __tablename__ = "requisitos_vacante"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vacante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacantes.id", ondelete="CASCADE"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    obligatorio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vacante: Mapped[Vacante] = relationship(back_populates="requisitos")


class DocumentoVacante(Base):
    __tablename__ = "documentos_vacante"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vacante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacantes.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_archivo: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    vacante: Mapped[Vacante] = relationship(back_populates="documentos")
