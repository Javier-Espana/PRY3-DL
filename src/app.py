"""Interfaz Streamlit para extracción y revisión de facturas FEL."""

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

st.set_page_config(page_title="Extractor FEL", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    :root, [data-theme="light"] {
        --ink: #17212b;
        --muted: #65717c;
        --line: #dce3e8;
        --surface: #ffffff;
        --canvas: #f4f7f8;
        --accent: #147d78;
        --accent-soft: #e5f3f1;
        --warning: #9a5d00;
        --warning-soft: #fff3dc;
        --sidebar-bg: #17212b;
        --sidebar-ink: #edf4f5;
        --sidebar-control: #24333e;
        --file-bg: #fbfdfd;
        --shadow: rgba(23, 33, 43, .05);
    }
    [data-theme="dark"] {
        --ink: #eef4f5;
        --muted: #aab9bd;
        --line: #34444c;
        --surface: #1d2a31;
        --canvas: #11191d;
        --accent: #55c5bb;
        --accent-soft: #173c3b;
        --warning: #f0b35d;
        --warning-soft: #493416;
        --sidebar-bg: #0c1317;
        --sidebar-ink: #edf4f5;
        --sidebar-control: #1d2a31;
        --file-bg: #18252b;
        --shadow: rgba(0, 0, 0, .22);
    }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
        background: var(--canvas);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: var(--sidebar-bg); }
    [data-testid="stSidebar"] * { color: var(--sidebar-ink); }
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="slider"] { background: var(--sidebar-control); }
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] input { color: var(--sidebar-ink) !important; }
    [data-baseweb="popover"], [role="listbox"] { background: var(--surface); color: var(--ink); }
    [role="option"] { color: var(--ink); }
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] h1,
    .stApp [data-testid="stMarkdownContainer"] h2,
    .stApp [data-testid="stMarkdownContainer"] h3,
    .stApp [data-testid="stMarkdownContainer"] h4,
    .stApp label { color: var(--ink); }
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] * { color: var(--muted); }
    .block-container { max-width: 1180px; padding-top: 2.5rem; padding-bottom: 4rem; }
    .hero { display: flex; justify-content: space-between; gap: 2rem; align-items: flex-end; margin-bottom: 2rem; }
    .eyebrow { color: var(--accent); font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .45rem; }
    .hero h1 { color: var(--ink); font-size: 2.35rem; letter-spacing: -.03em; line-height: 1.05; margin: 0; }
    .hero p { color: var(--muted); font-size: 1rem; margin: .65rem 0 0; max-width: 600px; }
    .model-chip { border: 1px solid var(--line); background: var(--surface); border-radius: 999px; color: var(--muted); font-size: .8rem; padding: .55rem .85rem; white-space: nowrap; }
    .section-label { color: var(--ink); font-size: 1.05rem; font-weight: 700; margin: 1.4rem 0 .7rem; }
    .upload-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 1.25rem 1.35rem .7rem; box-shadow: 0 8px 24px var(--shadow); }
    .upload-note { color: var(--muted); font-size: .8rem; margin-top: .2rem; }
    .result-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.15rem; min-height: 100%; }
    .result-panel h3 { font-size: 1rem; margin: 0 0 .8rem; }
    .status-ok { background: var(--accent-soft); border-left: 4px solid var(--accent); border-radius: 6px; color: var(--ink); padding: .8rem .9rem; }
    .status-warning { background: var(--warning-soft); border-left: 4px solid var(--warning); border-radius: 6px; color: var(--ink); padding: .8rem .9rem; }
    .metric-label { color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }
    .download-row { background: var(--surface); border-top: 1px solid var(--line); margin-top: 1.4rem; padding-top: 1.2rem; }
    div[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--line); border-radius: 9px; padding: .7rem .8rem; }
    div[data-testid="stFileUploader"] { border: 1px dashed var(--muted); border-radius: 9px; padding: .35rem; background: var(--file-bg); }
    .stDownloadButton button, .stButton button { color: var(--ink); border-color: var(--line); background: var(--surface); }
    .stDownloadButton button:hover, .stButton button:hover { color: var(--accent); border-color: var(--accent); }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Configuración")
    modelos = list(PRECIOS)
    por_defecto = os.getenv("FACTURAS_MODEL", DEFAULT_MODEL)
    modelo = st.selectbox("Modelo de extracción", modelos, index=modelos.index(por_defecto) if por_defecto in modelos else 0)
    reintentos = st.slider("Reintentos", min_value=0, max_value=1, value=1)
    st.divider()
    st.caption("Los documentos se envían al proveedor correspondiente al modelo seleccionado.")
    st.caption("Límite de archivo: 10 MB")

