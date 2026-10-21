"""Genera los 8 diagramas de las estrategias de chunking (uno por estrategia del código).

Todos los ejemplos salen de ejecutar las estrategias reales sobre data/budgets_sample.json
(worktree ai-engineering-s07, 21/10/2026), salvo el párrafo de Contextual Retrieval, que va
marcado como ilustrativo porque esa estrategia necesita la clave de Anthropic.

    python diagramas_estrategias.py
    # → curso-master/assets/s07-est-*.svg   (build_deck.py los rasteriza a PNG)
"""

from __future__ import annotations

import html
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent.parent.parent / "assets"
W, H = 760, 400
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "Consolas, Courier New, monospace"

# relleno, borde, tinta
C = {
    "blue": ("#dbeafe", "#2563eb", "#1e3a8a"),
    "violet": ("#ede9fe", "#7c3aed", "#4c1d95"),
    "amber": ("#fef3c7", "#d97706", "#78350f"),
    "green": ("#dcfce7", "#16a34a", "#14532d"),
    "red": ("#fee2e2", "#dc2626", "#7f1d1d"),
    "sky": ("#e0f2fe", "#0284c7", "#0c4a6e"),
    "pink": ("#fce7f3", "#db2777", "#831843"),
    "grey": ("#f1f5f9", "#94a3b8", "#334155"),
    "dark": ("#e2e8f0", "#64748b", "#0f172a"),
}


class Svg:
    def __init__(self, title: str, subtitle: str = "") -> None:
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}">',
                  f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']
        self.text(W / 2, 28, title, 18, bold=True, anchor="middle")
        if subtitle:
            self.text(W / 2, 48, subtitle, 11.5, color="#64748b", anchor="middle")

    def text(self, x, y, s, size=11, color="#0f172a", bold=False, anchor="start", mono=False, italic=False):
        attrs = f'font-size="{size}" fill="{color}" text-anchor="{anchor}"'
        if bold:
            attrs += ' font-weight="700"'
        if italic:
            attrs += ' font-style="italic"'
        if mono:
            attrs += f' font-family="{MONO}"'
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" {attrs}>{html.escape(s)}</text>')

    def box(self, x, y, w, h, color="grey", r=8, sw=1.5, dash=False, opacity=1.0):
        fill, stroke, _ = C[color]
        d = ' stroke-dasharray="5 4"' if dash else ""
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" '
                      f'fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def label_box(self, x, y, w, h, lines, color="grey", size=11, mono=False, bold_first=False, center=False):
        self.box(x, y, w, h, color)
        ink = C[color][2]
        lh = size * 1.35
        top = y + (h - lh * len(lines)) / 2 + size
        for i, s in enumerate(lines):
            self.text(x + w / 2 if center else x + 8, top + i * lh, s, size, ink,
                      bold=bold_first and i == 0, anchor="middle" if center else "start", mono=mono and i > 0)

    def arrow(self, x1, y1, x2, y2, color="#475569", width=2.2, label="", label_dy=-6):
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - 10 * math.cos(ang), y2 - 10 * math.sin(ang)
        px, py = -math.sin(ang) * 5.5, math.cos(ang) * 5.5
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{width}"/>')
        self.o.append(f'<polygon points="{x2:.1f},{y2:.1f} {bx + px:.1f},{by + py:.1f} {bx - px:.1f},{by - py:.1f}" fill="{color}"/>')
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 + label_dy, label, 10.5, "#475569", anchor="middle", bold=True)

    def line(self, x1, y1, x2, y2, color="#94a3b8", width=1.5, dash=False):
        d = ' stroke-dasharray="4 3"' if dash else ""
        self.o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{d}/>')

    def footer(self, s, color="#475569"):
        self.box(20, H - 46, W - 40, 32, "grey", r=8, sw=1)
        self.text(W / 2, H - 25, s, 11.5, color, anchor="middle", bold=True)

    def save(self, name: str) -> None:
        self.o.append("</svg>")
        (ASSETS / f"{name}.svg").write_text("\n".join(self.o), encoding="utf-8")
        print(f"{name}.svg")


