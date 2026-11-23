"""Genera S02-comandos-y-salidas.pdf: la guía de comandos de la Sesión 2 para los alumnos.

Cada comando de la sesión con para qué sirve, cómo se lanza (bash y PowerShell), la salida real, cómo leerla y el
test que comprueba ese comportamiento. Las salidas son las de la ejecución en local del 23/11/2026 sobre la rama
session_2_live con gpt-4o-mini (carpeta salidas/: la respuesta completa en .json y un resumen en .txt). No hace
falta repetir ninguna petición: todo lo que se cita sale de esos ficheros.

    python build_comandos.py
"""

import html
import json
import pathlib
import subprocess

AQUI = pathlib.Path(__file__).parent
SAL = AQUI / "salidas"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def leer(nombre: str) -> str:
    return (SAL / nombre).read_text(encoding="utf-8-sig").strip("\n").rstrip()


def resp(nombre: str) -> dict:
    return json.loads((SAL / f"{nombre}.json").read_text(encoding="utf-8"))


def corta(texto: str, lineas: int) -> str:
    ls = texto.splitlines()
    return "\n".join(ls[:lineas]) + ("\n…" if len(ls) > lineas else "")


def jq(nombre: str, campos: list[str], est_lineas: int = 0) -> str:
    """Reproduce la proyección que hace el jq del comando a partir de la respuesta guardada."""
    b = resp(nombre)
    v, u = b.get("validation") or {}, b.get("usage") or {}
    out: dict = {}
    for c in campos:
        if c == "score":
            out[c] = v.get("score")
        elif c == "issues":
            out[c] = v.get("issues")
        elif c in ("input_tokens", "output_tokens"):
            out[c] = u.get(c)
        elif c == "tokens":
            out[c] = u.get("total_tokens")
        elif c == "prep_tokens":
            out[c] = u.get("preprocessing_input_tokens", 0) + u.get("preprocessing_output_tokens", 0)
        elif c == "estimation":
            out[c] = "<<EST>>"
        elif c == "extracted_requirements":
            out[c] = "<<REQ>>"
        else:
            out[c] = b.get(c)
    s = json.dumps(out, indent=2, ensure_ascii=False)
    if "<<EST>>" in s:
        s = s.replace('"<<EST>>"', "(" + str(len(b["estimation"])) + " caracteres; primeras líneas abajo)")
        s += "\n\n── estimation ──\n" + corta(b["estimation"], est_lineas or 10)
    if "<<REQ>>" in s:
        s = s.replace('"<<REQ>>"', "(" + str(len(b["extracted_requirements"])) + " caracteres; extracto abajo)")
        s += "\n\n── extracted_requirements ──\n" + corta(b["extracted_requirements"], 14)
    return s


def ps_body(campos: str, select: str) -> str:
    """Equivalente en PowerShell 5.1 (sin jq): el body se envía en UTF-8 para no romper las tildes."""
    return (f"$body = @{{transcription=$TRANS{campos}}} | ConvertTo-Json\n"
            "$r = Invoke-RestMethod -Method Post -Uri $BASE/api/v1/estimate `\n"
            "  -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))\n"
            f"{select}")


ITEMS = []  # ("h2", texto) | ("intro", html) | ("paso", dict)


def h2(t):
    ITEMS.append(("h2", t))


def intro(t):
    ITEMS.append(("intro", t))


def paso(titulo, para, cmd, salida=None, leer_=None, diapo="", alt=None, test=None, alt_lab="En PowerShell"):
    ITEMS.append(("paso", dict(titulo=titulo, para=para, cmd=cmd.strip(), salida=salida, leer=leer_,
                               diapo=diapo, alt=alt, alt_lab=alt_lab, test=test)))


# ── 0 · Preparar el entorno ─────────────────────────────────────────────────
h2("0 · Preparar el entorno")
intro("Todos los comandos se lanzan desde la carpeta <code>estimator/</code> del repositorio, en la rama "
      "<code>session_2_live</code>. El servicio corre en Docker con <code>uvicorn --reload</code> y la carpeta "
      "<code>app/</code> montada: un cambio en el código se aplica al guardar. Los comandos van en "
      "<code>bash</code> con <code>curl</code> y <code>jq</code> (macOS, Linux o Git Bash); debajo de cada uno está "
      "el equivalente en <b>PowerShell</b>, que no necesita <code>jq</code>. <b>Cada petición a "
      "<code>/api/v1/estimate</code> llama al modelo y consume tokens</b>; los tests, en cambio, no llaman a ningún "
      "modelo y se pueden repetir sin coste.")
