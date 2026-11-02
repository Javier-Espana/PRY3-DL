# Extractor de facturas FEL con Claude (Proyecto 3: Casos de uso de LLM)

Sube una factura (PDF o imagen) y obtén un JSON/CSV con sus datos. Un LLM extrae los
campos, validadores deterministas revisan la consistencia (IVA, sumas, NIT, fecha) y los
campos dudosos se marcan para revisión humana.

> Este proyecto es independiente de AlertaP (Proyecto Final), que vive en `../src`.

## Pipeline

```
PDF/imagen -> bloque de documento -> Claude (salida estructurada, esquema Pydantic)
           -> validadores (IVA 12%, sumas, NIT, fecha, UUID)
           -> si fallan: se reenvían los problemas al modelo (reintento)
           -> tabla editable + JSON/CSV + campos marcados
```

## Instalación

```bash
cd proyecto3_llm
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows (en Linux/Mac: .venv/bin/pip)
cp .env.example .env                            # y pon tu ANTHROPIC_API_KEY
```

## Uso

```bash
.venv/Scripts/streamlit run src/app.py          # app
.venv/Scripts/python -m pytest -q               # tests (no llaman a la API)
```

## Evaluación (reproducir métricas)

Pon los documentos en `data/docs/` y su referencia en `data/gold/<nombre>.json`.

```bash
python -m src.evaluate --system regex                                   # v0 baseline sin LLM
python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v1 --retries 0
python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v2 --retries 0
python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v2 --retries 1
python -m src.evaluate --system llm --model claude-sonnet-5-5 --prompt v2 --retries 1
python -m src.evaluate --system llm --model claude-opus-5-5 --prompt v2 --retries 1
```

Cada corrida escribe `results/<run>.json` con exactitud por campo, % de documentos 100 %
correctos, latencia, tokens y costo. Esas corridas son la tabla de iteraciones del informe.

## Pendientes (ver también el plan del proyecto)

- [ ] Reunir 40–50 documentos + gold (la mitad etiquetada por cada integrante, con revisión cruzada).
- [ ] Verificar el algoritmo del dígito verificador del NIT (`src/validators.py`) con NITs reales.
- [ ] Verificar los campos del esquema contra 2–3 facturas FEL reales.
- [ ] Ajustar los patrones del baseline regex (`src/baseline_regex.py`) a las facturas reales.
- [ ] Verificar los precios por modelo en `src/extractor.py` antes de reportar costos.
- [ ] Ejecutar las corridas de arriba y llenar la tabla de iteraciones.
- [ ] Caché de respuestas / video de respaldo para la feria.

## Notas técnicas

- Los modelos actuales rechazan `temperature`/`top_p`; no se envían.
- La clave de API se lee de `ANTHROPIC_API_KEY` (archivo `.env`, excluido de git).
- El contenido del documento se trata como datos: el prompt ordena ignorar instrucciones dentro de él (prompt injection).
- Las facturas se envían a la API de Anthropic: no usar con datos que no se puedan compartir.
