# Traspaso del proyecto — Extractor de facturas FEL con GPT

Fecha del traspaso: 2 de noviembre de 2026. Este documento explica el estado real del trabajo y qué sigue.

## 1. Contexto (leer primero)

El curso CC3092 tiene **dos proyectos distintos**; no confundirlos (el grupo ya se confundió una vez):

| | Proyecto 3: Casos de uso de LLM | Proyecto Final: Caso de uso real |
|---|---|---|
| Qué es | Producto end-to-end basado en un LLM | Deep learning + modelo de valor de negocio |
| Feria / presentación | Lunes **2 de noviembre de 2026** | Semana del **16 de noviembre** |
| Trabajo escrito | Viernes **6 de noviembre** | Miércoles **18 de noviembre** |
| Qué contiene este repo | **Sí, es este proyecto** | No. AlertaP (sismos) se quitó de aquí; está en el commit `66e8efe` |

Enunciados (en `docs/` y/o en la carpeta superior): `Proyecto_3_Casos_de_Uso_LLM-1.pdf` (este repo). El PDF del Proyecto Final quedó fuera del repo, en `Deep Learning/`.

Este repo es el **Proyecto 3**. Lo que pide su rúbrica: producto funcional usable por terceros, conjunto de evaluación propio (30–50 casos), métricas y un baseline, iteraciones documentadas, trabajo escrito, repo con README reproducible y **video de 1–3 min**.

> Se desconoce si ya se habló con el catedrático sobre la feria del 2 de noviembre (el grupo creyó que era el mismo proyecto que el Final). Confirmarlo.

## 2. Qué hace el producto

Sube una factura (PDF o imagen) → GPT extrae los campos en JSON estructurado (esquema Pydantic) → validadores deterministas revisan consistencia → si fallan, se reintenta enviando los problemas al modelo → UI Streamlit con tabla, campos marcados y descarga JSON/CSV.

```
src/schema.py        esquema de la factura (todo opcional; null si no aparece)
src/extractor.py     llamadas OpenAI Responses y Anthropic Messages (salida Pydantic), reintento, tokens/latencia/costo
src/validators.py    IVA 12 %, sumas, dígito verificador de NIT, fecha, UUID
src/baseline_regex.py baseline sin LLM (pdfplumber + regex)
src/evaluate.py      evalúa contra data/gold y escribe results/<corrida>.json
src/app.py           app Streamlit
scripts/make_synthetic.py  genera facturas sintéticas + gold
prompts/system_v1.txt (mínimo)  system_v2.txt (reglas, nulos, anti prompt-injection)
docs/informe.tex     informe final del trabajo escrito (secciones 2.1–2.9 del enunciado); PDF en docs/informe.pdf
```