paso("Levantar el servicio",
     "Construye la imagen y arranca el contenedor <code>estimator</code>. Antes hay que crear <code>.env</code> a "
     "partir de <code>.env.example</code> con la clave del proveedor (<code>OPENAI_API_KEY</code> si "
     "<code>LLM_PROVIDER=openai</code>).",
     "cp .env.example .env        # y rellenar OPENAI_API_KEY\ndocker compose up -d --build\ndocker compose ps",
     leer("01_ps.txt"),
     "<b>healthy</b> significa que el healthcheck de Docker ya ha llamado a <code>/health</code> con éxito. "
     "El nombre del contenedor puede variar en cada equipo.",
     diapo="4", alt="Copy-Item .env.example .env\ndocker compose up -d --build\ndocker compose ps")
paso("GET /health",
     "Comprueba que la API responde. Es lo mismo que consulta el healthcheck cada 30 segundos.",
     "curl -s localhost:8000/health | jq",
     leer("02_health.txt"),
     "Si no responde justo después de editar código, es la recarga de <code>uvicorn</code>: repite a los pocos "
     "segundos.",
     diapo="4", alt="Invoke-RestMethod http://localhost:8000/health",
     test="uv run pytest tests/test_health.py -v")
paso("Variables para el resto de la sesión",
     "Guarda la URL base y las dos transcripciones de ejemplo como texto JSON. <code>long_transcription.txt</code> "
     "es una reunión real de unas 5.000 palabras; <code>short_transcription.txt</code>, un brief limpio.",
     """export BASE=http://localhost:8000
export TRANS=$(jq -Rs . < app/fixtures/long_transcription.txt)
export SHORT=$(jq -Rs . < app/fixtures/short_transcription.txt)""",
     None,
     "En PowerShell se lee con <code>[IO.File]::ReadAllText</code> y no con <code>Get-Content -Raw</code>: en "
     "Windows PowerShell 5.1, <code>Get-Content</code> añade propiedades ocultas al texto y "
     "<code>ConvertTo-Json</code> las enviaría dentro del body (la API respondería 422, «Input should be a valid "
     "string»).",
     alt="""$BASE  = "http://localhost:8000"
$TRANS = [IO.File]::ReadAllText("$PWD\\app\\fixtures\\long_transcription.txt")
$SHORT = [IO.File]::ReadAllText("$PWD\\app\\fixtures\\short_transcription.txt")""")
paso("Sanity check: una estimación corta",
     "Primera llamada real al modelo con la transcripción corta. Si responde 200 con <code>score ≥ 0.5</code>, el "
     "sistema está listo.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$SHORT}" | jq '{model, score: .validation.score, latency_ms}'""",
     jq("04_sanity_short", ["model", "score", "latency_ms"]),
     "<code>model</code> trae la versión exacta que respondió (<code>gpt-4o-mini-2024-07-18</code>). La latencia "
     "va en milisegundos e incluye todo el trabajo del servidor.",
     diapo="4", alt=ps_body("", "$r | Select-Object model, latency_ms, @{n='score';e={$_.validation.score}}")
                       .replace("$TRANS", "$SHORT"))

# ── 1 · Los tests ───────────────────────────────────────────────────────────
h2("1 · Los tests: comprobar el sistema sin gastar tokens")
intro("El proyecto trae <b>21 tests</b> en <code>estimator/tests/</code>. Ninguno llama a OpenAI: en "
      "<code>test_estimate_endpoint.py</code> la función <code>_call_openai</code> se sustituye por un falso "
      "(<code>monkeypatch</code>) que devuelve una estimación fija y apunta cada llamada. Así se comprueba el camino "
      "completo de la petición —validación, preprocesado, prompt, evaluación— en milisegundos y gratis. Se ejecutan "
      "en el ordenador con <code>uv</code> (la imagen de Docker no incluye las dependencias de desarrollo). En cada "
      "paso de esta guía, el recuadro <b>Lo comprueba</b> indica el test relacionado.")
paso("uv run pytest -v",
     "Instala las dependencias de desarrollo la primera vez (<code>uv sync</code>) y ejecuta todos los tests con el "
     "nombre de cada uno.",
     "uv sync\nuv run pytest -v",
     corta(leer("03_pytest.txt").split("collecting ...", 1)[-1].strip(), 30),
     "<ul><li><code>test_estimate_endpoint.py</code> (6): el endpoint de punta a punta con el falso de OpenAI.</li>"
     "<li><code>test_evaluation.py</code> (6): el evaluador estructural con presupuestos conocidos.</li>"
     "<li><code>test_examples_format.py</code> (8): los tres formatos de ejemplos y la selección de cuántos.</li>"
     "<li><code>test_health.py</code> (1): la app importa y arranca.</li></ul>"
     "Para lanzar uno solo: <code>uv run pytest tests/fichero.py::nombre_del_test -v</code>.",
     diapo="19", alt="uv sync\nuv run pytest -v")

# ── 2 · La transcripción real ───────────────────────────────────────────────
h2("2 · La transcripción real: limpiar el input")
paso("Estimación sin preprocesado (preprocessing = none)",
     "La transcripción larga tal cual, con tres ejemplos en el prompt. Es la referencia con la que se compara todo "
     "lo demás.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"preprocessing\\":\\"none\\"}" \\
  | jq '{model, finish_reason, latency_ms, score: .validation.score, issues: .validation.issues, usage, estimation}'""",
     jq("05_none", ["model", "finish_reason", "latency_ms", "score", "issues", "usage", "estimation"], 16),
     "<ul><li><b>score 0.625</b>: 5 de 8 comprobaciones.</li>"
     "<li>El issue dice que falta la tabla, pero la tabla está: el modelo añadió una columna "
     "<code>Description</code> y el evaluador busca exactamente <code>| Task | Hours | Cost</code>. Sin esa "
     "cabecera tampoco puede sumar filas.</li>"
     "<li><code>input_tokens</code> 8.493: la transcripción más el system prompt con tres ejemplos.</li></ul>",
     diapo="7", alt=ps_body(';preprocessing="none"',
                            "$r | Select-Object model, finish_reason, latency_ms, @{n='score';e={$_.validation.score}}"
                            "\n$r.validation.issues; $r.usage"),
     test="uv run pytest tests/test_evaluation.py::test_missing_table_is_detected -v")
