# Dataset público Shopify Invoice Test Pack

Fuente: https://github.com/SalorWorks/shopify-invoice-test-pack
Licencia: CC BY 4.0. Las fixtures son sintéticas. Los PDF evaluables están en `docs/` y los PNG en `images/`.

Los `expected.json` originales se transformaron al esquema `Factura` del proyecto:
`supplier` -> emisor, `billTo` -> receptor, `invoiceNumber` -> numero,
`lines` -> lineas y `tax` -> iva. Los campos ausentes quedan en null.

Este conjunto se mantiene separado de `data/docs` y no se mezcla con la métrica de las 45
facturas FEL sintéticas. Algunas fixtures incluyen descuentos, flete o duty; los validadores
pueden marcarlas para revisión porque el esquema FEL actual no modela esos conceptos.

Corridas actuales (`--retries 0`): GPT 72,31 % / 0 % completos / `$0,00155` por documento; Haiku 83,08 % / 6,67 % / `$0,00078`; Sonnet 91,28 % / 33,33 % / `$0,01162`.

Baseline reproducible:
`.venv/bin/python -m src.evaluate --system regex --docs data/public/shopify/docs --gold data/public/shopify/gold --run-name public_shopify`
