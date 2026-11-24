"""Genera S07-comandos-y-salidas.pdf: la guía de comandos de la Sesión 7 para los alumnos.

Mismo formato que la de la S2 (para qué sirve, comando en bash y PowerShell, salida real, cómo leerla y el test que
lo comprueba). Salidas de la ejecución en local del 24/11/2026 sobre la rama session_07_live (carpeta salidas/).
Las estrategias de pago (semantic, propositional, contextual_retrieval) no se relanzaron: sus números son los del
informe app/generation/rag/COMPARISON_REPORT.md y del histórico del Chunking Lab.

    python build_comandos.py
"""

import html
import importlib.util
import pathlib
import subprocess

AQUI = pathlib.Path(__file__).parent
SAL = AQUI / "salidas"
_spec = importlib.util.spec_from_file_location("s02c", AQUI.parent.parent / "s02" / "comandos" / "build_comandos.py")
s02c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s02c)   # solo para reutilizar el CSS y el motor de Edge
CSS, EDGE = s02c.CSS, s02c.EDGE


def leer(nombre: str) -> str:
    return (SAL / nombre).read_text(encoding="utf-8-sig").strip("\n").rstrip()


def sin_logs(texto: str) -> str:
    """Quita las líneas de log de structlog (fecha + [info]) y deja la salida que interesa."""
    return "\n".join(ln for ln in texto.splitlines() if "[info" not in ln).strip("\n")


ITEMS = []


def h2(t):
    ITEMS.append(("h2", t))


def intro(t):
    ITEMS.append(("intro", t))


def paso(titulo, para, cmd, salida=None, leer_=None, diapo="", alt=None, test=None):
    ITEMS.append(("paso", dict(titulo=titulo, para=para, cmd=cmd.strip(), salida=salida, leer=leer_, diapo=diapo,
                               alt=alt, test=test)))


EXEC = "docker compose exec estimator python"
TEST_LAB = ("docker compose exec estimator-web bin/rails test "
            "test/controllers/rag/chunking_comparisons_controller_test.rb")

# ── 0 ───────────────────────────────────────────────────────────────────────
h2("0 · Preparar el entorno")
intro("Todos los comandos se lanzan desde la <b>raíz del repositorio</b>, en la rama <code>session_07_live</code>. El "
      "código Python corre dentro del contenedor <code>estimator</code> con <code>docker compose exec</code>. Los "
      "comandos sirven igual en bash y en PowerShell. Si en PowerShell salen avisos de librerías por la salida de "
      "errores, se pueden ocultar añadiendo <code>2&gt;$null</code> al final. <b>Coste:</b> casi todo lo de esta "
      "guía pide embeddings a <code>text-embedding-3-small</code>, a 0,02 $ por millón de tokens: el corpus entero "
      "cuesta unos 0,0001 $. Las estrategias que llaman a un LLM se señalan aparte.")
paso("Levantar los servicios",
     "Arranca los cinco contenedores: el servicio de IA (<code>estimator</code>) con su Postgres y Redis, y la web de "
     "Rails con el suyo. Hace falta <code>OPENAI_API_KEY</code> en <code>estimator/.env</code>.",
     "docker compose up -d --build\ndocker compose ps", leer("01_ps.txt"),
     "Los cinco en <b>healthy</b>. Los nombres de los contenedores pueden variar en cada equipo.", diapo="2")
paso("GET /health", "Comprueba que la API responde.", "curl -s localhost:8000/health", leer("02_health.txt"),
     None, alt="Invoke-RestMethod http://localhost:8000/health")

# ── 1 ───────────────────────────────────────────────────────────────────────
h2("1 · Los tests del Chunking Lab")
intro("El Chunking Lab de la web tiene <b>23 tests</b> en <code>estimator-web/test/</code>. Ninguno llama al "
      "servicio de embeddings: el cliente HTTP se sustituye por un falso. Las estrategias de chunking en Python no "
      "tienen tests todavía; se validan con los números de los pasos siguientes.")
