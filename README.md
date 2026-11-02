# Extractor de facturas FEL con GPT (Proyecto 3: Casos de uso de LLM)

Sube una factura (PDF o imagen) y obtén un JSON/CSV con sus datos. Un LLM extrae los
campos, validadores deterministas revisan la consistencia (IVA, sumas, NIT, fecha) y los
campos dudosos se marcan para revisión humana.

## Pipeline

```
PDF/imagen -> bloque de documento -> GPT (salida estructurada, esquema Pydantic)
           -> validadores (IVA 12%, sumas, NIT, fecha, UUID)
           -> si fallan: se reenvían los problemas al modelo (reintento)
           -> tabla editable + JSON/CSV + campos marcados
```

## Instalación

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # Windows: .venv/Scripts/python -m pip
cp .env.example .env                            # y configura ambas claves
```

`.env` debe contener:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
FACTURAS_MODEL=gpt-4o-mini
```

La aplicación usa `OPENAI_API_KEY` para GPT y `ANTHROPIC_API_KEY` para Claude. No subas `.env` ni uses facturas que no tengas permiso de compartir.

## Uso

```bash
.venv/bin/streamlit run src/app.py              # app
.venv/bin/python -m pytest -q                   # tests (no llaman a la API)
```

En la barra lateral se elige el modelo y se puede activar como máximo un reintento. La aplicación muestra el resultado estructurado, advertencias, latencia, tokens y costo estimado. Los botones finales descargan `factura.json` y `factura.csv`.

Para probar un documento desde la interfaz, usa un PDF o imagen de hasta 10 MB. Los modelos disponibles son `gpt-4o-mini`, `claude-haiku-5-5` y `claude-sonnet-5-5`.

## Datos sintéticos

```bash
.venv/bin/python scripts/make_synthetic.py --n 45 --seed 2026
```

Genera `data/docs/sint_XXX.pdf|png` y `data/gold/sint_XXX.json` (nombres, NIT y UUID inventados).
Hay 4 layouts, etiquetas y formatos de fecha distintos, 1–8 líneas, ~10 % de pequeño contribuyente
(sin IVA) y ~25 % de imágenes con rotación, ruido y desenfoque. Con la misma semilla salen los mismos datos.
**En el informe hay que declarar que este conjunto es sintético**; complétenlo con facturas reales anonimizadas.

## Dataset público adicional

Se incorporó `data/public/shopify/` desde [Synthetic Shopify Invoice Test Pack](https://github.com/SalorWorks/shopify-invoice-test-pack), con licencia CC BY 4.0:

- 15 PDFs evaluables en `data/public/shopify/docs/`.
- 15 PNG en `data/public/shopify/images/` para inspección visual.
- 15 referencias convertidas al esquema FEL en `data/public/shopify/gold/`.
- Casos de multipágina, árabe, bilingüe, descuentos, flete, duty, mala calidad y tablas densas.

La importación reproducible está en `scripts/import_shopify_dataset.py`. Este conjunto se evalúa separado de las 45 facturas sintéticas FEL y sus campos no equivalentes quedan en `null`.
En la prueba actual, Haiku obtuvo 83,08 % de exactitud global y `$0,00078` por documento.

```bash
.venv/bin/python -m src.evaluate --system regex \
    --docs data/public/shopify/docs --gold data/public/shopify/gold --run-name public_shopify
```

## Evaluación (reproducir métricas)

Pon los documentos en `data/docs/` y su referencia en `data/gold/<nombre>.json`.

```bash
.venv/bin/python -m src.evaluate --system regex                         # v0 baseline sin LLM
.venv/bin/python -m src.evaluate --system llm --model gpt-4o-mini --prompt v1 --retries 0
.venv/bin/python -m src.evaluate --system llm --model gpt-4o-mini --prompt v2 --retries 0
.venv/bin/python -m src.evaluate --system llm --model gpt-4o-mini --prompt v2 --retries 1
.venv/bin/python -m src.evaluate --system llm --model claude-sonnet-5-5 --prompt v2 --retries 0
.venv/bin/python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v2 --retries 0
```

Cada corrida escribe `results/<run>.json` con exactitud por campo, % de documentos 100 %
correctos, latencia, tokens y costo. Esas corridas son la tabla de iteraciones del informe.

## Estructura principal

- `src/schema.py`: esquema Pydantic de salida.
- `src/extractor.py`: proveedores, modelos, límites de tokens y costos.
- `src/validators.py`: validaciones deterministas.
- `src/evaluate.py`: evaluación por campo y por documento.
- `src/app.py`: interfaz Streamlit.
- `scripts/make_synthetic.py`: generación FEL reproducible.
- `scripts/import_shopify_dataset.py`: importación del dataset público.
- `docs/informe.tex`: fuente LaTeX autoritativa del informe final.
- `docs/informe.md`: copia legible del contenido del informe.
- `docs/informe.pdf`: PDF generado localmente; recompilar desde LaTeX antes de entregar.

## Notas técnicas

- Los modelos actuales rechazan `temperature`/`top_p`; no se envían.
- La clave se selecciona según el modelo: `OPENAI_API_KEY` para GPT y `ANTHROPIC_API_KEY` para Claude (archivo `.env`, excluido de git).
- El contenido del documento se trata como datos: el prompt ordena ignorar instrucciones dentro de él (prompt injection).
- Las facturas se envían a OpenAI o Anthropic según el modelo: no usar con datos que no se puedan compartir.
- `gpt-4o-mini` es el modelo predeterminado; Sonnet y Haiku se comparan con `--retries 0` para controlar el gasto.
- Los resultados guardados en `results/` son locales y están excluidos de Git; cada corrida puede regenerarse con `src.evaluate`.

Para regenerar el informe PDF:

```bash
pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory docs docs/informe.tex
```
