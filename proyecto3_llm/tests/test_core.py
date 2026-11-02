from types import SimpleNamespace

from src.baseline_regex import extraer_regex_texto
from src.evaluate import comparar, norm
from src.extractor import extraer
from src.schema import Factura, Linea
from src.validators import nit_digito_valido, validar


def _ok() -> Factura:
    return Factura(
        nit_emisor="CF", fecha="2026-10-15", subtotal=100.0, iva=12.0, total=112.0,
        lineas=[Linea(descripcion="Café", cantidad=2, precio_unitario=50.0, total_linea=100.0)],
    )


def test_factura_consistente_sin_problemas():
    assert validar(_ok()) == []


def test_detecta_total_incorrecto():
    f = _ok().model_copy(update={"total": 150.0})
    assert any("no coincide" in p for p in validar(f))


def test_detecta_iva_incorrecto():
    f = _ok().model_copy(update={"iva": 30.0, "total": 130.0})
    assert any("12%" in p for p in validar(f))


def test_fecha_invalida():
    f = _ok().model_copy(update={"fecha": "2026-13-45"})
    assert any("fecha" in p for p in validar(f))


def test_nit_digito_verificador_autoconsistente():
    # Construimos un NIT válido con el mismo algoritmo (ver advertencia en validators.py).
    cuerpo = "123456"
    total = sum(int(d) * f for d, f in zip(cuerpo, range(len(cuerpo) + 1, 1, -1)))
    r = (11 - total % 11) % 11
    verif = "K" if r == 10 else str(r)
    assert nit_digito_valido(cuerpo + "-" + verif)
    assert not nit_digito_valido(cuerpo + "-" + ("0" if verif != "0" else "1"))
    assert nit_digito_valido("CF")


def test_normalizacion_y_comparacion():
    assert norm("1234567-K", "nit_emisor") == norm("1234567 k", "nit_emisor")
    gold = _ok().model_dump()
    assert all(comparar(_ok(), gold).values())
    assert not comparar(None, gold)["total"]


def test_baseline_regex_extrae_basicos():
    texto = "NIT: 1234567-8\nFecha: 2026-10-15\nIVA: Q 12.00\nTotal: Q 112.00"
    f = extraer_regex_texto(texto)
    assert f.total == 112.0 and f.iva == 12.0 and f.fecha == "2026-10-15"


def test_reintento_cuando_hay_problemas(tmp_path):
    """Cliente falso: la primera respuesta es inconsistente, la segunda correcta."""
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    malo = _ok().model_copy(update={"total": 999.0})
    respuestas = [malo, _ok()]
    llamadas = []

    class FakeMessages:
        def parse(self, **kwargs):
            llamadas.append(kwargs)
            return SimpleNamespace(
                parsed_output=respuestas[len(llamadas) - 1], stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
            )

    r = extraer(pdf, modelo="claude-haiku-5-5", max_reintentos=1, client=SimpleNamespace(messages=FakeMessages()))
    assert r.intentos == 2 and r.problemas == [] and r.factura.total == 112.0
    assert r.tokens_in == 2000 and r.costo_usd > 0
    assert "temperature" not in llamadas[0]


def test_formato_no_soportado_no_lanza(tmp_path):
    txt = tmp_path / "x.txt"
    txt.write_text("hola")
    r = extraer(txt, client=SimpleNamespace())
    assert r.factura is None and "Formato no soportado" in r.error


def test_generador_sintetico_es_consistente_y_reproducible():
    import random

    from scripts.make_synthetic import crear_caso

    g1, _ = crear_caso(random.Random(7), 1)
    g2, _ = crear_caso(random.Random(7), 1)
    assert g1 == g2
    for seed in range(30):
        g, _ = crear_caso(random.Random(seed), 1)
        assert validar(Factura(**g)) == []