# ---------------------------------------------------------------------------

def fixed() -> None:
    s = Svg("Fixed-size: ventanas de 512 tokens, solapadas 80",
            "Ejemplo real: BUD-2024-016 · MONO-001, el componente gigante de 1391 tokens")
    x0, x1, total = 50, 710, 1391
    sx = lambda t: x0 + (x1 - x0) * t / total
    s.box(x0, 64, x1 - x0, 26, "dark", r=5)
    s.text((x0 + x1) / 2, 81, "el componente entero: 1391 tokens", 11.5, "#0f172a", bold=True, anchor="middle")
    parts = [("p0", 0, 512, "blue"), ("p1", 432, 944, "violet"), ("p2", 864, 1376, "amber"), ("p3", 1296, 1391, "green")]
    for i, (n, a, b, col) in enumerate(parts):
        y = 104 + i * 36
        s.box(sx(a), y, sx(b) - sx(a), 28, col, r=5)
        lab = f"{n} · {b - a} tokens"
        if b - a > 200:
            s.text((sx(a) + sx(b)) / 2, y + 18, lab, 11, C[col][2], bold=True, anchor="middle")
        else:
            s.text(sx(a) - 8, y + 18, lab, 11, C[col][2], bold=True, anchor="end")
    for a, b, y in ((432, 512, 104), (864, 944, 140), (1296, 1376, 176)):
        s.o.append(f'<rect x="{sx(a):.1f}" y="{y}" width="{sx(b) - sx(a):.1f}" height="64" fill="#0f172a" fill-opacity="0.13"/>')
    s.text(sx(472), 98, "80 repetidos", 10, "#334155", anchor="middle", bold=True)
    s.line(x0, 254, x1, 254, "#334155", 1.2)
    for t in (0, 512, 1024, 1391):
        s.line(sx(t), 254, sx(t), 259, "#334155", 1.2)
        s.text(sx(t), 271, str(t), 10, "#334155", anchor="middle")
    s.text(x1, 286, "tokens", 10, "#64748b", anchor="end")
    s.box(50, 292, 660, 54, "red", r=8)
    s.text(62, 312, "Dónde cae el corte (texto real)", 11.5, C["red"][2], bold=True)
    s.text(62, 332, "p3 empieza en «it knowledge is the single largest project risk…»: la palabra anterior quedó partida.", 11,
           C["red"][2])
    s.footer("Los otros 59 componentes miden menos de 512 tokens: ahí no corta nada (1 componente = 1 chunk)")
    s.save("s07-est-fixed")


