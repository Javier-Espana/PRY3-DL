"""App Streamlit: sube una factura (PDF/imagen) y obtén JSON/CSV revisable.

Ejecutar desde la raíz del repo:  streamlit run src/app.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from src.extractor import DEFAULT_MODEL, PRECIOS, extraer  # noqa: E402

MAX_MB = 10

st.set_page_config(page_title="Extractor de facturas", page_icon="🧾", layout="wide")
st.title("🧾 Extractor de facturas FEL")
st.caption("Sube una factura y revisa los datos. Los campos marcados con ⚠️ no pasaron las validaciones: verifícalos.")

with st.sidebar:
    modelos = list(PRECIOS)
    por_defecto = os.getenv("FACTURAS_MODEL", DEFAULT_MODEL)
    modelo = st.selectbox("Modelo", modelos, index=modelos.index(por_defecto) if por_defecto in modelos else 0)
    reintentos = st.slider("Reintentos de corrección", 0, 1, 1)
    st.info("Los documentos se envían a OpenAI o Anthropic según el modelo. No subas facturas con datos que no puedas compartir.")

api_key_name = "ANTHROPIC_API_KEY" if modelo.startswith("claude-") else "OPENAI_API_KEY"
if not os.getenv(api_key_name):
    st.error(f"Falta {api_key_name}. Copia .env.example a .env y agrega la clave.")
    st.stop()

archivo = st.file_uploader("Factura (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg", "webp"])
if archivo is not None:
    if archivo.size > MAX_MB * 1024 * 1024:
        st.error(f"El archivo supera {MAX_MB} MB.")
        st.stop()
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(archivo.name).suffix) as tmp:
        tmp.write(archivo.getvalue())
    try:
        with st.spinner("Extrayendo datos..."):
            r = extraer(tmp.name, modelo=modelo, max_reintentos=reintentos)
    finally:
        os.unlink(tmp.name)

    if r.error or r.factura is None:
        st.error(f"No se pudo procesar el documento. {r.error or ''}")
        st.stop()

    f = r.factura
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Datos generales")
        generales = {k: v for k, v in f.model_dump().items() if k != "lineas"}
        st.dataframe(pd.DataFrame({"campo": generales.keys(), "valor": [str(v) for v in generales.values()]}),
                     hide_index=True, use_container_width=True)
        st.subheader("Líneas")
        st.dataframe(pd.DataFrame([l.model_dump() for l in f.lineas]), hide_index=True, use_container_width=True)
    with col2:
        if r.problemas:
            st.warning("⚠️ Revisar manualmente:\n\n" + "\n".join(f"- {p}" for p in r.problemas))
        else:
            st.success("Pasó todas las validaciones.")
        st.metric("Latencia", f"{r.latencia_s:.1f} s")
        st.metric("Costo estimado", f"${r.costo_usd:.4f}")
        st.caption(f"{r.tokens_in} tokens de entrada · {r.tokens_out} de salida · {r.intentos} intento(s)")

    st.download_button("Descargar JSON", f.model_dump_json(indent=2), "factura.json", "application/json")
    filas = [{**{k: v for k, v in f.model_dump().items() if k != "lineas"}, **l.model_dump()} for l in f.lineas] \
        or [{k: v for k, v in f.model_dump().items() if k != "lineas"}]
    st.download_button("Descargar CSV", pd.DataFrame(filas).to_csv(index=False), "factura.csv", "text/csv")
