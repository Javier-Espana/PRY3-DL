"""Importa fixtures públicas sintéticas de facturas al esquema del proyecto.

Uso:
    python scripts/import_shopify_dataset.py --source-dir /ruta/shopify-invoice-test-pack
    python scripts/import_shopify_dataset.py  # descarga la fuente desde GitHub
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "public" / "shopify"
SOURCE_URL = "https://github.com/SalorWorks/shopify-invoice-test-pack/archive/refs/heads/main.zip"


def obtener_fuente(source_dir: Path | None) -> tuple[Path, Path | None]:
    if source_dir:
        return source_dir, None
    temp_dir = Path(tempfile.mkdtemp(prefix="shopify-invoice-"))
    archive = temp_dir / "source.zip"
    urllib.request.urlretrieve(SOURCE_URL, archive)
    with zipfile.ZipFile(archive) as source_zip:
        source_zip.extractall(temp_dir)
    return next(temp_dir.glob("shopify-invoice-test-pack-*")), temp_dir


def convertir(gold: dict) -> dict:
    return {
        "nit_emisor": gold["supplier"].get("taxRegistration"),
        "nombre_emisor": gold["supplier"].get("name"),
        "nit_receptor": None,
        "nombre_receptor": gold.get("billTo"),
        "fecha": gold.get("invoiceDate"),
        "serie": None,
        "numero": gold.get("invoiceNumber"),
        "autorizacion": None,
        "lineas": [
            {
                "descripcion": line.get("description", ""),
                "cantidad": line.get("quantity"),
                "precio_unitario": line.get("unitPrice"),
                "total_linea": line.get("lineTotal"),
            }
            for line in gold.get("lines", [])
        ],
        "subtotal": gold.get("subtotal"),
        "iva": gold.get("tax"),
        "total": gold.get("total"),
        "moneda": gold.get("currency"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, help="checkout local de la fuente pública")
    args = parser.parse_args()
    source, temp_dir = obtener_fuente(args.source_dir)
    try:
        fixtures = sorted((source / "fixtures").glob("*/expected.json"))
        if not fixtures:
            raise SystemExit(f"No se encontraron fixtures en {source / 'fixtures'}")
        docs_dir = DEST / "docs"
        images_dir = DEST / "images"
        gold_dir = DEST / "gold"
        docs_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        gold_dir.mkdir(parents=True, exist_ok=True)
        for old_image in docs_dir.glob("*.png"):
            old_image.unlink()
        for expected_path in fixtures:
            fixture = expected_path.parent
            name = f"shopify_{fixture.name}"
            shutil.copy2(fixture / "invoice.pdf", docs_dir / f"{name}.pdf")
            shutil.copy2(fixture / "invoice.png", images_dir / f"{name}.png")
            gold = json.loads(expected_path.read_text(encoding="utf-8"))
            (gold_dir / f"{name}.json").write_text(
                json.dumps(convertir(gold), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        shutil.copy2(source / "LICENSE", DEST / "LICENSE")
        (DEST / "README.md").write_text(
            """# Dataset público Shopify Invoice Test Pack

Fuente: https://github.com/SalorWorks/shopify-invoice-test-pack
Licencia: CC BY 4.0. Las fixtures son sintéticas y se conservaron PDF/PNG.

Los `expected.json` originales se transformaron al esquema `Factura` del proyecto:
`supplier` -> emisor, `billTo` -> receptor, `invoiceNumber` -> numero,
`lines` -> lineas y `tax` -> iva. Los campos ausentes quedan en null.

Este conjunto se mantiene separado de `data/docs` y no se mezcla con la métrica de las 45
facturas FEL sintéticas. Algunas fixtures incluyen descuentos, flete o duty; los validadores
pueden marcarlas para revisión porque el esquema FEL actual no modela esos conceptos.
""",
            encoding="utf-8",
        )
        print(f"Importadas {len(fixtures)} fixtures en {DEST}")
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()