paso("Estrategia A: inline_cleaning",
     "Una sola llamada. Añade al system prompt el bloque <code>INLINE_CLEANING_BLOCK</code> "
     "(<code>app/services/llm_service.py</code>): ignorar la charla, sacar los requisitos implícitos y quedarse con "
     "lo último que se dijo cuando hay contradicciones.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"preprocessing\\":\\"inline_cleaning\\"}" \\
  | jq '{score: .validation.score, issues: .validation.issues, latency_ms, usage}'""",
     jq("06_inline_cleaning", ["score", "issues", "latency_ms", "usage"]),
     "Con <b>65 tokens</b> más de entrada (8.558 frente a 8.493) el score sube a <b>0.75</b>: ahora la tabla tiene "
     "la cabecera esperada. Lo que falla es la suma: las filas dan 274 h y el total declarado es 324 h.",
     diapo="8", alt=ps_body(';preprocessing="inline_cleaning"',
                            "$r | Select-Object latency_ms, @{n='score';e={$_.validation.score}}"
                            "\n$r.validation.issues; $r.usage"))
paso("Estrategia B: two_phase",
     "Dos llamadas. La primera (<code>extract_requirements</code>) convierte la transcripción en una lista limpia "
     "de requisitos; la segunda estima a partir de esa lista.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"preprocessing\\":\\"two_phase\\"}" \\
  | jq '{extracted_requirements, score: .validation.score, latency_ms, tokens: .usage.total_tokens,
         prep_tokens: (.usage.preprocessing_input_tokens + .usage.preprocessing_output_tokens)}'""",
     jq("07_two_phase", ["extracted_requirements", "score", "latency_ms", "tokens", "prep_tokens"]),
     "<ul><li>La estimación recibe solo <b>1.758 tokens</b> (los requisitos), pero la fase 1 leyó la transcripción "
     "entera: <b>7.585 tokens</b> de preprocesado.</li>"
     "<li>La lista ya es útil por sí sola: resuelve la contradicción SAP → BCN-Touch y saca requisitos enterrados "
     "(depósitos configurables, GDPR, WCAG AA).</li>"
     "<li>Latencia: 21,9 s, la más alta de las tres, porque son dos llamadas seguidas.</li></ul>",
     diapo="8-9", alt=ps_body(';preprocessing="two_phase"',
                              "$r.extracted_requirements\n$r | Select-Object latency_ms, "
                              "@{n='score';e={$_.validation.score}}; $r.usage"),
     test="uv run pytest tests/test_estimate_endpoint.py::test_two_phase_invokes_llm_twice_and_fills_extracted -v")