## 3. Cómo ejecutar

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt  # Windows: .venv/Scripts/python -m pip
cp .env.example .env                                  # y poner ambas claves en .env
.venv/bin/python -m pytest -q                         # 11 tests, no usan la API
.venv/bin/streamlit run src/app.py                   # app
.venv/bin/python -m src.evaluate --system llm --model gpt-4o-mini --prompt v2 --retries 1
.venv/bin/python -m src.evaluate --system llm --model claude-sonnet-5-5 --prompt v2 --retries 0
.venv/bin/python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v2 --retries 0
```

En Windows, si salen errores de codificación, anteponer `PYTHONUTF8=1`.

⚠️ **La clave va en `.env`, nunca en `.env.example`** (este último sí se versiona). Ya ocurrió una vez; se corrigió antes de subirla. `.env` está en `.gitignore`.

## 4. Resultados actuales (45 facturas sintéticas, `results/*.json`)

| Corrida | Campos OK | Docs 100 % OK | Latencia | USD/doc |
|---|---|---|---|---|
| Regex (v0, gold corregido) | 23,25 % | 0 % | — | 0 |
| GPT-4o-mini, prompt v2, sin reintento | 90,77 % | 15,56 % | 4,923 s | 0,00147 |
| Claude Haiku 5.5, prompt v2, sin reintento | 100 % | 100 % | 5,305 s | 0,00076 |
| Claude Sonnet 5.5, prompt v2, sin reintento | 98,63 % | 82,22 % | 3,958 s | 0,0113 |

Las corridas actuales están guardadas localmente en `results/` y usan el gold corregido. `results/*.json` **no se sube a git** (`.gitignore`); se pueden regenerar con los comandos anteriores. Haiku obtuvo 83,08 % de exactitud y 6,67 % de documentos completos en las 15 fixtures públicas, a `$0,00078` por documento.

### Hallazgos
1. **Bug en el gold sintético (corregido).** Los 6 documentos (`sint_016, 018, 022, 025, 030, 041`) son facturas sin IVA y no muestran subtotal. `make_synthetic.py` ahora genera `subtotal: null`; los seis JSON fueron regenerados y las corridas actuales usan ese gold corregido.
2. **El prompt v2 empeora `moneda`.** La regla "si no aparece explícito, devuelve null" deja la moneda vacía en 3–7 documentos que solo dicen "Q". El v1 infiere GTQ. Es un compromiso real (no inventar vs. inferir bien) que conviene documentar en el informe.
3. **Haiku fue el mejor en ambos conjuntos:** 100 % en las 45 FEL y 83,08 % en las 15 públicas; la diferencia refleja que el segundo conjunto contiene idiomas, descuentos y layouts fuera del esquema FEL.
4. **El conjunto sintético es demasiado fácil** (techo de rendimiento): la comparación puede no distinguir modelos; hace falta añadir datos difíciles y reales anonimizados.

## 5. Pendientes, en orden de prioridad

1. **[x] Arreglar el gold:** las facturas sin IVA ahora tienen `subtotal: null` en `crear_caso`; se regeneraron los 45 casos con la semilla 2026. **Declararlo en el informe** como un error de etiquetado hallado tras ver resultados, no como un ajuste a favor de un modelo. Las tres corridas actuales ya fueron ejecutadas.
2. **[parcial] Endurecer el conjunto:** se incorporaron 15 fixtures públicas sintéticas con fotos, layouts raros, descuentos, flete, duty y texto bilingüe en `data/public/shopify/`. Falta añadir **10–15 facturas reales anonimizadas**, etiquetarlas a mano con revisión cruzada y anotar quién etiquetó.
3. **[x] Completar `docs/informe.tex`:** informe final con arquitectura, datasets, métricas, costos, limitaciones, conclusiones y comandos reproducibles. La validación con usuarios externos y las capturas siguen siendo trabajo de entrega, no se inventan.
4. **Prueba de usabilidad** con 2–3 personas ajenas al grupo (sección 2.6), con capturas de pantalla.
5. **Material visual:** [parcial] el contenido base y la justificación metodológica del póster están en `docs/poster.md`. Falta maquetarlo visualmente y añadir el enlace/QR del repositorio. También falta el video demo de 1–3 min (.mp4) y el plan B de respuestas en caché.
6. **Verificar supuestos escritos de memoria**, hoy sin comprobar con datos reales:
   - Algoritmo del dígito verificador del NIT (`src/validators.py`).
   - Nombres de campos de la factura FEL (`src/schema.py`).
   - Que los precios incluyan IVA (el generador asume total = suma de líneas, subtotal = total/1,12).
   - Precios por modelo en `src/extractor.py` (`PRECIOS`) antes de reportar costos.
   - Patrones del baseline regex, ajustados a facturas reales.
7. **Ideas opcionales:** few-shot con ejemplos, intervalos de confianza (varias semillas/documentos), análisis de qué campos fallan por documento, caché de respuestas.

## 6. Cosas a tener en cuenta

- Los modelos actuales **rechazan `temperature`/`top_p`** (400); no se envían. El modelo razona siempre.
- Las facturas se envían a OpenAI o Anthropic según el modelo: no usar datos que no puedan compartirse. Declararlo en el informe (privacidad). El prompt trata el contenido del documento como dato (mitigación de prompt injection).
- `data/docs/*` está ignorado salvo `sint_*` (sintéticos) y el README; los documentos **reales** no deben subirse.
- El conjunto sintético y su gold salen del mismo script que diseñamos: declararlo como limitación.
- Historial del repo: `66e8efe` contiene AlertaP si algún día hace falta (`git checkout 66e8efe -- src README.md`).
