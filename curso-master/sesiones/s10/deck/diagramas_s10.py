"""Genera los diagramas propios de la Sesión 10 (los que no cubren las 6 diapos de LIDR).

Reutiliza el helper ``Svg`` de los diagramas de la Sesión 7 para mantener el mismo estilo.

    python diagramas_s10.py
    # → curso-master/assets/s10-*.svg   (build_deck.py los rasteriza a PNG)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "s07" / "deck"))
from diagramas_estrategias import C, H, W, Svg  # noqa: E402

RRF_K = 60


def rrf() -> None:
    s = Svg("RRF: fusiona por posición, no por puntuación",
            f"score(d) = Σ 1 / (k + rank)  ·  k = {RRF_K}  ·  consulta «integration with Stripe Connect» (ilustrativo)")
    vector = ["AUTH-001", "PAY-002", "STRIPE-003", "CART-004"]
    lexica = ["STRIPE-003", "PSP-005", "PAY-002"]
    cols = {"STRIPE-003": "green", "PAY-002": "blue", "AUTH-001": "grey", "PSP-005": "grey", "CART-004": "grey"}
    for x, title, lst, sub in ((24, "Rama vectorial", vector, "embeddings: «se parece»"),
                               (214, "Rama léxica", lexica, "tsvector: palabras exactas")):
        s.text(x + 85, 74, title, 12, bold=True, anchor="middle")
        s.text(x + 85, 89, sub, 10, "#64748b", anchor="middle")
        for i, doc in enumerate(lst):
            s.label_box(x, 98 + i * 40, 170, 32, [f"#{i + 1}  {doc}"], cols[doc], 11, center=True)
    scores = {}
    for lst in (vector, lexica):
        for i, doc in enumerate(lst):
            scores[doc] = scores.get(doc, 0) + 1 / (RRF_K + i + 1)
    s.arrow(392, 170, 432, 170, label="RRF")
    s.text(590, 74, "Ranking fusionado", 12, bold=True, anchor="middle")
    s.text(590, 89, "suma de 1/(60 + posición) en cada lista", 10, "#64748b", anchor="middle")
    for i, (doc, sc) in enumerate(sorted(scores.items(), key=lambda kv: -kv[1])):
        both = doc in vector and doc in lexica
        s.label_box(440, 98 + i * 40, 300, 32, [f"#{i + 1}  {doc}   {sc:.4f}".replace(".", ",") + ("   ← en las dos" if both else "")],
                    "green" if both else "grey", 11)
    s.box(24, 312, 712, 36, "amber", r=8)
    s.text(380, 335, "AUTH-001 era el #1 vectorial y cae al #3: gana quien va bien en las DOS ramas. "
                     "k grande aplana; k pequeño deja dominar a un #1.", 10.5, C["amber"][2], anchor="middle", bold=True)
    s.footer("Rankings, no scores: la distancia del vector y ts_rank_cd no son comparables entre sí")
    s.save("s10-rrf")


def rerank() -> None:
    s = Svg("Recall-then-rerank: bi-encoder para buscar, cross-encoder para ordenar",
            "El reranking del ejercicio previo: hoy no se reprograma, se compone y se mide")
    s.box(24, 66, 340, 150, "blue")
    s.text(194, 88, "Bi-encoder (embeddings)", 13, C["blue"][2], bold=True, anchor="middle")
    s.label_box(40, 100, 130, 36, ["consulta → vector"], "grey", 10.5, center=True)
    s.label_box(218, 100, 130, 36, ["doc → vector"], "grey", 10.5, center=True)
    s.text(194, 156, "por separado · se compara con coseno", 10.5, C["blue"][2], anchor="middle")
    s.text(194, 176, "barato: sirve para miles de chunks", 10.5, C["blue"][2], anchor="middle", bold=True)
    s.text(194, 196, "pero confunde «mismo tema» con «misma cosa»", 10, C["blue"][2], anchor="middle", italic=True)
    s.box(396, 66, 340, 150, "violet")
    s.text(566, 88, "Cross-encoder (reranker)", 13, C["violet"][2], bold=True, anchor="middle")
    s.label_box(470, 100, 192, 36, ["(consulta, doc) → score"], "grey", 10.5, center=True)
    s.text(566, 156, "los lee JUNTOS en una pasada del modelo", 10.5, C["violet"][2], anchor="middle")
    s.text(566, 176, "preciso, pero una inferencia por par", 10.5, C["violet"][2], anchor="middle", bold=True)
    s.text(566, 196, "imposible sobre todo el corpus", 10, C["violet"][2], anchor="middle", italic=True)
    steps = [("Corpus", "miles de chunks", "dark"), ("Recall", "top 50 (bi-encoder)", "blue"),
             ("Rerank", "cross-encoder sobre 50", "violet"), ("Top-N", "los 5 mejores", "green")]
    for i, (t, sub, col) in enumerate(steps):
        x = 24 + i * 184
        s.label_box(x, 236, 160, 50, [t, sub], col, 11, bold_first=True, center=True)
        if i < 3:
            s.arrow(x + 162, 261, x + 182, 261)
    s.box(24, 298, 712, 50, "amber", r=8)
    s.text(380, 318, "Coste: ~80 s la primera vez (carga del modelo) y luego cientos de ms. Calentar antes de clase.", 10.5,
           C["amber"][2], anchor="middle", bold=True)
    s.text(380, 336, "En el arnés: +2,6 s sobre el vectorial. En las horas por tarea: menos filas rojas.", 10.5,
           C["amber"][2], anchor="middle")
    s.footer("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 · multilingüe · CPU · off por defecto")
    s.save("s10-rerank")


def decay() -> None:
    half = 900
    s = Svg("Decaimiento temporal: preferir lo reciente sin descartar lo antiguo",
            f"weight = 0,5 ^ (edad_días / {half})  ·  semivida de {half} días (≈ 2,5 años)")
    x0, x1, y0, y1, dmax = 70, 470, 300, 80, 2000
    sx = lambda d: x0 + (x1 - x0) * d / dmax
    sy = lambda w: y0 - (y0 - y1) * w
    s.line(x0, y0, x1, y0, "#334155", 1.5)
    s.line(x0, y0, x0, y1 - 6, "#334155", 1.5)
    for w in (0, 0.25, 0.5, 0.75, 1):
        s.line(x0 - 4, sy(w), x1, sy(w), "#e2e8f0", 1)
        s.text(x0 - 8, sy(w) + 4, f"{w:g}".replace(".", ","), 10, "#475569", anchor="end")
    for d in (0, 365, 900, 1825):
        s.line(sx(d), y0, sx(d), y0 + 5, "#334155", 1.2)
    for d, lab in ((0, "hoy"), (365, "1 año"), (900, "2,5 años"), (1825, "5 años")):
        s.text(sx(d), y0 + 18, lab, 10, "#475569", anchor="middle")
    pts = " ".join(f"{sx(d):.1f},{sy(0.5 ** (d / half)):.1f}" for d in range(0, dmax + 1, 25))
    s.o.append(f'<polyline points="{pts}" fill="none" stroke="#d97706" stroke-width="3"/>')
    for d in (365, 900, 1825):
        w = 0.5 ** (d / half)
        s.o.append(f'<circle cx="{sx(d):.1f}" cy="{sy(w):.1f}" r="5" fill="#d97706"/>')
        s.text(sx(d) + 8, sy(w) - 8, f"{w:.2f}".replace(".", ","), 11, C["amber"][2], bold=True)
    s.text((x0 + x1) / 2, y0 + 36, "edad del presupuesto", 10.5, "#475569", anchor="middle")
    s.box(500, 70, 236, 104, "green")
    s.text(512, 92, "Por qué al cierre", 12, C["green"][2], bold=True)
    for i, t in enumerate(["Es ponderación BLANDA: solo", "desempata entre finalistas ya", "relevantes. Antes del rerank",
                           "penalizaría lo que no sabes si sirve."]):
        s.text(512, 112 + i * 16, t, 10.5, C["green"][2])
    s.box(500, 184, 236, 104, "violet")
    s.text(512, 206, "Por qué sigmoid antes", 12, C["violet"][2], bold=True)
    for i, t in enumerate(["El logit del cross-encoder puede", "ser negativo: × 0,5 lo «sube».",
                           "sigmoid lo lleva a (0, 1) y el", "decaimiento solo atenúa."]):
        s.text(512, 226 + i * 16, t, 10.5, C["violet"][2])
    s.footer("Off por defecto (TEMPORAL_DECAY_ENABLED=false): encenderlo solo con evidencia")
    s.save("s10-decaimiento")


if __name__ == "__main__":
    for fn in (rrf, rerank, decay):
        fn()