paso("Prueba tú: el contrato rechaza lo que no cumple",
     "<code>EstimationRequest</code> (<code>app/schemas/estimation.py</code>) valida el body antes de llamar al "
     "modelo. Estas tres peticiones no cuestan nada: FastAPI responde <b>422</b> sin ejecutar el endpoint.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d '{"transcription":"Quiero una web."}' | jq
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d '{"transcription":"We need a small CRM with auth, contacts and roles. MVP six weeks.","num_examples":9}' | jq
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d '{"transcription":"We need a small CRM with auth, contacts and roles. MVP six weeks.","preprocessing":"magic"}' | jq""",
     "\n\n".join(leer(f).replace("HTTP 422\n", "") for f in
                 ("24_422_corta.txt", "25_422_num_examples.txt", "26_422_preprocessing.txt")),
     "Cada error dice <b>qué campo</b> (<code>loc</code>), <b>qué regla</b> (<code>type</code>) y <b>qué se "
     "recibió</b> (<code>input</code>): menos de 50 caracteres, <code>num_examples</code> por encima de 5 y un modo "
     "de preprocesado que no existe. Ninguna línea del endpoint se ha escrito para esto: lo hace Pydantic.",
     diapo="6")

# ── 3 · Iterar el contexto ──────────────────────────────────────────────────
h2("3 · Iterar el contexto de referencia")
paso("3.1 · Sin contexto y con contexto",
     "La misma transcripción y el mismo modelo, quitando y poniendo el bloque de ejemplos (<code>use_examples</code>).",
     """# Sin CAG
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"use_examples\\": false}" | jq '{score: .validation.score, issues: .validation.issues, usage}'
# Con CAG
curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"use_examples\\": true}" | jq '{score: .validation.score, issues: .validation.issues, usage}'""",
     "── use_examples = false ──\n" + jq("08_sin_ejemplos", ["score", "issues", "usage"]) +
     "\n\n── use_examples = true ──\n" + jq("09_con_ejemplos", ["score", "issues", "usage"]),
     "<ul><li>Sin ejemplos, <b>0.375</b>: ni título, ni tabla, ni totales. El modelo describe cada tarea en un "
     "bloque de viñetas a su manera.</li>"
     "<li>Con ejemplos, <b>0.75</b>: aparece la estructura de la casa. Los ejemplos ocupan "
     "<b>1.265 tokens</b> (8.493 − 7.228).</li>"
     "<li>Lo único que cambia es el contexto inyectado: eso es CAG.</li></ul>",
     diapo="10", alt=ps_body(';use_examples=$false', "$r.validation | Select-Object score, issues; $r.usage"),
     test="uv run pytest tests/test_estimate_endpoint.py::test_use_examples_false_omits_examples_block -v")
paso("3.2 · El formato de los ejemplos",
     "Los mismos tres ejemplos escritos en Markdown, en JSON o en prosa (<code>example_format</code>). Los tres "
     "formatos salen de la misma fuente, <code>CANONICAL_EXAMPLES</code> en <code>app/context/examples.py</code>.",
     """for FMT in markdown json narrative; do
  curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
    -d "{\\"transcription\\":$TRANS,\\"example_format\\":\\"$FMT\\"}" \\
    | jq "{format:\\"$FMT\\", input_tokens: .usage.input_tokens, latency_ms, score: .validation.score}"
done""",
     "\n".join(json.dumps({"format": f, **json.loads(leer(f"{n}.txt"))}, ensure_ascii=False)
               .replace('"http": 200, ', "")
               for f, n in (("markdown", "10_formato_markdown"), ("json", "11_formato_json"),
                            ("narrative", "12_formato_narrative")))
     + "\n\n── estimation con example_format=json (primeras líneas) ──\n"
     + corta(resp("11_formato_json")["estimation"], 8),
     "<ul><li><b>El modelo imita el formato del contexto</b>: con ejemplos en JSON, responde con un bloque "
     "<code>```json</code>. El evaluador busca Markdown y el score cae a <b>0.25</b>.</li>"
     "<li>Con prosa (<code>narrative</code>) escribe títulos pero ni tabla ni totales: <b>0.5</b>.</li>"
     "<li>JSON es el formato más caro en tokens (9.081) por las comillas y las claves repetidas.</li></ul>",
     diapo="11",
     alt="""foreach ($FMT in "markdown","json","narrative") {
  $body = @{transcription=$TRANS; example_format=$FMT} | ConvertTo-Json
  $r = Invoke-RestMethod -Method Post -Uri $BASE/api/v1/estimate `
    -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
  [pscustomobject]@{format=$FMT; input_tokens=$r.usage.input_tokens; latency_ms=$r.latency_ms; score=$r.validation.score}
}""",
     test="uv run pytest tests/test_examples_format.py -v")