paso("bin/rails test",
     "Ejecuta los tests del catálogo de estrategias, del controlador, de la respuesta tipada, de la ejecución guardada "
     "y del cliente HTTP.",
     "docker compose exec estimator-web bin/rails test -v test/models/rag test/controllers/rag \\\n"
     "  test/services/estimator_ai/embeddings_client_test.rb",
     "\n".join(ln.split(" = ")[0] + "  ✓" if " = ." in ln else ln
               for ln in leer("12_rails_tests.txt").splitlines() if ln and not ln.startswith(("Run options", "# Running"))),
     "<ul><li><code>RagStrategyTest</code>: las 8 estrategias y cuáles se marcan como de pago.</li>"
     "<li><code>RagChunkingComparisonsControllerTest</code>: el Lab de punta a punta, incluidos un 400 (estrategia "
     "desconocida) y un 500 (falta la clave) convertidos en avisos.</li>"
     "<li><code>EstimatorAi::EmbeddingsClientTest</code>: el POST a <code>/embeddings/compare</code> y sus errores.</li></ul>",
     diapo="28", alt="docker compose exec estimator-web bin/rails test -v test/models/rag test/controllers/rag "
                     "test/services/estimator_ai/embeddings_client_test.rb")

# ── 2 ───────────────────────────────────────────────────────────────────────
h2("2 · Embeddings: el sanity check")
paso("scripts/compare.py",
     "Embebe dos textos y calcula su similitud coseno a mano, sin numpy. Tres parejas: cercanas, sin relación y "
     "genéricas.",
     f"""{EXEC} scripts/compare.py \\
  --text-a "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app" \\
  --text-b "Authorization service using JSON Web Tokens for a banking application"
{EXEC} scripts/compare.py --text-a "OAuth 2.0 authentication backend with JWT tokens for fintech mobile app" \\
  --text-b "Database migration from MySQL to PostgreSQL with zero downtime"
{EXEC} scripts/compare.py --text-a "Backend services" --text-b "API development\"""",
     "\n\n".join(leer(f) for f in ("03_compare_A.txt", "04_compare_B.txt", "05_compare_C.txt")),
     "<ul><li><b>0,5957</b>: el mismo concepto con casi ninguna palabra en común. Se queda justo por debajo de 0,6: "
     "los umbrales dependen del modelo y de la redacción.</li>"
     "<li><b>0,1920</b>: temas sin relación, bien separados.</li>"
     "<li><b>0,5407</b>: dos frases cortas y vagas salen casi tan «cercanas» como la primera pareja. Por eso cada "
     "chunk del proyecto lleva una cabecera con proyecto, sector y tecnología.</li></ul>",
     diapo="4")

# ── 3 ───────────────────────────────────────────────────────────────────────
h2("3 · La ingesta: de presupuestos a vectores")
paso("POST /embeddings/ingest",
     "Trocea los presupuestos con la estrategia estructural (un componente = un chunk) y embebe cada chunk. "
     "Devuelve los chunks con su vector y las estadísticas. No se guarda nada: los vectores viven en memoria hasta la "
     "Sesión 8.",
     """curl -s -X POST localhost:8000/embeddings/ingest -H 'Content-Type: application/json' \\
  -d "{\\"budgets\\": $(cat estimator/data/budgets_sample.json)}" \\
  | jq '{stats, primero: .chunks[0] | {chunk_id, token_count, text, metadata, dims: (.embedding | length)}}'""",
     leer("11_ingest.txt").replace("0,0", "0.0"),
     "<ul><li>17 presupuestos → <b>60 chunks</b>, 5.970 tokens, unos <b>0,0001 $</b>.</li>"
     "<li>Cada vector tiene <b>1536</b> números.</li>"
     "<li>El texto empieza con la <b>cabecera de contexto</b> del presupuesto padre; lo que va en "
     "<code>metadata</code> no se embebe, sirve para filtrar (Sesión 8).</li></ul>",
     diapo="11",
     alt="""$body = '{"budgets": ' + [IO.File]::ReadAllText("$PWD\\estimator\\data\\budgets_sample.json") + '}'
$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/embeddings/ingest `
  -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
$r.stats
$r.chunks | Select-Object -First 5 chunk_id, token_count, @{n='dims';e={$_.embedding.Count}}""")