api_key_name = "ANTHROPIC_API_KEY" if modelo.startswith("claude-") else "OPENAI_API_KEY"

st.markdown(
    f"""
    <div class="hero">
      <div>
        <div class="eyebrow">Revisión documental</div>
        <h1>Extractor FEL</h1>
        <p>Convierte una factura en datos estructurados y revisables.</p>
      </div>
      <div class="model-chip">{modelo}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not os.getenv(api_key_name):
    st.error(f"Falta {api_key_name}. Configura la clave en .env para usar este modelo.")
    st.stop()

st.markdown('<div class="section-label">Documento de entrada</div>', unsafe_allow_html=True)
with st.container(border=True):
    archivo = st.file_uploader(
        "Selecciona una factura",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        label_visibility="visible",
    )
    st.markdown('<div class="upload-note">Formatos aceptados: PDF, PNG, JPG y WEBP.</div>', unsafe_allow_html=True)

if archivo is not None:
    if archivo.size > MAX_MB * 1024 * 1024:
        st.error(f"El archivo supera el límite de {MAX_MB} MB.")
        st.stop()

    st.markdown('<div class="section-label">Resultado</div>', unsafe_allow_html=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(archivo.name).suffix) as tmp:
        tmp.write(archivo.getvalue())
        temp_path = tmp.name
    try:
        with st.spinner("Procesando documento"):
            resultado = extraer(temp_path, modelo=modelo, max_reintentos=reintentos)
    finally:
        os.unlink(temp_path)

    if resultado.error or resultado.factura is None:
        st.error(f"No se pudo procesar el documento. {resultado.error or ''}")
        st.stop()

    factura = resultado.factura
    generales = {k: v for k, v in factura.model_dump().items() if k != "lineas"}
    datos = pd.DataFrame({"Campo": generales.keys(), "Valor": [str(v) for v in generales.values()]})
    lineas = pd.DataFrame([linea.model_dump() for linea in factura.lineas])

    left, right = st.columns([1.7, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Datos generales")
            st.dataframe(datos, hide_index=True, use_container_width=True, height=355)
        with st.container(border=True):
            st.markdown("### Líneas de factura")
            if lineas.empty:
                st.caption("No se encontraron líneas de detalle.")
            else:
                st.dataframe(lineas, hide_index=True, use_container_width=True)

    with right:
        with st.container(border=True):
            st.markdown("### Control de calidad")
            if resultado.problemas:
                problemas = "<br>".join(f"· {problema}" for problema in resultado.problemas)
                st.markdown(f'<div class="status-warning"><strong>Revisión requerida</strong><br>{problemas}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-ok"><strong>Validación correcta</strong><br>No se detectaron inconsistencias.</div>', unsafe_allow_html=True)
            st.write("")
            st.metric("Latencia", f"{resultado.latencia_s:.1f} s")
            st.metric("Costo estimado", f"${resultado.costo_usd:.4f}")
            st.caption(f"{resultado.tokens_in:,} tokens de entrada · {resultado.tokens_out:,} de salida · {resultado.intentos} intento(s)")

    st.markdown('<div class="download-row">', unsafe_allow_html=True)
    st.markdown("### Exportar resultado")
    filas = [
        {**{k: v for k, v in factura.model_dump().items() if k != "lineas"}, **linea.model_dump()}
        for linea in factura.lineas
    ] or [{k: v for k, v in factura.model_dump().items() if k != "lineas"}]
    download_json, download_csv = st.columns(2, gap="small")
    with download_json:
        st.download_button("Descargar JSON", factura.model_dump_json(indent=2), "factura.json", "application/json", use_container_width=True)
    with download_csv:
        st.download_button("Descargar CSV", pd.DataFrame(filas).to_csv(index=False), "factura.csv", "text/csv", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
