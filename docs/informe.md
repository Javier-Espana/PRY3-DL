# Extractor de facturas FEL con Claude — Trabajo escrito (Proyecto 3)

CC3092 Deep Learning y Sistemas Inteligentes · Entrega: viernes 6 de noviembre de 2026

> Esqueleto con la estructura del enunciado (sección 2). Lo marcado **[PENDIENTE]** requiere resultados reales
> o decisiones de ustedes; no se inventó ningún número. Convertir a PDF/LaTeX al final.

## 2.1 Definición del problema y usuario objetivo

- **Usuario:** pyme o contador que digita facturas a mano en Excel. **[PENDIENTE: describir un usuario real, ojalá validado con 1–2 personas.]**
- **Cómo se resuelve hoy:** digitación manual / regex por proveedor. **[PENDIENTE: estimar minutos por factura y tasa de error actual.]**
- **Por qué un LLM:** los formatos varían entre emisores y las reglas fijas se rompen con cada formato nuevo. Alternativa simple considerada: regex (baseline v0).
- **Criterios de éxito:** **[PENDIENTE: fijar metas ANTES de ver resultados, p. ej. exactitud por campo ≥ X % y ≥ Y % de documentos 100 % correctos.]**

## 2.2 Datos y pipeline

- **Fuentes:** 45 facturas **sintéticas** (`scripts/make_synthetic.py`, semilla 2026) + **[PENDIENTE: N facturas reales anonimizadas]**.
  Declarar explícitamente que el conjunto sintético lo diseñaron ustedes y puede favorecer o perjudicar a cada sistema.
- **Variación del conjunto sintético:** 4 layouts de PDF, 12 imágenes con rotación/ruido/desenfoque, 3 formatos de fecha, 1–8 líneas, ~10 % sin IVA.
- **Preprocesamiento:** PDF e imagen se envían directamente como bloques `document`/`image` (sin OCR propio).
- **Diagrama de arquitectura:** **[PENDIENTE: dibujar]** entrada → bloque documento → Claude (salida estructurada Pydantic) → validadores → reintento → UI/CSV/JSON.
- **RAG/embeddings:** no aplica (tarea de extracción). Decirlo y justificarlo.
- **Ventana de contexto:** una factura ocupa pocos miles de tokens. **[PENDIENTE: medir tokens promedio con `results/*.json`.]**

## 2.3 Selección del modelo y técnica de adaptación

- **Modelos comparados:** `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5` (cerrados, vía API, instruct). **[PENDIENTE: justificar elección final con costo y latencia medidos.]**
- **Técnica:** prompting con salida estructurada (esquema Pydantic) + validación determinista + reintento con retroalimentación. Sin fine-tuning.
- **Prompts:** `prompts/system_v1.txt` (mínimo) y `prompts/system_v2.txt` (reglas, nulos, formato, defensa ante prompt injection).
- **Parámetros de generación:** los modelos actuales no aceptan `temperature`/`top_p`; `max_tokens=8000`. Sin few-shot con imágenes (documentarlo como decisión o añadirlo).

## 2.4 Evaluación y medición

- **Conjunto propio:** 45 sintéticos (+ reales). **[PENDIENTE: quién etiquetó y quién revisó las referencias reales.]** El gold sintético sale del propio generador.
- **Métricas:** exactitud por campo, % documentos 100 % correctos, % salida válida, latencia media, tokens, costo por documento (`src/evaluate.py`).
- **Baseline:** regex sobre texto del PDF (v0). Medido sin API: ver `results/regex.json` (22 % de campos, 0 % de documentos completos; no lee imágenes por diseño).
- **Operativas / costo:** **[PENDIENTE: completar con las corridas]**.

## 2.5 Resultados de iteraciones

| Iter. | Cambio | Exactitud campos | Docs 100 % ok | Latencia (s) | Costo/doc (USD) |
|---|---|---|---|---|---|
| v0 | regex | 22.2 % | 0 % | — | 0 |
| v1 | Haiku, prompt mínimo | **[PENDIENTE]** | | | |
| v2 | Haiku, prompt v2 | **[PENDIENTE]** | | | |
| v3 | + reintento con validadores | **[PENDIENTE]** | | | |
| v4 | Sonnet / Opus | **[PENDIENTE]** | | | |

- **Ejemplos de fallas y cómo se abordaron:** **[PENDIENTE: salen de `results/*.json` → `detalle`]**.

## 2.6 Producto final y experiencia de usuario

- App Streamlit (`src/app.py`): subir archivo → tabla editable → descargar JSON/CSV; campos que no pasan validaciones se listan para revisión. **[PENDIENTE: capturas.]**
- Manejo de errores: archivo > 10 MB, formato no soportado, clave ausente, errores de API (no rompen la app).
- **[PENDIENTE: prueba con 2–3 personas ajenas al grupo.]**

## 2.7 Limitaciones, riesgos y ética

- Alucinación de montos (mitigada por validadores, no eliminada); documentos fuera de dominio; costo y latencia por llamada.
- **Privacidad:** las facturas se envían a la API de Anthropic. **Prompt injection:** el documento es dato (instrucción en el prompt).
- Validadores basados en supuestos no verificados con datos reales: dígito verificador del NIT, IVA 12 %, precios con IVA incluido.
- **No usar** para contabilidad oficial sin revisión humana.

## 2.8 Conclusiones

**[PENDIENTE tras las corridas: desempeño final, aprendizajes, trabajo futuro.]**

## 2.9 Repositorio

**[PENDIENTE: enlace público de GitHub.]** El README explica instalación, ejecución y cómo reproducir las métricas. La clave de API va en `.env` (excluido de git).