paso("3.3 · Cuántos ejemplos",
     "De 0 a 5 ejemplos en el prompt (<code>num_examples</code>, validado entre 0 y 5).",
     """for N in 0 1 3 5; do
  curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
    -d "{\\"transcription\\":$TRANS,\\"num_examples\\":$N}" \\
    | jq "{n:$N, input_tokens: .usage.input_tokens, output_tokens: .usage.output_tokens, latency_ms, score: .validation.score}"
done""",
     "\n".join(json.dumps({"n": n, **{k: v for k, v in json.loads(leer(f"{f}.txt")).items() if k != "http"}},
                          ensure_ascii=False)
               for n, f in ((0, "13_n0"), (1, "14_n1"), (3, "15_n3"), (5, "16_n5"))),
     "<ul><li>Los tokens de entrada suben en línea recta: unos <b>430 por ejemplo</b>, en cada llamada.</li>"
     "<li>El score salta de 0.5 a 0.625 con el primer ejemplo y luego no se mueve.</li>"
     "<li>Es una sola ejecución por valor: la latencia varía de una llamada a otra y no permite conclusiones. Para "
     "comparar en serio habría que repetir cada fila varias veces.</li></ul>",
     diapo="12",
     alt="""foreach ($N in 0,1,3,5) {
  $body = @{transcription=$TRANS; num_examples=$N} | ConvertTo-Json
  $r = Invoke-RestMethod -Method Post -Uri $BASE/api/v1/estimate `
    -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
  [pscustomobject]@{n=$N; input=$r.usage.input_tokens; output=$r.usage.output_tokens; latency_ms=$r.latency_ms; score=$r.validation.score}
}""",
     test="uv run pytest tests/test_examples_format.py::test_canonical_examples_have_calibrated_totals -v")
paso("3.4 · El prompt de salida: de BASIC a STRUCTURED",
     "En <code>app/services/llm_service.py</code> conviven dos prompts de salida y una línea elige cuál se usa. Se "
     "lanza la petición, se cambia esa línea, se guarda y se repite la misma petición.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS}" | jq '{score: .validation.score, issues: .validation.issues}'

# En app/services/llm_service.py:
#   ACTIVE_OUTPUT_PROMPT = PROMPT_OUTPUT_STRUCTURED   # antes: PROMPT_OUTPUT_BASIC

curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS}" | jq '{score: .validation.score, issues: .validation.issues}'""",
     "── PROMPT_OUTPUT_BASIC ──\n" + jq("17_prompt_basic", ["score", "issues"]) +
     "\n\n── PROMPT_OUTPUT_STRUCTURED ──\n" + jq("18_prompt_structured", ["score", "issues"]) +
     "\n\n── docker compose logs estimator (al guardar el cambio) ──\n" +
     "\n".join(ln.split("|", 1)[-1].strip() for ln in leer("30_logs_reload.txt").splitlines()[:9]),
     "<ul><li>Con BASIC falta la sección de totales: el modelo no sabe qué forma se espera.</li>"
     "<li>Con STRUCTURED aparecen todas las secciones, incluida la de riesgos, y la respuesta es más corta (568 "
     "tokens frente a 795). Sube a <b>0.75</b>.</li>"
     "<li>Lo que queda en rojo son las <b>sumas</b>: 292 h en las filas frente a 320 h declaradas. El modelo "
     "escribe el total, no lo calcula. Ocurrió en todas las ejecuciones de la sesión, también con "
     "<code>gpt-4o</code>.</li>"
     "<li>Los logs muestran la recarga: <code>WatchFiles detected changes … Reloading</code>. No hace falta "
     "reconstruir la imagen.</li></ul>",
     diapo="13-14", alt=ps_body("", "$r.validation | Select-Object score, issues"),
     test="uv run pytest tests/test_evaluation.py::test_mismatched_total_hours_is_flagged -v")

