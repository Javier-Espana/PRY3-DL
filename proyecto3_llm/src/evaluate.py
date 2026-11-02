"""Evaluación contra el conjunto de referencia (gold).

Uso (desde proyecto3_llm/):
    python -m src.evaluate --system regex
    python -m src.evaluate --system llm --model claude-haiku-5-5 --prompt v1
    python -m src.evaluate --system llm --model claude-sonnet-5-5 --prompt v2 --retries 1

Convención: data/docs/<nombre>.pdf|png|jpg  <->  data/gold/<nombre>.json (mismo esquema que Factura).
Escribe results/<run>.json con métricas y el detalle por documento.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

from .schema import CAMPOS_ESCALARES, Factura

ROOT = Path(__file__).resolve().parent.parent
DOC_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def norm(valor, campo: str):
    """Normaliza para comparar sin penalizar diferencias de formato irrelevantes."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return round(float(valor), 2)
    s = re.sub(r"\s+", " ", str(valor)).strip().upper()
    if campo.startswith("nit"):
        s = re.sub(r"[\s-]", "", s)
    return s


def comparar(pred: Factura | None, gold: dict) -> dict[str, bool]:
    """Devuelve {campo: acierto}. Una predicción ausente falla todos los campos."""
    pred_d = pred.model_dump() if pred else {}
    out = {c: norm(pred_d.get(c), c) == norm(gold.get(c), c) for c in CAMPOS_ESCALARES}
    gl = sorted((norm(l.get("descripcion"), "d"), norm(l.get("cantidad"), "c"), norm(l.get("total_linea"), "t"))
                for l in gold.get("lineas", []))
    pl = sorted((norm(l.get("descripcion"), "d"), norm(l.get("cantidad"), "c"), norm(l.get("total_linea"), "t"))
                for l in pred_d.get("lineas", []))
    out["lineas"] = gl == pl
    return out


def listar_casos(docs: Path, gold: Path) -> list[tuple[Path, dict]]:
    casos = []
    for doc in sorted(docs.iterdir()):
        if doc.suffix.lower() in DOC_EXT and (gold / f"{doc.stem}.json").exists():
            casos.append((doc, json.loads((gold / f"{doc.stem}.json").read_text(encoding="utf-8"))))
    return casos


def evaluar(system: str, model: str, prompt: str, retries: int, docs: Path, gold: Path) -> dict:
    casos = listar_casos(docs, gold)
    if not casos:
        raise SystemExit(f"No hay casos: pon documentos en {docs} y su gold JSON en {gold}")
    detalle, lat, costo, tin, tout = [], [], 0.0, 0, 0
    for doc, g in casos:
        if system == "regex":
            from .baseline_regex import extraer_regex
            try:
                pred, err, problemas = extraer_regex(doc), None, []
            except Exception as e:  # el baseline no debe romper la evaluación
                pred, err, problemas = None, str(e), []
        else:
            from .extractor import extraer
            r = extraer(doc, modelo=model, prompt_version=prompt, max_reintentos=retries)
            pred, err, problemas = r.factura, r.error, r.problemas
            lat.append(r.latencia_s)
            costo += r.costo_usd
            tin += r.tokens_in
            tout += r.tokens_out
        aciertos = comparar(pred, g)
        detalle.append({"doc": doc.name, "aciertos": aciertos, "todo_ok": all(aciertos.values()),
                        "valido": pred is not None, "error": err, "problemas": problemas})
        print(f"{doc.name}: {sum(aciertos.values())}/{len(aciertos)} campos ok")
    n = len(detalle)
    campos = list(detalle[0]["aciertos"])
    metricas = {
        "n_documentos": n,
        "exactitud_por_campo": {c: round(sum(d["aciertos"][c] for d in detalle) / n, 4) for c in campos},
        "exactitud_global_campos": round(sum(sum(d["aciertos"].values()) for d in detalle) / (n * len(campos)), 4),
        "documentos_100_correctos": round(sum(d["todo_ok"] for d in detalle) / n, 4),
        "salida_valida": round(sum(d["valido"] for d in detalle) / n, 4),
    }
    if lat:
        metricas.update({
            "latencia_media_s": round(statistics.mean(lat), 3),
            "tokens_entrada": tin, "tokens_salida": tout,
            "costo_total_usd": round(costo, 4), "costo_por_documento_usd": round(costo / n, 5),
        })
    return {"config": {"system": system, "model": model if system == "llm" else None,
                       "prompt": prompt if system == "llm" else None, "retries": retries},
            "metricas": metricas, "detalle": detalle}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=["regex", "llm"], required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--prompt", default="v2")
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--docs", type=Path, default=ROOT / "data" / "docs")
    ap.add_argument("--gold", type=Path, default=ROOT / "data" / "gold")
    a = ap.parse_args()
    salida = evaluar(a.system, a.model, a.prompt, a.retries, a.docs, a.gold)
    nombre = "regex" if a.system == "regex" else f"{a.model}_{a.prompt}_r{a.retries}"
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"{nombre}.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(salida["metricas"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