# ── 4 ───────────────────────────────────────────────────────────────────────
h2("4 · Dimensiones: 1536 frente a 768")
paso("compare_chunkers.py --models",
     "El mismo modelo (<code>text-embedding-3-small</code>) pedido a 1536 y a 768 dimensiones (Matryoshka). Compara la "
     "latencia media y el coseno entre los dos primeros componentes.",
     f"{EXEC} scripts/compare_chunkers.py --models small-1536,small-768", sin_logs(leer("06_dimensiones.txt")),
     "El coseno apenas cambia (0,9119 frente a 0,9116) y el vector ocupa la mitad. La latencia de una sola ejecución "
     "varía mucho entre llamadas: no la tomes como dato fijo. Lo que <b>no</b> se puede hacer es comparar un vector "
     "de 1536 con uno de 768.",
     diapo="9-10")

# ── 5 ───────────────────────────────────────────────────────────────────────
h2("5 · Estrategias de chunking gratuitas")
intro("<code>compare_chunkers.py</code> pasa el mismo corpus por varias estrategias. <b>Columnas:</b> número de "
      "chunks; mínimo, p50, p95 y máximo de tokens por chunk; <b>huérfanos</b> (&lt; 20 tokens, sin contexto) y "
      "<b>obesos</b> (&gt; 800 tokens, mezclan temas). Los nombres de estrategia se escriben con guion: "
      "<code>fixed-size</code>, <code>sentence-window</code>.")
paso("structural frente a fixed-size",
     "La estrategia de referencia (un componente = un chunk) contra ventanas fijas de 512 tokens.",
     f"{EXEC} scripts/compare_chunkers.py --strategies structural,fixed-size --show-stats",
     sin_logs(leer("07_structural_fixed.txt")),
     "Casi iguales: el corpus ya está estructurado y casi todos los componentes caben en 512 tokens. El obeso de "
     "structural es MONO-001, una descripción de 1.391 tokens que fixed-size parte en tres.",
     diapo="14, 18")
paso("recursive",
     "Separadores jerárquicos (párrafo → línea → frase → palabra) con un máximo de 512 tokens.",
     f"{EXEC} scripts/compare_chunkers.py --strategies recursive --show-stats", sin_logs(leer("08_recursive.txt")),
     "23 chunks: casi cada presupuesto entero cabe en uno, así que mezcla componentes distintos en el mismo vector. "
     "El huérfano es un trozo de 10 tokens con solo el nombre.",
     diapo="15")
paso("sentence-window frente a structural, con una consulta",
     "Una frase por chunk frente a un componente por chunk, y los 3 chunks más cercanos a una consulta.",
     f"""{EXEC} scripts/compare_chunkers.py --strategies sentence-window,structural --show-stats \\
  --queries "OAuth authentication for fintech mobile app" --show-top-k 3""",
     sin_logs(leer("09_sentence_structural.txt")),
     "<ul><li>sentence-window: 78 chunks y <b>34 huérfanos</b>.</li>"
     "<li>En su top-3 se cuela <b>«Email and password login.»</b> (0,4407), una frase suelta de otro proyecto que no "
     "tiene nada de OAuth ni de fintech.</li>"
     "<li>structural devuelve los tres componentes del proyecto de banca, con scores más altos gracias a la cabecera "
     "de contexto.</li></ul>",
     diapo="17, 19")