# ── 4 · Parámetros del modelo ───────────────────────────────────────────────
h2("4 · Parámetros del modelo")
paso("4.1 · Modelo económico y modelo premium",
     "El campo <code>model</code> del body sustituye al <code>LLM_MODEL</code> de <code>.env</code> solo para esa "
     "petición, sin reiniciar nada.",
     """for M in gpt-4o-mini gpt-4o; do
  curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
    -d "{\\"transcription\\":$TRANS,\\"model\\":\\"$M\\"}" | jq '{model, score: .validation.score, latency_ms, usage}'
done""",
     jq("19_gpt4o_mini", ["model", "score", "latency_ms", "usage"]) + "\n" +
     jq("20_gpt4o", ["model", "score", "latency_ms", "usage"]),
     "<ul><li>Mismo score (0.75) con los dos.</li>"
     "<li>Coste con los precios de referencia de la sesión (por millón de tokens: <code>gpt-4o-mini</code> 0,15 $ "
     "entrada y 0,60 $ salida; <code>gpt-4o</code> 2,50 $ y 10 $): unos <b>0,0017 $</b> frente a <b>0,0293 $</b> "
     "por estimación, <b>unas 17 veces más</b>.</li>"
     "<li>Cambiar de <b>proveedor</b> (<code>LLM_PROVIDER=anthropic</code>) sí requiere editar <code>.env</code> y "
     "recrear el contenedor: <code>docker compose up -d --force-recreate estimator</code>. "
     "<code>get_settings()</code> está en caché (<code>@lru_cache</code>) y <code>--reload</code> no lo relee.</li>"
     "<li>Las variantes con <code>claude-haiku-4-5</code> y <code>claude-sonnet-4-6</code> necesitan "
     "<code>ANTHROPIC_API_KEY</code>; no se ejecutaron para esta guía.</li></ul>",
     diapo="15",
     alt="""foreach ($M in "gpt-4o-mini","gpt-4o") {
  $body = @{transcription=$TRANS; model=$M} | ConvertTo-Json
  $r = Invoke-RestMethod -Method Post -Uri $BASE/api/v1/estimate `
    -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
  $r | Select-Object model, latency_ms, @{n='score';e={$_.validation.score}}; $r.usage
}""",
     test="uv run pytest tests/test_estimate_endpoint.py::test_model_override_is_passed_to_provider -v")
paso("4.2 · max_tokens y finish_reason",
     "Limita la salida a 200 tokens para ver qué ocurre cuando la respuesta no cabe.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"max_tokens\\": 200}" \\
  | jq '{finish_reason, score: .validation.score, issues: .validation.issues}'""",
     jq("21_max_tokens_200", ["finish_reason", "score", "issues"]),
     "<code>finish_reason: \"length\"</code> significa que el modelo se quedó sin presupuesto de salida: la tabla "
     "se cortó tras la primera fila. El evaluador lo marca de forma explícita. <b>Hay que fijar siempre "
     "<code>max_tokens</code> y comprobar <code>finish_reason</code></b> antes de dar una respuesta por buena.",
     diapo="16", alt=ps_body(";max_tokens=200", "$r | Select-Object finish_reason, @{n='score';e={$_.validation.score}}"
                                                "\n$r.validation.issues"),
     test="uv run pytest tests/test_estimate_endpoint.py::test_max_tokens_low_propagates_finish_reason_length -v")
paso("4.2 · thinking_budget con OpenAI",
     "<code>thinking_budget</code> activa el razonamiento extendido, que solo existe en el camino de Anthropic. Con "
     "<code>LLM_PROVIDER=openai</code> el servicio lo ignora y lo deja anotado en los logs.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$SHORT,\\"thinking_budget\\": 2000,\\"max_tokens\\": 6000}" \\
  | jq '{model, finish_reason, score: .validation.score}'
docker compose logs estimator | grep thinking_budget""",
     jq("22_thinking_openai", ["model", "finish_reason", "score"]) + "\n\n" + leer("23_log_thinking.txt"),
     "La petición funciona igual y el aviso <code>thinking_budget_ignored_for_provider</code> deja constancia. Con "
     "Anthropic, los tokens de razonamiento se facturan como salida: compensa en estimaciones complejas, donde "
     "importa que las cifras cuadren, no en las simples.",
     diapo="16",
     alt=ps_body(";thinking_budget=2000;max_tokens=6000", "$r | Select-Object model, finish_reason")
         .replace("$TRANS", "$SHORT") + "\ndocker compose logs estimator | Select-String thinking_budget")