def recursive() -> None:
    s = Svg("Recursive: corta por el separador más grande que pueda",
            "Solo baja al siguiente separador si el trozo sigue pasando de 512 tokens")
    steps = [("1", "párrafo", "\\n\\n"), ("2", "línea", "\\n"), ("3", "frase", "\". \""), ("4", "palabra", "\" \"")]
    for i, (n, name, sep) in enumerate(steps):
        y = 66 + i * 50
        s.label_box(24, y, 150, 38, [f"{n} · {name}", sep], ["green", "sky", "amber", "red"][i], 11, mono=True,
                    bold_first=True, center=True)
        if i < 3:
            s.arrow(99, y + 38, 99, y + 50, width=1.8)
    # caso A
    s.text(200, 76, "BUD-2024-001 · 278 tokens → cabe entero", 12, bold=True)
    s.box(200, 84, 250, 104, "blue")
    s.text(212, 102, "r0 · un solo chunk", 11, C["blue"][2], bold=True)
    for i, comp in enumerate(["AUTH-001", "PSD2-002", "TXN-003", "NOTIF-004"]):
        s.label_box(212 + (i % 2) * 118, 112 + (i // 2) * 34, 108, 26, [comp], "grey", 10.5, center=True)
    s.text(200, 206, "4 componentes distintos, un solo vector", 11, C["red"][2], bold=True)
    # caso B
    s.text(476, 76, "BUD-2024-016 · 1472 tokens → 7 chunks", 12, bold=True)
    rows = [("r0", 41, "cabecera"), ("r1", 10, "solo el nombre"), ("r2", 457, "descripción 1/3"),
            ("r3", 492, "descripción 2/3"), ("r4", 494, "descripción 3/3"), ("r5", 27, "stack y horas"),
            ("r6", 74, "MONO-002 entero")]
    for i, (n, tok, what) in enumerate(rows):
        y = 86 + i * 25
        w = max(6, 90 * tok / 494)
        col = "red" if tok < 20 else ("amber" if tok > 400 else "violet")
        s.box(476, y, w, 18, col, r=3, sw=1.2)
        s.text(476 + w + 6, y + 13, f"{n} · {tok} tok · {what}", 10.5, C[col][2] if col == "red" else "#334155",
               bold=col == "red")
    s.text(476, 274, "r1 es un huérfano (10 tokens)", 11, C["red"][2], bold=True)
    s.footer("En nuestro corpus: 23 chunks para 17 presupuestos · casi todos caben enteros en uno")
    s.save("s07-est-recursive")


def sentence_window() -> None:
    s = Svg("Sentence-window: se busca por frase, se devuelve la ventana",
            "Ejemplo real: MONO-001 partido en frases (WINDOW_SIZE = 2)")
    sents = ["This component covers the full extraction of the general ledger…",
             "The work begins with a complete reverse-engineering exercise…",
             "Each stored procedure is catalogued, its inputs and outputs…",
             "Once the golden master is in place, the new service is built…",
             "Then the write path is migrated account-product by account-product…",
             "Every write is dual-written to both systems during a bake-in…",
             "The component also includes the design of the event schema…"]
    for i, t in enumerate(sents):
        y = 62 + i * 33
        if i == 3:
            col = "blue"
        elif 1 <= i <= 5:
            col = "sky"
        else:
            col = "grey"
        s.box(24, y, 420, 27, col, r=5, sw=2.4 if i == 3 else 1.2)
        s.text(32, y + 18, f"s{i}  {t}", 10.5, C[col][2], bold=i == 3)
    s.o.append('<path d="M 452 98 L 460 98 L 460 252 L 452 252" fill="none" stroke="#0284c7" stroke-width="2"/>')
    s.text(468, 150, "ventana ±2", 11, C["sky"][2], bold=True)
    s.text(468, 165, "(metadata.window_text)", 10, C["sky"][2])
    s.text(468, 180, "→ es lo que recibe el LLM", 10.5, C["sky"][2])
    s.text(468, 210, "s3 → lo único que se", 10.5, C["blue"][2], bold=True)
    s.text(468, 224, "embebe y se busca", 10.5, C["blue"][2], bold=True)
    s.box(600, 62, 140, 190, "red")
    s.text(670, 82, "El riesgo", 12, C["red"][2], bold=True, anchor="middle")
    s.text(670, 104, "BUD-2024-017 · MVP-001", 10, C["red"][2], anchor="middle")
    s.text(670, 126, "«Email and", 11.5, C["red"][2], anchor="middle", bold=True)
    s.text(670, 142, "password login.»", 11.5, C["red"][2], anchor="middle", bold=True)
    s.text(670, 162, "5 tokens", 10.5, C["red"][2], anchor="middle")
    s.text(670, 190, "Sale #2 (0,441) para", 10, C["red"][2], anchor="middle")
    s.text(670, 204, "«OAuth authentication", 10, C["red"][2], anchor="middle")
    s.text(670, 218, "for fintech mobile app»", 10, C["red"][2], anchor="middle")
    s.text(670, 238, "sin saber que es un MVP", 10, C["red"][2], anchor="middle", italic=True)
    s.footer("En nuestro corpus: 78 chunks · p50 de 21 tokens · 34 huérfanos")
    s.save("s07-est-sentence")


def structural() -> None:
    s = Svg("Structural: un componente = un chunk, con la cabecera del padre",
            "Ejemplo real: BUD-2024-001 → 4 chunks")
    s.box(24, 70, 200, 230, "dark")
    s.text(124, 92, "Presupuesto (JSON)", 12, bold=True, anchor="middle")
    for i, t in enumerate(["BUD-2024-001", "finance · 2024", "ruby_on_rails"]):
        s.text(36, 116 + i * 17, t, 10.5, "#334155", mono=True)
    comps = [("AUTH-001", "OAuth 2.0 authentication backend", 106), ("PSD2-002", "PSD2 open banking connectors", 96),
             ("TXN-003", "Transaction ledger service", 93), ("NOTIF-004", "Push and email notifications", 88)]
    for i, (cid, name, tok) in enumerate(comps):
        y = 172 + i * 30
        s.label_box(36, y, 176, 24, [cid], "grey", 10.5, center=True)
        cy = 66 + i * 64
        s.arrow(214, y + 12, 268, cy + 26, width=1.6)
        s.box(272, cy, 464, 56, "blue")
        s.box(280, cy + 6, 448, 18, "amber", r=4, sw=1)
        s.text(286, cy + 19, "[Project: Mobile banking API…] [finance | 2024 | ruby_on_rails]", 10, C["amber"][2], mono=True)
        s.text(286, cy + 44, f"Component: {name}  ·  descripción · stack · horas", 10.5, C["blue"][2])
        s.text(728, cy + 44, f"{tok} tok", 10.5, C["blue"][2], bold=True, anchor="end")
    s.footer("En nuestro corpus: 60 chunks · p50 de 78 tokens · 1 obeso (MONO-001: no lo parte, lo deja ver) · 0 $")
    s.save("s07-est-structural")


def semantic() -> None:
    s = Svg("Semantic: corta donde más cambia el significado",
            "Ejemplo real: BUD-2024-001 · distancia entre trozos consecutivos = 1 − coseno")
    pieces = ["[Project…] [Client…]  AUTH-001: nombre + descripción",
              "AUTH-001: stack y horas  ·  PSD2-002: nombre + descripción",
              "PSD2-002: stack y horas  ·  TXN-003: nombre + descripción",
              "TXN-003: stack y horas  ·  NOTIF-004: nombre + descripción",
              "NOTIF-004: stack y horas"]
    cols = ["blue", "blue", "violet", "violet", "violet"]
    for i, t in enumerate(pieces):
        y = 64 + i * 46
        s.box(24, y, 380, 30, cols[i], r=5)
        s.text(34, y + 20, f"{i}  {t}", 10.5, C[cols[i]][2])
    s.text(214, 302, "sem0 = trozos 0-1 (150 tok)  ·  sem1 = trozos 2-4 (128 tok)", 10.5, "#334155", anchor="middle",
           bold=True)
    # distancias reales
    dists = [0.0255, 0.1636, 0.0930, 0.1225]
    bx0, bscale = 450, 1050
    s.text(450, 74, "distancia entre trozos", 11, "#334155", bold=True)
    for i, dval in enumerate(dists):
        y = 64 + i * 46 + 30
        cut = dval > 0.1574
        s.box(bx0, y, dval * bscale, 16, "red" if cut else "grey", r=3, sw=1.2)
        s.text(bx0 + dval * bscale + 6, y + 12, f"{dval:.3f}".replace(".", ",") + ("  ← CORTE" if cut else ""), 10.5,
               C["red"][2] if cut else "#334155", bold=cut)
    tx = bx0 + 0.1574 * bscale
    s.line(tx, 80, tx, 270, "#dc2626", 1.5, dash=True)
    s.text(tx, 284, "percentil 95 = 0,157", 10.5, C["red"][2], anchor="middle", bold=True)
    s.box(24, 312, 712, 40, "amber", r=8)
    s.text(34, 328, "Parte el texto por «. »: cada trozo junta el final de un componente con el principio del siguiente.", 10.5,
           C["amber"][2])
    s.text(34, 344, "Resultado: la descripción de PSD2-002 queda en un chunk y su stack y sus horas, en el otro.", 10.5,
           C["amber"][2], bold=True)
    s.footer("En nuestro corpus: 34 chunks (17 × 2: un corte por presupuesto) · 0,000094 $ · 5,3 s de ingesta")
    s.save("s07-est-semantic")


def propositional() -> None:
    s = Svg("Propositional: un LLM reescribe el componente en frases atómicas",
            "Ejemplo real: AUTH-001 con gpt-4o-mini → 15 proposiciones")
    s.box(24, 70, 196, 210, "blue")
    s.text(122, 92, "Chunk de AUTH-001", 12, C["blue"][2], bold=True, anchor="middle")
    for i, t in enumerate(["[Project…] [finance…]", "Component: OAuth 2.0", "authentication backend",
                           "Description: OAuth 2.0", "flows, JWT sessions,", "multi-tenant, rate", "limiting…",
                           "Stack · Complexity · Hours"]):
        s.text(34, 114 + i * 19, t, 10.5, C["blue"][2], mono=True)
    s.text(122, 272, "106 tokens", 11, C["blue"][2], bold=True, anchor="middle")
    s.arrow(224, 175, 266, 175, label="LLM")
    props = [("The project focuses on a Mobile banking API.", 9), ("…will use OAuth 2.0 authentication.", 13),
             ("…will be compliant with PSD2 standards.", 12), ("The client sector is finance.", 6),
             ("The project is scheduled for the year 2024.", 11), ("The main technology … is Ruby on Rails.", 12),
             ("…is an OAuth 2.0 authentication backend.", 14), ("…will implement authorization code flows.", 14),
             ("…will implement refresh token flows.", 14), ("…will utilize JWT-based session management.", 15),
             ("…will provide multi-tenant token isolation.", 16), ("…will include rate limiting per client.", 15),
             ("…includes Ruby on Rails, PostgreSQL…", 22), ("The complexity … is high.", 14),
             ("The estimated hours … is 120 hours.", 18)]
    for i, (t, tok) in enumerate(props):
        col, row = divmod(i, 8)
        x, y = 272 + col * 236, 62 + row * 27
        c = "grey" if i < 6 else "green"
        s.box(x, y, 228, 23, c, r=11, sw=1.1)
        s.text(x + 9, y + 15.5, f"{i}. {t}", 9.5, C[c][2])
        s.text(x + 222, y + 15.5, str(tok), 9.5, C[c][2], bold=True, anchor="end")
    s.text(272, 300, "Grises: hablan del proyecto, no del componente → se repiten en cada componente", 10.5,
           "#334155", bold=True)
    s.text(272, 318, "15 chunks de 6 a 22 tokens: casi todos huérfanos (< 20), pero cada uno se entiende solo", 10.5,
           C["green"][2], bold=True)
    s.footer("En nuestro corpus: 778 chunks · 765 huérfanos · 0,00755 $ · 173 s de ingesta (una llamada por componente)")
    s.save("s07-est-propositional")


def contextual() -> None:
    s = Svg("Contextual Retrieval: el LLM escribe el contexto que le falta al chunk",
            "Técnica de Anthropic · en el código, con Claude Sonnet y prompt caching")
    s.label_box(24, 70, 180, 64, ["Presupuesto entero", "se envía una vez y", "queda en caché"], "dark", 10.5,
                bold_first=True, center=True)
    s.label_box(24, 150, 180, 64, ["Chunk structural", "AUTH-001", "(106 tokens)"], "blue", 10.5, bold_first=True,
                center=True)
    s.arrow(206, 102, 262, 136)
    s.arrow(206, 182, 262, 150)
    s.label_box(266, 112, 120, 60, ["Claude", "«sitúa este chunk", "en el documento»"], "violet", 10.5,
                bold_first=True, center=True)
    s.arrow(388, 142, 430, 142)
    s.box(434, 64, 304, 188, "green")
    s.text(446, 84, "Chunk enriquecido = contexto + chunk", 11.5, C["green"][2], bold=True)
    s.box(444, 94, 284, 88, "amber", r=6, sw=1.2)
    for i, t in enumerate(["This chunk describes the OAuth 2.0", "authentication backend of FintechCorp's",
                           "mobile banking API, the security layer that", "the PSD2 connectors and the ledger rely on."]):
        s.text(452, 112 + i * 17, t, 10, C["amber"][2], mono=True)
    s.text(444, 196, "+  [Project…] Component: OAuth 2.0…", 10.5, C["green"][2], mono=True)
    s.text(444, 216, "   Description · Stack · Hours", 10.5, C["green"][2], mono=True)
    s.text(444, 242, "Párrafo de ejemplo ilustrativo", 10, "#64748b", italic=True)
    s.box(24, 268, 714, 54, "grey", r=8, sw=1)
    s.text(36, 288, "Caché: el primer chunk de cada presupuesto paga el documento (3,75 $/M); los demás lo leen a 0,30 $/M.",
           10.5, "#334155")
    s.text(36, 308, "AUTH-001 para «OAuth authentication for fintech mobile app»: 0,568 → 0,607 (+0,04).", 10.5, "#334155",
           bold=True)
    s.footer("En nuestro corpus: 60 chunks · p50 de 132,5 tokens (78 + contexto) · 0,14 $ · 203 s de ingesta")
    s.save("s07-est-contextual")


def hierarchical() -> None:
    s = Svg("Hierarchical: indexa hijos y padres a la vez",
            "Ejemplo real: BUD-2024-001 → 1 padre + 4 hijos en el mismo índice")
    s.box(24, 64, 440, 50, "violet")
    s.text(244, 84, "PADRE · BUD-2024-001::parent · 278 tokens", 12, C["violet"][2], bold=True, anchor="middle")
    s.text(244, 102, "el presupuesto entero: contexto completo para el LLM", 10.5, C["violet"][2], anchor="middle")
    kids = [("AUTH-001", 106), ("PSD2-002", 96), ("TXN-003", 93), ("NOTIF-004", 88)]
    for i, (cid, tok) in enumerate(kids):
        x = 24 + i * 112
        s.line(244, 114, x + 50, 152, "#7c3aed", 1.4, dash=True)
        s.label_box(x, 152, 104, 52, ["HIJO", cid, f"{tok} tokens"], "blue", 10.5, bold_first=True, center=True)
    s.text(244, 226, "cada hijo guarda metadata.parent_chunk_id", 10.5, "#334155", anchor="middle", italic=True)
    steps = [("1", "La consulta encuentra un HIJO", "pequeño y preciso → buen recall", "blue"),
             ("2", "Se resuelve su PADRE", "parent_chunk_id → presupuesto entero", "violet"),
             ("3", "El LLM recibe el PADRE", "con todo el contexto para responder", "green")]
    for i, (n, t, sub, col) in enumerate(steps):
        y = 64 + i * 64
        s.label_box(490, y, 248, 50, [f"{n} · {t}", sub], col, 10.5, bold_first=True)
        if i < 2:
            s.arrow(614, y + 50, 614, y + 64, width=1.8)
    s.box(24, 244, 714, 62, "amber", r=8)
    s.text(36, 264, "Consulta «GDPR compliance and audit logging» (real):", 11, C["amber"][2], bold=True)
    s.text(36, 282, "1. BUD-2024-009::CONSENT-004 (hijo) 0,418   ·   2. BUD-2024-012::parent 0,307 ← un padre entero en el top-3",
           10.5, C["amber"][2])
    s.text(36, 298, "Para una consulta abstracta, a veces el presupuesto completo es mejor respuesta que un componente.", 10.5,
           C["amber"][2])
    s.footer("En nuestro corpus: 77 chunks = 17 padres + 60 hijos · 2 obesos (el padre de BUD-2024-016: 1472 tokens) · 0 $")
    s.save("s07-est-hierarchical")


if __name__ == "__main__":
    for fn in (fixed, recursive, sentence_window, structural, semantic, propositional, contextual, hierarchical):
        fn()