paso("Tabla resumen con las seis consultas de prueba",
     "Las cinco estrategias gratuitas con las consultas de <code>data/test_queries.json</code>: el coseno medio del "
     "primer resultado.",
     f"{EXEC} scripts/compare_chunkers.py --strategies structural,fixed-size,recursive,sentence-window,hierarchical \\\n"
     "  --queries all --output-table",
     sin_logs(leer("10_tabla_mecanicas.txt")),
     "sentence-window saca el coseno medio más alto (0,5365) porque una frase corta se parece mucho a una consulta "
     "corta, aunque le falte el contexto. Un score alto no garantiza un buen chunk. recursive es la más baja: sus "
     "chunks mezclan demasiado.",
     diapo="27")

# ── 6 ───────────────────────────────────────────────────────────────────────
h2("6 · Estrategias de pago y el Chunking Lab")
paso("Las tres estrategias que llaman a un modelo",
     "<code>semantic</code> embebe durante la ingesta, <code>propositional</code> usa <code>gpt-4o-mini</code> y "
     "<code>contextual_retrieval</code> usa Claude (necesita <code>ANTHROPIC_API_KEY</code>). Con "
     "<code>--strategies all</code>, si falta la clave de Anthropic la ejecución entera falla: conviene listar las "
     "estrategias a mano.",
     f"{EXEC} scripts/compare_chunkers.py --strategies semantic,propositional --show-stats --show-cost",
     """strategy              n_chunks  p50     orphans  obese  cost_usd  seconds
semantic              34        112,5   0        1      0,0001    5
propositional         778       11      765      0      0,0076    173
contextual_retrieval  60        132,5   0        1      0,14      203
(datos del informe estimator/app/generation/rag/COMPARISON_REPORT.md)""",
     "<ul><li><b>propositional</b>: 13 veces más chunks, casi todos huérfanos, y 3 minutos de ingesta; a cambio, "
     "scores muy altos en consultas concretas.</li>"
     "<li><b>contextual_retrieval</b>: la más cara (0,14 $ con este corpus pequeño) y la más lenta; mejora la "
     "similitud del chunk correcto sin cambiar el número de chunks.</li>"
     "<li><b>semantic</b>: barata, pero ya no es gratis ni instantánea.</li></ul>",
     diapo="20-22",
     test=f"docker compose exec estimator-web bin/rails test test/models/rag/strategy_test.rb")
paso("El Chunking Lab en la web",
     "La misma comparativa con formulario: se eligen estrategias (las de pago van marcadas), consultas y top-k. Cada "
     "ejecución <b>se guarda</b>, así que las estrategias caras se pagan una sola vez.",
     "http://localhost:3000/rag/chunking_comparisons/new      # nueva comparativa\n"
     "http://localhost:3000/rag/chunking_comparisons          # histórico", None,
     "En cada ejecución: la tabla de estadísticas, las barras de coste y el playground con los chunks recuperados por "
     "consulta. Las llamadas largas tienen un timeout de 600 s.",
     diapo="13", test=TEST_LAB)


def render() -> str:
    out = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>S07 · comandos y salidas</title>"
           f"<style>{CSS}</style></head><body>",
           "<h1>Sesión 7 · Los comandos de la sesión y su salida</h1>",
           "<div class='sub'>Embeddings y representación vectorial · Máster en AI Engineering (LIDR). Cada comando que "
           "se usa en el directo, en orden: <b>para qué sirve</b>, <b>cómo se lanza</b>, la <b>salida real</b> "
           "(ejecutada en local el 24/11/2026 sobre la rama <code>session_07_live</code>), <b>cómo leerla</b> y, "
           "cuando lo hay, el <b>test</b> que lo comprueba. La referencia «diapo N» indica dónde aparece en las "
           "diapositivas.</div>"]
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
                out.append(f"<div class='lab'>En PowerShell</div><pre class='alt'>{html.escape(v['alt'])}</pre>")
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
    h = AQUI / "comandos-y-salidas-s07.html"
    h.write_text(render(), encoding="utf-8")
    pdf = AQUI.parent / "S07-comandos-y-salidas.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", h.as_uri()], check=True, capture_output=True)
    print("ok", pdf, pdf.stat().st_size)
