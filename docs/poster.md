# Texto base para el póster

## Resultados principales

### 45 facturas FEL sintéticas

**Exactitud global por campo, sin reintentos**

| Sistema | Exactitud |
|---|---:|
| Regex | 23,25% |
| GPT-4o-mini | 90,77% |
| Claude Haiku 5.5 | **100%** |
| Claude Sonnet 5.5 | 98,63% |

| Sistema | Documentos 100% correctos | Latencia media | Costo por documento |
|---|---:|---:|---:|
| Regex | 0% | -- | USD 0 |
| GPT-4o-mini | 15,56% | 4,9 s | USD 0,00147 |
| Claude Haiku 5.5 | **100%** | 5,3 s | **USD 0,00076** |
| Claude Sonnet 5.5 | 82,22% | 4,0 s | USD 0,0113 |

**Conclusión para el póster:**

> En el conjunto principal FEL, Claude Haiku 5.5 fue la mejor relación precisión/costo: alcanzó 100% de exactitud global y de documentos completamente correctos, con un costo de USD 0,00076 por documento. Sonnet costó aproximadamente 15 veces más y obtuvo 98,63%, por debajo de Haiku en este experimento.

El costo total de las tres corridas LLM fue aproximadamente USD 0,61. Todas las corridas comparativas usaron prompt v2, cero reintentos y un límite de 2.000 tokens de salida.

## Justificación metodológica

El encabezado debe decir **"Resultados principales: 45 facturas FEL"**. La conclusión de Haiku se refiere únicamente a ese conjunto: facturas sintéticas con campos y convenciones cercanas al esquema FEL guatemalteco. No afirma que Haiku sea superior a Sonnet en cualquier dataset.

Como comprobación de robustez, se evaluó además un pack público de 15 facturas sintéticas internacionales. En ese conjunto los resultados cambiaron: GPT obtuvo 72,31%, Haiku 83,08% y Sonnet 91,28%. Sonnet fue mejor allí, pero con un costo de USD 0,01162 por documento frente a USD 0,00078 de Haiku.

Esta diferencia no contradice el resultado principal. Los datasets tienen dominios distintos:

- El conjunto FEL contiene facturas diseñadas alrededor del esquema guatemalteco y sus campos.
- El pack público contiene documentos árabes, bilingües e internacionales, con descuentos, flete, duty y otra estructura comercial.
- El conjunto público se usa como prueba secundaria de robustez, no como evidencia de desempeño tributario FEL.

**Texto opcional pequeño para el póster:**

> La recomendación de Haiku es específica para el conjunto FEL evaluado. En un conjunto público internacional adicional, Sonnet obtuvo mayor exactitud, pero con un costo aproximadamente 15 veces mayor. Esto muestra que la selección del modelo depende del dominio y del presupuesto.

## Orden visual sugerido

1. Problema y pipeline.
2. Tabla principal de 45 facturas FEL.
3. Mensaje destacado: "Haiku: 100% de exactitud, USD 0,00076/documento".
4. Comparación de costo y latencia.
5. Nota metodológica: conjunto sintético, validación humana pendiente y revisión obligatoria.
6. QR o enlace al repositorio.

## Qué no afirmar

- No decir que Haiku es universalmente mejor que Sonnet.
- No mezclar los porcentajes del pack público con la tabla principal FEL.
- No presentar las facturas sintéticas como facturas reales.
- No afirmar que el sistema reemplaza revisión contable o validación tributaria.
