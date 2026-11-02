"""Extracción de facturas con la API de Claude + validación + reintento."""

from __future__ import annotations

import base64
import mimetypes
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from .schema import Factura
from .validators import validar

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
DEFAULT_MODEL = "claude-opus-5-5"

# USD por millón de tokens (entrada, salida). Fuente: tabla de modelos de la API; verificar antes de reportar.
PRECIOS = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


@dataclass
class Resultado:
    factura: Factura | None
    problemas: list[str] = field(default_factory=list)
    modelo: str = ""
    prompt: str = ""
    intentos: int = 0
    latencia_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    costo_usd: float = 0.0
    error: str | None = None


def cargar_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"system_{version}.txt").read_text(encoding="utf-8")


def bloque_documento(path: str | Path) -> dict:
    """Convierte un PDF o imagen en un bloque de contenido para la API."""
    path = Path(path)
    media_type = mimetypes.guess_type(path.name)[0] or ""
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    if media_type == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": media_type, "data": data}}
    if media_type in IMAGE_TYPES:
        return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}
    raise ValueError(f"Formato no soportado: {path.suffix} (usa PDF, PNG, JPG o WEBP)")


def _costo(modelo: str, tin: int, tout: int) -> float:
    pin, pout = PRECIOS.get(modelo, (0.0, 0.0))
    return (tin * pin + tout * pout) / 1_000_000


def extraer(
    path: str | Path,
    *,
    modelo: str = DEFAULT_MODEL,
    prompt_version: str = "v2",
    max_reintentos: int = 1,
    client: anthropic.Anthropic | None = None,
) -> Resultado:
    """Extrae una factura. Si los validadores fallan, reenvía los problemas al modelo
    (hasta `max_reintentos` veces). Nunca lanza por errores de API: los devuelve en `error`."""
    client = client or anthropic.Anthropic()
    res = Resultado(factura=None, modelo=modelo, prompt=prompt_version)
    started = time.perf_counter()
    try:
        system = cargar_prompt(prompt_version)
        messages: list[dict] = [{
            "role": "user",
            "content": [bloque_documento(path), {"type": "text", "text": "Extrae la factura."}],
        }]
        for intento in range(max_reintentos + 1):
            res.intentos = intento + 1
            # Sin temperature/top_p: los modelos actuales los rechazan (400).
            resp = client.messages.parse(
                model=modelo,
                max_tokens=8000,
                system=system,
                messages=messages,
                output_format=Factura,
            )
            res.tokens_in += resp.usage.input_tokens
            res.tokens_out += resp.usage.output_tokens
            if resp.stop_reason == "refusal":
                res.error = "El modelo rechazó la solicitud"
                break
            res.factura = resp.parsed_output
            res.problemas = validar(res.factura)
            if not res.problemas or intento == max_reintentos:
                break
            messages += [
                {"role": "assistant", "content": res.factura.model_dump_json()},
                {"role": "user", "content": (
                    "Tu extracción tiene inconsistencias:\n- " + "\n- ".join(res.problemas)
                    + "\nRevisa el documento y corrige solo lo que esté mal. "
                    "Si el documento mismo es inconsistente, deja los valores como aparecen."
                )},
            ]
    except (anthropic.APIError, ValueError) as e:  # APIError cubre red, auth, rate limit, etc.
        res.error = f"{type(e).__name__}: {e}"
    res.latencia_s = round(time.perf_counter() - started, 3)
    res.costo_usd = round(_costo(modelo, res.tokens_in, res.tokens_out), 6)
    return res
