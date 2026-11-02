"""Esquema de salida de la extracción. Todo es opcional: si el dato no aparece
en el documento, el modelo debe devolver null en vez de inventarlo."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Linea(BaseModel):
    descripcion: str
    cantidad: Optional[float] = None
    precio_unitario: Optional[float] = None
    total_linea: Optional[float] = None


class Factura(BaseModel):
    nit_emisor: Optional[str] = Field(None, description="NIT del emisor, sin guiones ni espacios")
    nombre_emisor: Optional[str] = None
    nit_receptor: Optional[str] = Field(None, description="NIT del receptor o CF")
    nombre_receptor: Optional[str] = None
    fecha: Optional[str] = Field(None, description="Fecha de emisión en formato AAAA-MM-DD")
    serie: Optional[str] = None
    numero: Optional[str] = None
    autorizacion: Optional[str] = Field(None, description="Número de autorización (UUID)")
    lineas: list[Linea] = Field(default_factory=list)
    subtotal: Optional[float] = None
    iva: Optional[float] = None
    total: Optional[float] = None
    moneda: Optional[str] = Field(None, description="GTQ, USD, etc.")


# Campos escalares que se comparan en la evaluación.
CAMPOS_ESCALARES = [
    "nit_emisor", "nombre_emisor", "nit_receptor", "nombre_receptor", "fecha",
    "serie", "numero", "autorizacion", "subtotal", "iva", "total", "moneda",
]
