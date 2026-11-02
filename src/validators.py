"""Validadores deterministas sobre la salida del LLM.

Cada validador devuelve una lista de problemas (texto). Lista vacía = sin problemas.
Se usan para (1) marcar campos dudosos en la UI y (2) pedirle al modelo que corrija.
"""

from __future__ import annotations

import re
from datetime import date

from .schema import Factura

IVA_RATE = 0.12  # IVA en Guatemala. Ver nota en el README sobre facturas exentas/pequeño contribuyente.
TOLERANCIA = 0.05  # Q, por redondeos


def nit_digito_valido(nit: str) -> bool:
    """Verifica el dígito verificador de un NIT (módulo 11).

    ⚠️ Algoritmo escrito de memoria: validarlo con NITs reales antes de confiar en él.
    """
    limpio = re.sub(r"[\s-]", "", nit).upper()
    if limpio == "CF":
        return True
    if len(limpio) < 2 or not limpio[:-1].isdigit():
        return False
    cuerpo, verif = limpio[:-1], limpio[-1]
    factor = len(cuerpo) + 1
    total = 0
    for digito in cuerpo:
        total += int(digito) * factor
        factor -= 1
    resultado = (11 - total % 11) % 11
    esperado = "K" if resultado == 10 else str(resultado)
    return verif == esperado


def validar(f: Factura) -> list[str]:
    problemas: list[str] = []

    if f.subtotal is not None and f.iva is not None and f.total is not None:
        if abs(f.subtotal + f.iva - f.total) > TOLERANCIA:
            problemas.append(f"subtotal + iva ({f.subtotal + f.iva:.2f}) no coincide con total ({f.total:.2f})")

    if f.subtotal is not None and f.iva is not None:
        if abs(f.subtotal * IVA_RATE - f.iva) > TOLERANCIA:
            problemas.append(f"iva ({f.iva:.2f}) no es ~12% del subtotal ({f.subtotal:.2f})")

    sumas = [l.total_linea for l in f.lineas if l.total_linea is not None]
    if sumas and f.total is not None and len(sumas) == len(f.lineas):
        if abs(sum(sumas) - f.total) > TOLERANCIA and abs(sum(sumas) - (f.subtotal or -1)) > TOLERANCIA:
            problemas.append(f"la suma de líneas ({sum(sumas):.2f}) no coincide con subtotal ni con total")

    for l in f.lineas:
        if l.cantidad is not None and l.precio_unitario is not None and l.total_linea is not None:
            if abs(l.cantidad * l.precio_unitario - l.total_linea) > TOLERANCIA:
                problemas.append(f"línea '{l.descripcion[:30]}': cantidad × precio ≠ total de línea")

    for campo in ("nit_emisor", "nit_receptor"):
        valor = getattr(f, campo)
        if valor and not nit_digito_valido(valor):
            problemas.append(f"{campo} '{valor}' no pasa el dígito verificador")

    if f.fecha:
        try:
            date.fromisoformat(f.fecha)
        except ValueError:
            problemas.append(f"fecha '{f.fecha}' no es una fecha AAAA-MM-DD válida")

    if f.autorizacion and not re.fullmatch(
        r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}", f.autorizacion
    ):
        problemas.append("autorización no tiene formato UUID")

    return problemas
