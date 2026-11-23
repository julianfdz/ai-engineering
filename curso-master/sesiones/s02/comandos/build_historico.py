"""Genera historico-s02.html: las respuestas reales de la Sesión 2 guardadas en salidas/*.json, para enseñarlas
en clase sin volver a llamar al modelo. Una fila por petición (parámetros, tokens, latencia, score e issues) y,
al desplegarla, la estimación completa y la validación. Se abre con cualquier navegador.

    python build_historico.py
"""

import html
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
SAL = AQUI / "salidas"

DEMOS = [  # (fichero, bloque, qué cambia)
    ("04_sanity_short", "Setup", "transcripción corta · valores por defecto"),
    ("05_none", "2.1-2.2", "preprocessing = none"),
    ("06_inline_cleaning", "2.3", "preprocessing = inline_cleaning"),
    ("07_two_phase", "2.4", "preprocessing = two_phase"),
    ("08_sin_ejemplos", "3.1", "use_examples = false"),
    ("09_con_ejemplos", "3.1", "use_examples = true"),
    ("10_formato_markdown", "3.2", "example_format = markdown"),
    ("11_formato_json", "3.2", "example_format = json"),
    ("12_formato_narrative", "3.2", "example_format = narrative"),
    ("13_n0", "3.3", "num_examples = 0"),
    ("14_n1", "3.3", "num_examples = 1"),
    ("15_n3", "3.3", "num_examples = 3"),
    ("16_n5", "3.3", "num_examples = 5"),
    ("17_prompt_basic", "3.4", "ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_BASIC"),
    ("18_prompt_structured", "3.4", "ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED"),
    ("19_gpt4o_mini", "4.1", "model = gpt-4o-mini"),
    ("20_gpt4o", "4.1", "model = gpt-4o"),
    ("21_max_tokens_200", "4.2", "max_tokens = 200"),
    ("22_thinking_openai", "4.2", "thinking_budget = 2000 con OpenAI (se ignora)"),
]

CSS = """
:root { --bg:#f6f7fb; --card:#fff; --ink:#1d2330; --muted:#6b7280; --line:#e2e5ef; --acc:#3f3fb0; --ok:#1f7a50;
        --ko:#a33a1e; --mid:#a06a00; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--ink); }
header { background: var(--acc); color: #fff; padding: 14px 22px; }
header h1 { margin: 0; font-size: 20px; } header p { margin: 4px 0 0; opacity: .85; font-size: 13px; }
main { padding: 16px 22px 40px; max-width: 1400px; margin: 0 auto; }
table.t { width: 100%; border-collapse: collapse; background: var(--card); font-size: 13px; }
table.t th { text-align: left; color: var(--muted); font-weight: 600; padding: 8px; border-bottom: 2px solid var(--line);
             position: sticky; top: 0; background: var(--card); }
table.t td { padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr.fila { cursor: pointer; } tr.fila:hover { background: #eef0ff; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.s { font-weight: 700; } .s.ok { color: var(--ok); } .s.mid { color: var(--mid); } .s.ko { color: var(--ko); }
.iss { color: var(--muted); font-size: 12px; } .tag { font-size: 11px; color: var(--muted); }
tr.det td { background: #fbfbfe; padding: 0 8px 14px; display: none; }
tr.det.on td { display: table-cell; }
.cols { display: grid; grid-template-columns: 2fr 1fr; gap: 14px; }
pre { white-space: pre-wrap; word-break: break-word; font-family: Consolas, monospace; font-size: 12px;
      background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 10px; margin: 6px 0 0; max-height: 520px;
      overflow: auto; }
h3 { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin: 10px 0 0; }
@media (max-width: 900px) { .cols { grid-template-columns: 1fr; } }
"""

JS = """
document.querySelectorAll('tr.fila').forEach(tr => tr.addEventListener('click', () =>
  tr.nextElementSibling.classList.toggle('on')));
"""


def clase(score: float | None) -> str:
    if score is None:
        return ""
    return "ok" if score >= 0.75 else "mid" if score >= 0.5 else "ko"


def main() -> None:
    filas = []
    for f, bloque, cambio in DEMOS:
        b = json.loads((SAL / f"{f}.json").read_text(encoding="utf-8"))
        v, u = b.get("validation") or {}, b.get("usage") or {}
        prep = u.get("preprocessing_input_tokens", 0) + u.get("preprocessing_output_tokens", 0)
        sc = v.get("score")
        issues = "<br>".join(html.escape(i) for i in v.get("issues", [])) or "—"
        filas.append(
            f"<tr class='fila'><td>{bloque}</td><td><b>{html.escape(cambio)}</b><div class='tag'>{f}</div></td>"
            f"<td>{html.escape(b.get('model', ''))}</td><td class='num'>{u.get('input_tokens', 0):,}</td>"
            f"<td class='num'>{u.get('output_tokens', 0):,}</td><td class='num'>{prep:,}</td>"
            f"<td class='num'>{b.get('latency_ms', 0) / 1000:.1f} s</td><td>{html.escape(b.get('finish_reason', ''))}</td>"
            f"<td class='num'><span class='s {clase(sc)}'>{sc}</span></td><td class='iss'>{issues}</td></tr>")
        req = (f"<h3>extracted_requirements (fase 1)</h3><pre>{html.escape(b['extracted_requirements'])}</pre>"
               if b.get("extracted_requirements") else "")
        filas.append(
            f"<tr class='det'><td colspan='10'><div class='cols'><div>{req}<h3>estimation</h3>"
            f"<pre>{html.escape(b.get('estimation', ''))}</pre></div><div><h3>validation</h3>"
            f"<pre>{html.escape(json.dumps(v, indent=2, ensure_ascii=False))}</pre><h3>usage</h3>"
            f"<pre>{html.escape(json.dumps(u, indent=2, ensure_ascii=False))}</pre></div></div></td></tr>")
    page = (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' "
        "content='width=device-width,initial-scale=1'><title>S02 · histórico de estimaciones</title>"
        f"<style>{CSS}</style></head><body><header><h1>Sesión 2 · Histórico de estimaciones</h1>"
        "<p>Respuestas reales de <code>POST /api/v1/estimate</code> con la transcripción de Acme Foods "
        "(23/11/2026, gpt-4o-mini salvo donde se indica). Pulsa una fila para ver la estimación completa.</p></header>"
        "<main><table class='t'><tr><th>Bloque</th><th>Qué cambia</th><th>Modelo</th><th class='num'>Tokens in</th>"
        "<th class='num'>Tokens out</th><th class='num'>Fase 1</th><th class='num'>Latencia</th><th>finish</th>"
        "<th class='num'>score</th><th>issues</th></tr>" + "".join(filas) +
        f"</table></main><script>{JS}</script></body></html>")
    out = AQUI.parent / "historico-s02.html"
    out.write_text(page, encoding="utf-8")
    print("ok", out)


if __name__ == "__main__":
    main()
