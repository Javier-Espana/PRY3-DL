"""Extracción multimodelo de facturas con validación y reintento limitado."""

from __future__ import annotations

import base64
import mimetypes
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic
from openai import OpenAI

from .schema import Factura
from .validators import validar

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_OUTPUT_TOKENS = 2000
MAX_REINTENTOS = 1

# USD por millón de tokens (entrada, salida). Verificar antes de publicar métricas.
PRECIOS = {
    "gpt-4o-mini": (0.15, 0.60),
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
    """Convierte un PDF o imagen en un bloque de entrada multimodal."""
    path = Path(path)
    media_type = mimetypes.guess_type(path.name)[0] or ""
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    if media_type == "application/pdf":
        return {"type": "input_file", "filename": path.name,
                "file_data": f"data:{media_type};base64,{data}"}
    if media_type in IMAGE_TYPES:
        return {"type": "input_image", "image_url": f"data:{media_type};base64,{data}"}
    raise ValueError(f"Formato no soportado: {path.suffix} (usa PDF, PNG, JPG o WEBP)")


def _bloque_anthropic(path: str | Path) -> dict:
    """Convierte un PDF o imagen al formato de contenido de Anthropic."""
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
    max_reintentos: int = MAX_REINTENTOS,
    client: Any | None = None,
    anthropic_client: Any | None = None,
) -> Resultado:
    """Extrae una factura. Si los validadores fallan, reenvía los problemas al modelo
    (hasta `max_reintentos` veces). Nunca lanza por errores de API: los devuelve en `error`."""
    if max_reintentos < 0 or max_reintentos > MAX_REINTENTOS:
        raise ValueError(f"max_reintentos debe estar entre 0 y {MAX_REINTENTOS}")
    usa_anthropic = modelo.startswith("claude-")
    client = client or (anthropic_client or anthropic.Anthropic() if usa_anthropic else OpenAI())
    res = Resultado(factura=None, modelo=modelo, prompt=prompt_version)
    started = time.perf_counter()
    try:
        system = cargar_prompt(prompt_version)
        messages: list[dict] = [{"role": "user", "content": [
            (_bloque_anthropic(path) if usa_anthropic else bloque_documento(path)),
            {"type": "text", "text": "Extrae la factura."}
            if usa_anthropic else {"type": "input_text", "text": "Extrae la factura."},
        ]}]
        for intento in range(max_reintentos + 1):
            res.intentos = intento + 1
            if usa_anthropic:
                resp = client.messages.parse(
                    model=modelo, max_tokens=MAX_OUTPUT_TOKENS, system=system,
                    messages=messages, output_format=Factura,
                )
            else:
                resp = client.responses.parse(
                    model=modelo, max_output_tokens=MAX_OUTPUT_TOKENS,
                    input=[
                        {"role": "system", "content": [{"type": "input_text", "text": system}]},
                        *messages,
                    ],
                    text_format=Factura,
                )
            res.tokens_in += resp.usage.input_tokens
            res.tokens_out += resp.usage.output_tokens
            parsed = resp.parsed_output if usa_anthropic else resp.output_parsed
            rechazado = (getattr(resp, "stop_reason", "") == "refusal" if usa_anthropic else (
                getattr(resp, "status", "completed") != "completed" or parsed is None
            ))
            if rechazado or parsed is None:
                res.error = "El modelo rechazó la solicitud"
                break
            res.factura = parsed
            res.problemas = validar(res.factura)
            if not res.problemas or intento == max_reintentos:
                break
            texto_correccion = (
                    "Tu extracción tiene inconsistencias:\n- " + "\n- ".join(res.problemas)
                    + "\nRevisa el documento y corrige solo lo que esté mal. "
                    "Si el documento mismo es inconsistente, deja los valores como aparecen."
                )
            if usa_anthropic:
                messages += [
                    {"role": "assistant", "content": res.factura.model_dump_json()},
                    {"role": "user", "content": texto_correccion},
                ]
            else:
                messages += [{"role": "user", "content": [{"type": "input_text", "text": texto_correccion}]}]
    except Exception as e:
        res.error = f"{type(e).__name__}: {e}"
    res.latencia_s = round(time.perf_counter() - started, 3)
    res.costo_usd = round(_costo(modelo, res.tokens_in, res.tokens_out), 6)
    return res
