"""Baseline sin LLM: regex sobre el texto del PDF (pdfplumber).

Es a propósito simple: representa lo que haría una regla fija. Los patrones asumen
etiquetas tipo 'NIT:', 'Total:', etc.; ajustarlos tras ver facturas reales.
"""

from __future__ import annotations

import re
from pathlib import Path

from .schema import Factura

UUID = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"


def texto_pdf(path: str | Path) -> str:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _num(s: str | None) -> float | None:
    if not s:
        return None
    return float(s.replace(",", ""))


def extraer_regex_texto(texto: str) -> Factura:
    nits = re.findall(r"NIT[:\s]*([0-9]+-?[0-9Kk])", texto)
    fecha = re.search(r"(\d{4}-\d{2}-\d{2})", texto)
    if not fecha:
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto)
        fecha_iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    else:
        fecha_iso = fecha.group(1)
    total = re.search(r"Total[:\s]*(?:Q\.?\s*)?([\d,]+\.\d{2})", texto, re.I)
    iva = re.search(r"IVA[:\s]*(?:Q\.?\s*)?([\d,]+\.\d{2})", texto, re.I)
    auth = re.search(UUID, texto)
    return Factura(
        nit_emisor=nits[0].replace("-", "").upper() if nits else None,
        nit_receptor=nits[1].replace("-", "").upper() if len(nits) > 1 else None,
        fecha=fecha_iso,
        autorizacion=auth.group(0) if auth else None,
        iva=_num(iva.group(1)) if iva else None,
        total=_num(total.group(1)) if total else None,
    )


def extraer_regex(path: str | Path) -> Factura:
    return extraer_regex_texto(texto_pdf(path))
