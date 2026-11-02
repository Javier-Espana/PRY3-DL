"""Genera facturas SINTÉTICAS (datos inventados) con su gold JSON.

Uso (desde la raíz del repo):
    python scripts/make_synthetic.py --n 45 --seed 2026

Salida: data/docs/sint_XXX.pdf|png y data/gold/sint_XXX.json

Variación intencional: 4 layouts de PDF, etiquetas distintas ("Total", "TOTAL A PAGAR"...),
3 formatos de fecha, separador de miles, 1-8 líneas, receptor CF o con NIT, un 10 % de
"pequeño contribuyente" (sin IVA) y ~25 % imágenes con rotación, ruido y desenfoque.
Todos los nombres, NIT y UUID son inventados; los NIT pasan el dígito verificador de
src/validators.py (que aún debe verificarse contra NITs reales).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from src.validators import nit_digito_valido  # noqa: E402

EMISORES = [
    "Distribuidora Los Volcanes", "Ferretería El Tornillo Feliz", "Café Altiplano", "Papelería La Ceiba",
    "Tecnoservicios Quetzal", "Panadería San Jerónimo", "Librería Pop Wuj", "Farmacia Vida Nueva",
    "Agroinsumos del Lago", "Imprenta Tikal", "Comercial Xelajú", "Taller Mecánico Chimaltenango",
    "Lácteos de Verapaz", "Muebles Atitlán", "Verdulería La Esperanza",
]
SUFIJOS = ["S.A.", "Ltda.", "y Cía.", "E.I.R.L."]
RECEPTORES = ["Constructora Motagua, S.A.", "Juan Pérez López", "María Sánchez Ajú", "Colegio Los Pinos",
              "Clínica Dental Sonrisas", "Restaurante El Fogón", "Rosa Tojín Cux"]
PRODUCTOS = [
    ("Café molido 1 lb", 45.0), ("Pan francés (docena)", 18.0), ("Resma papel carta", 52.5),
    ("Tornillo 1/2 pulg (caja)", 33.75), ("Cuaderno universitario", 14.0), ("Servicio de instalación", 250.0),
    ("Cable UTP cat6 (metro)", 6.5), ("Paracetamol 500 mg", 22.0), ("Fertilizante 50 lb", 189.0),
    ("Impresión banner", 120.0), ("Queso fresco 1 lb", 28.0), ("Aceite de motor 1 L", 75.0),
    ("Silla de oficina", 640.0), ("Mantenimiento mensual", 900.0), ("Tomate (caja)", 85.0),
]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]
ETIQ_TOTAL = ["Total", "TOTAL A PAGAR", "Gran Total", "Total Q."]
ETIQ_IVA = ["IVA", "IVA 12%", "Impuesto (IVA)"]
ETIQ_SUB = ["Subtotal", "Sub-total", "Valor neto"]


def nit_valido(rng: random.Random) -> str:
    cuerpo = "".join(str(rng.randint(0, 9)) for _ in range(rng.choice([6, 7])))
    total = sum(int(d) * f for d, f in zip(cuerpo, range(len(cuerpo) + 1, 1, -1)))
    r = (11 - total % 11) % 11
    nit = cuerpo + ("K" if r == 10 else str(r))
    assert nit_digito_valido(nit)
    return nit


def monto(x: float, miles: bool) -> str:
    return f"{x:,.2f}" if miles else f"{x:.2f}"


def fecha_txt(d: date, estilo: int) -> str:
    return [d.isoformat(), d.strftime("%d/%m/%Y"), f"{d.day} de {MESES[d.month - 1]} de {d.year}"][estilo]


def crear_caso(rng: random.Random, i: int) -> tuple[dict, dict]:
    """Devuelve (gold, estilo). El gold ya es consistente (subtotal + iva = total)."""
    pequeno = rng.random() < 0.10
    lineas = []
    for nombre, precio in rng.sample(PRODUCTOS, rng.randint(1, 8)):
        cant = rng.choice([1, 1, 2, 3, 5, 10, 0.5])
        precio = round(precio * rng.uniform(0.9, 1.15), 2)
        lineas.append({"descripcion": nombre, "cantidad": cant, "precio_unitario": precio,
                       "total_linea": round(cant * precio, 2)})
    suma = round(sum(l["total_linea"] for l in lineas), 2)
    # En FEL los precios suelen incluir IVA: aquí el total es la suma y el subtotal es total/1.12.
    if pequeno:
        subtotal, iva, total = suma, None, suma
    else:
        total = suma
        subtotal = round(total / 1.12, 2)
        iva = round(total - subtotal, 2)
    receptor_cf = rng.random() < 0.5
    emisor = f"{rng.choice(EMISORES)}, {rng.choice(SUFIJOS)}"
    gold = {
        "nit_emisor": nit_valido(rng), "nombre_emisor": emisor,
        "nit_receptor": "CF" if receptor_cf else nit_valido(rng),
        "nombre_receptor": "Consumidor Final" if receptor_cf else rng.choice(RECEPTORES),
        "fecha": (date(2026, 1, 1) + timedelta(days=rng.randint(0, 300))).isoformat(),
        "serie": "".join(rng.choices("ABCDEF0123456789", k=8)), "numero": str(rng.randint(10**8, 10**9 - 1)),
        "autorizacion": str(uuid.UUID(int=rng.getrandbits(128))).upper(),
        "lineas": lineas, "subtotal": subtotal, "iva": iva, "total": total, "moneda": "GTQ",
    }
    estilo = {
        "layout": rng.randint(0, 3), "fecha": rng.randint(0, 2), "miles": rng.random() < 0.5,
        "t": rng.choice(ETIQ_TOTAL), "iva": rng.choice(ETIQ_IVA), "sub": rng.choice(ETIQ_SUB),
        "imagen": rng.random() < 0.25, "pequeno": pequeno,
    }
    return gold, estilo


def lineas_texto(g: dict, e: dict) -> list[str]:
    """Texto del documento, línea por línea, según el layout."""
    fecha = fecha_txt(date.fromisoformat(g["fecha"]), e["fecha"])
    m = lambda x: monto(x, e["miles"])  # noqa: E731
    nit_e = f"{g['nit_emisor'][:-1]}-{g['nit_emisor'][-1]}"
    nit_r = g["nit_receptor"] if g["nit_receptor"] == "CF" else f"{g['nit_receptor'][:-1]}-{g['nit_receptor'][-1]}"
    cab = {
        0: [g["nombre_emisor"], f"NIT: {nit_e}", "FACTURA ELECTRÓNICA", f"Fecha: {fecha}",
            f"Serie: {g['serie']}  Número: {g['numero']}", f"Autorización: {g['autorizacion']}",
            f"Cliente: {g['nombre_receptor']}", f"NIT: {nit_r}"],
        1: ["DOCUMENTO TRIBUTARIO ELECTRÓNICO", f"Emisor: {g['nombre_emisor']} (NIT {nit_e})",
            f"Receptor: {g['nombre_receptor']} (NIT {nit_r})", f"Emitida el {fecha}",
            f"No. Autorización {g['autorizacion']}", f"Serie {g['serie']} / No. {g['numero']}"],
        2: [f"{g['nombre_emisor'].upper()}", f"NIT {nit_e}", f"Factura No. {g['numero']}  Serie {g['serie']}",
            f"Fecha de emisión {fecha}", f"Nombre: {g['nombre_receptor']}", f"NIT cliente: {nit_r}",
            f"Autorización: {g['autorizacion']}"],
        3: ["Factura", f"{g['nombre_emisor']}", f"NIT: {nit_e}", f"Serie: {g['serie']}", f"Número: {g['numero']}",
            f"Fecha: {fecha}", f"Cliente: {g['nombre_receptor']} - NIT: {nit_r}", f"UUID: {g['autorizacion']}"],
    }[e["layout"]]
    det = ["Cant.  Descripción                          P. Unit.      Total"]
    for l in g["lineas"]:
        cant = int(l["cantidad"]) if float(l["cantidad"]).is_integer() else l["cantidad"]
        det.append(f"{cant}   {l['descripcion']}   Q{m(l['precio_unitario'])}   Q{m(l['total_linea'])}")
    pie = []
    if g["iva"] is not None:
        pie += [f"{e['sub']}: Q{m(g['subtotal'])}", f"{e['iva']}: Q{m(g['iva'])}"]
    else:
        pie += ["Sujeto a pagos trimestrales (pequeño contribuyente)"]
    pie += [f"{e['t']}: Q{m(g['total'])}"]
    return cab + [""] + det + [""] + pie


def escribir_pdf(path: Path, filas: list[str], layout: int) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    fuente = ["Helvetica", "Times-Roman", "Courier", "Helvetica-Oblique"][layout]
    c.setFont(fuente, 10 if layout != 2 else 9)
    y = 740
    for fila in filas:
        c.drawString(50 if layout != 1 else 70, y, fila)
        y -= 16
    c.save()


def escribir_imagen(path: Path, filas: list[str], rng: random.Random) -> None:
    try:
        fuente = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    except OSError:
        fuente = ImageFont.load_default(size=22)
    img = Image.new("L", (1000, 60 + 32 * len(filas)), 255)
    d = ImageDraw.Draw(img)
    for k, fila in enumerate(filas):
        d.text((40, 30 + 32 * k), fila, fill=20, font=fuente)
    img = img.rotate(rng.uniform(-4, 4), expand=True, fillcolor=255)
    arr = np.asarray(img, dtype=np.float32) + np.random.default_rng(rng.getrandbits(32)).normal(0, 12, (img.height, img.width))
    img = Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 1.0)))
    img.save(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=45)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", type=Path, default=ROOT / "data")
    a = ap.parse_args()
    (a.out / "docs").mkdir(parents=True, exist_ok=True)
    (a.out / "gold").mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    for i in range(1, a.n + 1):
        gold, e = crear_caso(rng, i)
        nombre = f"sint_{i:03d}"
        filas = lineas_texto(gold, e)
        if e["imagen"]:
            escribir_imagen(a.out / "docs" / f"{nombre}.png", filas, rng)
        else:
            escribir_pdf(a.out / "docs" / f"{nombre}.pdf", filas, e["layout"])
        (a.out / "gold" / f"{nombre}.json").write_text(json.dumps(gold, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{a.n} facturas sintéticas en {a.out}")


if __name__ == "__main__":
    main()