# ── 5 · Evaluación ──────────────────────────────────────────────────────────
h2("5 · Evaluar la calidad")
paso("5.1 · El objeto validation completo",
     "<code>evaluate_estimation_structure</code> (<code>app/services/evaluation.py</code>) pasa ocho comprobaciones "
     "con expresiones regulares, sin llamar a ningún modelo. Este es el resultado completo de la estimación "
     "two-phase.",
     """curl -s $BASE/api/v1/estimate -H 'Content-Type: application/json' \\
  -d "{\\"transcription\\":$TRANS,\\"preprocessing\\":\\"two_phase\\"}" | jq '.validation'""",
     json.dumps(resp("07_two_phase")["validation"], indent=2, ensure_ascii=False),
     "<ul><li>Cinco booleanos de estructura: título, tabla, totales, equipo y duración.</li>"
     "<li><code>declared_total_*</code> frente a <code>sum_row_*</code>: lo declarado y lo que suman las filas. "
     "Tolerancia de ±1 h y ±2 % del coste.</li>"
     "<li><code>score = superadas / 8</code>. Aquí, 6 de 8 = 0.75.</li>"
     "<li><code>issues</code> explica en texto cada comprobación que falla.</li></ul>",
     diapo="17", alt=ps_body(';preprocessing="two_phase"', "$r.validation"),
     test="uv run pytest tests/test_evaluation.py -v")
paso("5.2 · Prueba tú: añadir la comprobación de riesgos",
     "Añadir un noveno check, <code>has_risks_section</code>. En <code>app/services/evaluation.py</code>, dentro de "
     "<code>evaluate_estimation_structure</code>: calcular el booleano, añadirlo a <code>checks</code> y añadir su "
     "<code>issues.append(...)</code>. En <code>app/schemas/estimation.py</code>, añadir el campo a "
     "<code>StructureCheck</code>. El router no se toca.",
     """has_risks_section = bool(
    re.search(r"##\\s+(Risks?|Risks?\\s+and\\s+assumptions)", text, re.IGNORECASE)
)
# … en checks:  has_risks_section,
# … en issues:  if not has_risks_section: issues.append("Missing risks and assumptions section")
# … en StructureCheck(...):  has_risks_section=has_risks_section

# tests/test_risks_section.py: dos tests nuevos
#   - un ejemplo canónico + "## Risks and assumptions"  → has_risks_section=True y score 1.0
#   - el ejemplo canónico tal cual                       → False y el issue "Missing risks and assumptions section"

uv run pytest tests/test_evaluation.py tests/test_risks_section.py -v""",
     "── salida de pytest tras el cambio ──\n" + leer("27_pytest_risks.txt") +
     "\n\n── detalle del fallo ──\n" + "\n".join(ln for ln in leer("29_pytest_risks_fallo.txt").splitlines()
                                              if ln.startswith(("E ", ">", "FAILED"))) +
     "\n\n── las salidas de 3.4, reevaluadas con el check nuevo ──\n" + leer("28_risks_reevaluado.txt"),
     "<ul><li>Los dos tests nuevos pasan, pero <b>fallan dos que ya existían</b>: un presupuesto canónico ya no saca "
     "1.0 sino <b>0.889</b> (8 de 9).</li>"
     "<li>El motivo: <b>ninguno de los cinco ejemplos canónicos tiene sección de riesgos</b>. Y como el modelo imita "
     "los ejemplos (3.2), con el prompt BASIC tampoco la escribe: 0.556. Con STRUCTURED, que la pide, 0.778.</li>"
     "<li>Para cerrar el cambio hay que decidir: añadir riesgos a los ejemplos o pedirlos siempre en el prompt, y "
     "actualizar los tests. Un check nuevo cambia lo que significa «bien formado».</li></ul>",
     diapo="18")

# ── 6 · Docker ──────────────────────────────────────────────────────────────
h2("6 · Comandos de Docker útiles durante la sesión")
paso("Logs, recrear y apagar",
     "Los tres comandos que se usan alrededor de las demos.",
     """docker compose logs -f estimator                      # ver cada petición y cada aviso en directo
docker compose up -d --force-recreate estimator       # tras cambiar .env
docker compose down                                   # apagar al terminar""",
     None,
     "<code>restart</code> no basta tras editar <code>.env</code>: Compose lee el fichero al <b>crear</b> el "
     "contenedor, no al reiniciarlo.",
     diapo="4")


# ── HTML ────────────────────────────────────────────────────────────────────
CSS = """
@page { size: A4; margin: 14mm 13mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color: #1d2330; font-size: 10pt; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 2mm; color: #2f2a8a; }
.sub { color: #4a5568; margin-bottom: 4mm; font-size: 9.5pt; line-height: 1.45; }
h2 { font-size: 13pt; color: #fff; background: #3f3fb0; padding: 2mm 3mm; margin: 6mm 0 3mm; border-radius: 1.5mm;
     break-after: avoid; }
.intro { font-size: 9.3pt; line-height: 1.45; margin: 0 0 3mm; background: #eef0ff; border-radius: 1.5mm;
         padding: 2.2mm 3mm; }
.paso { border: 0.3mm solid #cfd3ea; border-radius: 1.5mm; margin: 0 0 3.5mm; padding: 2.5mm 3mm; }
.cab { display: flex; justify-content: space-between; align-items: baseline; gap: 3mm; break-after: avoid; }
.tit { font-weight: 700; font-size: 10.8pt; color: #2f2a8a; }
.diapo { font-size: 8pt; color: #6b7280; white-space: nowrap; }
.para { font-size: 9.3pt; line-height: 1.42; margin: 1.2mm 0 0; }
.lab { font-size: 7.5pt; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; margin: 1.8mm 0 0.6mm;
       break-after: avoid; }
pre { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 7.4pt; line-height: 1.3; margin: 0;
      padding: 1.8mm 2.2mm; border-radius: 1mm; white-space: pre-wrap; word-break: break-word; }
pre.cmd { background: #1c1f2e; color: #f3f6fb; break-inside: avoid; }
pre.alt { background: #2b2f45; color: #dfe3f5; break-inside: avoid; }
pre.out { background: #f4f5f9; color: #1d2330; border: 0.25mm solid #e1e3ee; }
.leer { margin-top: 1.6mm; font-size: 9.1pt; line-height: 1.42; background: #f1fbf5; border-left: 1mm solid #2f9e6a;
        padding: 1.5mm 2.5mm; break-inside: avoid; }
.leer b.l { color: #1f7a50; }
.leer ul { margin: 0.5mm 0 0 4mm; padding: 0; }
.test { margin-top: 1.4mm; font-size: 8.6pt; background: #ecfdf5; border: 0.25mm solid #a7e3c4; border-radius: 1mm;
        padding: 1.2mm 2.5mm; break-inside: avoid; }
.test b { color: #13704a; }
code { font-family: Consolas, monospace; font-size: 0.92em; background: #eef0f7; padding: 0 0.6mm; border-radius: 0.6mm; }
"""


def render() -> str:
    out = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>S02 · comandos y salidas</title>"
           f"<style>{CSS}</style></head><body>",
           "<h1>Sesión 2 · Los comandos de la sesión y su salida</h1>",
           "<div class='sub'>Primeros pasos de arquitectura CAG · Máster en AI Engineering (LIDR). Cada comando que se "
           "usa en el directo, en orden: <b>para qué sirve</b>, <b>cómo se lanza</b>, la <b>salida real</b> "
           "(ejecutada en local el 23/11/2026 sobre la rama <code>session_2_live</code>, con "
           "<code>gpt-4o-mini</code>), <b>cómo leerla</b> y el <b>test</b> que comprueba ese comportamiento sin "
           "llamar al modelo. Las respuestas de un LLM varían de una ejecución a otra: los números exactos cambiarán, "
           "la tendencia no. La referencia «diapo N» indica dónde aparece en las diapositivas.</div>"]
    for kind, val in ITEMS:
        if kind == "h2":
            out.append(f"<h2>{html.escape(val)}</h2>")
        elif kind == "intro":
            out.append(f"<div class='intro'>{val}</div>")
        else:
            v = val
            diapo = f"<span class='diapo'>diapo {v['diapo']}</span>" if v["diapo"] else ""
            out.append(f"<div class='paso'><div class='cab'><div class='tit'>{html.escape(v['titulo'])}</div>"
                       f"{diapo}</div><div class='para'><b>Para qué sirve.</b> {v['para']}</div>")
            out.append(f"<div class='lab'>Comando</div><pre class='cmd'>{html.escape(v['cmd'])}</pre>")
            if v["alt"]:
                out.append(f"<div class='lab'>{html.escape(v['alt_lab'])}</div>"
                           f"<pre class='alt'>{html.escape(v['alt'])}</pre>")
            if v["salida"]:
                out.append(f"<div class='lab'>Salida</div><pre class='out'>{html.escape(v['salida'])}</pre>")
            if v["leer"]:
                out.append(f"<div class='leer'><b class='l'>Cómo leerla.</b> {v['leer']}</div>")
            if v["test"]:
                out.append(f"<div class='test'><b>Lo comprueba:</b> <code>{html.escape(v['test'])}</code></div>")
            out.append("</div>")
    out.append("</body></html>")
    return "".join(out)


if __name__ == "__main__":
    h = AQUI / "comandos-y-salidas-s02.html"
    h.write_text(render(), encoding="utf-8")
    pdf = AQUI.parent / "S02-comandos-y-salidas.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True)
    print("ok", pdf, pdf.stat().st_size)
