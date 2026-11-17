"""Genera el notebook en vivo de la Sesión 1 (LLMs y setup de entorno de trabajo).

Sigue los siete bloques de la guía de la sesión. Cada celda de código empieza con un rótulo
(«# 2.2 · Iteración 4 …») para poder citarla desde las diapositivas y el guion.

    uv run python build_notebook.py
    # → sesion-01-version-julian.ipynb
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
OUT = HERE / "sesion-01-version-julian.ipynb"

CELLS: list[tuple[str, str]] = []


def md(text: str) -> None:
    CELLS.append(("md", text.strip("\n")))


def code(text: str) -> None:
    CELLS.append(("code", text.strip("\n")))


# =============================================================================
# Portada y configuración
# =============================================================================

md(r"""
# Sesión 1 · LLMs y setup de entorno de trabajo

**Máster en AI Engineering · LIDR · Julián Fernández**

Hoy hacemos la llamada más básica de todas, y la miramos desde el punto de vista de producto:

| Bloque | Qué vemos |
|---|---|
| Configuración | Dependencias, claves y función de costes |
| 2 | Del prompt del usuario al prompt del producto |
| 3 | Parámetros del modelo y herramientas integradas |
| 4 | Comparativa de proveedores en vivo |
| 5 | Agregadores: una interfaz, varios proveedores |
| 6 | Tokens: cómo funcionan y cuánto cuestan |
| 7 | Arquitecturas reales y cierre |

Funciona igual en **Google Colab** (claves en el panel 🔑 *Secrets*) y en **local** (claves en un fichero `.env`).
""")

md(r"""
## Configuración inicial

Tres celdas. Las tres tienen que terminar bien antes de pasar al Bloque 2.
""")

code(r'''
# Config 1 · Dependencias
import importlib
import subprocess
import sys

try:
    import google.colab  # noqa: F401
    EN_COLAB = True
except ImportError:
    EN_COLAB = False

PAQUETES = ["openai", "anthropic", "tiktoken", "litellm"]

if EN_COLAB:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *PAQUETES])

import warnings
warnings.filterwarnings("ignore")  # avisos de dependencias de gradio/typer en Colab: inofensivos

for nombre in PAQUETES:
    modulo = importlib.import_module(nombre)
    version = getattr(modulo, "__version__", "")
    if not version:
        from importlib.metadata import version as _v
        version = _v(nombre)
    print(f"✅ {nombre} {version}")
''')

code(r'''
# Config 2 · Claves y clientes
import os

def leer_clave(nombre: str) -> str | None:
    """Colab Secrets si estamos en Colab; si no, variables de entorno o el fichero .env."""
    if EN_COLAB:
        from google.colab import userdata
        try:
            return userdata.get(nombre)
        except Exception:
            return None
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        pass
    return os.environ.get(nombre) or None

from openai import OpenAI
from anthropic import Anthropic

OPENAI_API_KEY = leer_clave("OPENAI_API_KEY")
ANTHROPIC_API_KEY = leer_clave("ANTHROPIC_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# LiteLLM lee las claves del entorno
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if ANTHROPIC_API_KEY:
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

print("OpenAI:   ", "OK" if openai_client else "falta OPENAI_API_KEY")
print("Anthropic:", "OK" if anthropic_client else "falta ANTHROPIC_API_KEY (las celdas de Anthropic lo avisarán)")
if openai_client:
    print("Clients configured successfully")
''')

code(r'''
# Config 3 · Función de costes
# Precios en dólares por millón de tokens (entrada, salida). Comprobados el 16/11/2026
# en las páginas oficiales de precios de OpenAI y Anthropic.
PRICES = {
    "gpt-4o-mini":       (0.15, 0.60),
    "gpt-4o":            (2.50, 10.00),
    "gpt-4.1-mini":      (0.40, 1.60),
    "gpt-5.4-nano":      (0.20, 1.25),
    "gpt-5.4-mini":      (0.75, 4.50),
    "gpt-5.4":           (2.50, 15.00),
    "gpt-5.5":           (5.00, 30.00),
    "claude-haiku-4-5":  (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}

def precio(modelo: str) -> tuple[float, float]:
    """Busca el precio por prefijo: 'claude-haiku-4-5-20251001' usa el de 'claude-haiku-4-5'."""
    modelo = modelo.split("/")[-1]  # 'openai/gpt-4o-mini' → 'gpt-4o-mini'
    for nombre in sorted(PRICES, key=len, reverse=True):
        if modelo.startswith(nombre):
            return PRICES[nombre]
    raise KeyError(f"Sin precio para {modelo}")

def calcular_coste(modelo: str, tokens_entrada: int, tokens_salida: int) -> float:
    p_in, p_out = precio(modelo)
    return (tokens_entrada * p_in + tokens_salida * p_out) / 1_000_000

def resumen_uso(modelo: str, tokens_entrada: int, tokens_salida: int) -> str:
    coste = calcular_coste(modelo, tokens_entrada, tokens_salida)
    return f"[{modelo}] entrada {tokens_entrada} · salida {tokens_salida} · ${coste:.6f}"

print("Cost calculation function loaded")
print(resumen_uso("gpt-4o-mini", 1_000, 500))
''')

# =============================================================================
# Bloque 2
# =============================================================================

md(r"""
---
# Bloque 2 · Del prompt del usuario al prompt del producto

En un producto, la calidad de la respuesta **no puede depender de que el usuario sepa escribir prompts**.
La diseña quien desarrolla, y su herramienta principal es el *system prompt*.

## 2.1 · El problema: la respuesta genérica
""")

code(r'''
# 2.1 · Sin system prompt
MODEL = "gpt-4o-mini"

respuesta = openai_client.responses.create(
    model=MODEL,
    input="We're migrating our payment service from a monolith to microservices. What should we consider?",
)

print(respuesta.output_text)
print()
print(f"{len(respuesta.output_text.split())} palabras")
print(resumen_uso(MODEL, respuesta.usage.input_tokens, respuesta.usage.output_tokens))
''')

md(r"""
¿Pondríais esto en un producto? ¿Se lo daríais a un cliente que paga por vuestro software?

## 2.2 · El system prompt como contrato de calidad

La pregunta del usuario se fija **una vez**. Lo único que cambia en las cuatro iteraciones es el system prompt.
""")

code(r'''
# 2.2 · La pregunta del usuario (no cambia)
USER_QUESTION = "We're migrating our payment service from a monolith to microservices. What should we consider?"

def preguntar(system_prompt: str, pregunta: str = USER_QUESTION, model: str = MODEL, **params):
    """Una llamada a la Responses API: 'instructions' es el system prompt, 'input' lo que escribe el usuario."""
    r = openai_client.responses.create(model=model, instructions=system_prompt, input=pregunta, **params)
    print(r.output_text)
    print()
    print(f"{len(r.output_text.split())} palabras · {resumen_uso(model, r.usage.input_tokens, r.usage.output_tokens)}")
    return r
''')

code(r'''
# 2.2 · Iteración 1 — rol básico
SYSTEM_PROMPT_V1 = "You are a senior software architect with experience in distributed systems."

r1 = preguntar(SYSTEM_PROMPT_V1)
''')

code(r'''
# 2.2 · Iteración 2 — rol + audiencia + formato
SYSTEM_PROMPT_V2 = """You are a senior software architect with 15+ years of experience building payment infrastructure.

Your audience: backend developers with 5+ years of experience who have never led a migration like this one.

Format: plain prose, no bullet lists, at most 250 words. Every paragraph must contain an actionable insight."""

r2 = preguntar(SYSTEM_PROMPT_V2)
''')

code(r'''
# 2.2 · Iteración 3 — restricciones de comportamiento
SYSTEM_PROMPT_V3 = SYSTEM_PROMPT_V2 + """

Behaviour:
- When you mention a trade-off, state its concrete consequence (latency, cost, team effort or risk).
- If the question lacks context, state your assumptions explicitly before answering.
- Do not recommend specific vendors or commercial products.
- Mention at least one non-obvious risk."""

r3 = preguntar(SYSTEM_PROMPT_V3)
''')

code(r'''
# 2.2 · Iteración 4 — contrato completo de producción
PRODUCTION_SYSTEM_PROMPT = """You are a principal engineer who has led the migration of a PCI-DSS compliant payment platform
processing more than $1B a year from a monolith to microservices.

Audience: backend developers with 5+ years of experience who have never led a migration like this one.

Response structure (follow it exactly):
1. Open with the single most critical decision they must make first, in one sentence.
2. Then give 2-3 considerations. For each one: what to do, why, and what happens if they get it wrong.
3. Close with one risk that teams usually overlook.

Constraints:
- Plain prose, at most 250 words.
- State your assumptions in one sentence if the question lacks context.
- Every trade-off must include a concrete consequence.
- Do not recommend vendors or commercial products.
- Do not use filler phrases like "Great question!" or "It depends" without quantifying."""

r4 = preguntar(PRODUCTION_SYSTEM_PROMPT)
''')

md(r"""
Tras cada iteración: **¿qué ha cambiado y por qué?** Cada línea del system prompt es una decisión de producto.

## 2.3 · Abstraer al usuario del prompting — naive vs production

Un revisor de *pull requests*. El usuario solo pega un diff; nunca ve el prompt.
""")

code(r'''
# 2.3 · El diff que revisamos (código de pagos con fallos)
DIFF = """
+def charge_customer(customer_id, amount):
+    customer = db.query(f"SELECT * FROM customers WHERE id = {customer_id}")
+    total = amount * 1.21
+    result = stripe.Charge.create(amount=total, currency="eur", customer=customer["stripe_id"])
+    db.execute(f"UPDATE orders SET paid = 1 WHERE customer_id = {customer_id}")
+    return result
"""
print(f"El usuario escribe {len(DIFF.strip().splitlines())} líneas de código.")
''')

code(r'''
# 2.3 · review_pull_request_naive()
def review_pull_request_naive(diff: str) -> str:
    r = openai_client.responses.create(
        model=MODEL,
        instructions="You are a code reviewer.",
        input=diff,
    )
    print(resumen_uso(MODEL, r.usage.input_tokens, r.usage.output_tokens))
    return r.output_text

print(review_pull_request_naive(DIFF))
''')

code(r'''
# 2.3 · review_pull_request() — prompt de producción
PR_REVIEW_SYSTEM_PROMPT = """You are a senior backend engineer reviewing pull requests for a payments team.
Payments code handles real money and personal data, so correctness and security come first.

Review criteria, in strict priority order:
1. Security: injection, secrets, unsafe handling of personal or card data.
2. Money correctness: rounding, units (cents vs euros), currency, double charges, idempotency.
3. Data consistency: what happens if a step fails halfway (transactions, retries).
4. Readability and tests, only if the points above are clean.

Output format (Markdown):
- First line: a verdict, exactly one of APPROVE, REQUEST CHANGES or BLOCK.
- Then a numbered list of findings, most severe first. Each finding: severity (critical/major/minor),
  the exact line, what is wrong, and a corrected snippet.
- At most 5 findings. Do not list style nitpicks if there is any critical finding.

Behaviour:
- Be direct and specific. No praise, no filler.
- If you are not sure something is a bug, say what you would need to check.
- Never invent context that is not in the diff."""

def review_pull_request(diff: str, language: str = "Python", service: str = "payments") -> str:
    # Lo que el usuario aporta son sus datos; el prompt lo construye el producto.
    user_input = f"Language: {language}\nService: {service}\n\nDiff to review:\n```diff\n{diff}\n```"
    r = openai_client.responses.create(
        model=MODEL,
        instructions=PR_REVIEW_SYSTEM_PROMPT,
        input=user_input,
        temperature=0.2,
    )
    print(resumen_uso(MODEL, r.usage.input_tokens, r.usage.output_tokens))
    return r.output_text

print(f"System prompt: {len(PR_REVIEW_SYSTEM_PROMPT.split())} palabras que el usuario nunca ve.\n")
print(review_pull_request(DIFF))
''')

md(r"""
### Tu turno (opcional)

Piensa en una tarea de tu trabajo y escribe su función: el usuario aporta los datos y tú el prompt.
""")

code(r'''
# 2.3 · Tu turno
MI_SYSTEM_PROMPT = """You are ...

Audience: ...

Format: ...

Constraints:
- ..."""

def mi_funcion(datos_del_usuario: str) -> str:
    r = openai_client.responses.create(model=MODEL, instructions=MI_SYSTEM_PROMPT, input=datos_del_usuario)
    return r.output_text

# print(mi_funcion("..."))
''')

md(r"""
## 2.4 · Consistencia de respuestas

¿Es aceptable que dos usuarios reciban respuestas de calidad diferente ante la misma pregunta?
""")

code(r'''
# 2.4 · temperature 1.0 + prompt vago → cuatro respuestas distintas
for i in range(4):
    r = openai_client.responses.create(
        model=MODEL,
        instructions="Help the user.",
        input="What is the main risk of migrating payments to microservices? Answer in one or two sentences.",
        temperature=1.0,
        max_output_tokens=120,
    )
    print(f"--- {i + 1} ---\n{r.output_text}\n")
''')

code(r'''
# 2.4 · temperature 0.1 + prompt preciso → cuatro respuestas casi idénticas
PRECISE_PROMPT = """Answer in exactly this format and nothing else:
Risk: <one noun phrase, at most 6 words>
Why: <one sentence, at most 20 words>"""

for i in range(4):
    r = openai_client.responses.create(
        model=MODEL,
        instructions=PRECISE_PROMPT,
        input="What is the main risk of migrating payments to microservices?",
        temperature=0.1,
        max_output_tokens=80,
    )
    print(f"--- {i + 1} ---\n{r.output_text}\n")
''')

md(r"""
Los modelos son estocásticos. La consistencia la ponen **tus instrucciones y tus parámetros**:
`temperature`, `max_output_tokens` y *structured outputs* (en la Sesión 4).

---
# Bloque 3 · Parámetros del modelo y herramientas integradas

## 3.1 · Temperature
""")

# =============================================================================
# Bloque 3
# =============================================================================

code(r'''
# 3.1 · Misma pregunta, tres temperaturas
NAMING = "Suggest one name for a SaaS that estimates the cost of software projects. Reply with the name only."

for temperatura in (0.0, 0.7, 1.5):
    nombres = []
    for _ in range(3):
        r = openai_client.responses.create(model=MODEL, input=NAMING, temperature=temperatura, max_output_tokens=20)
        nombres.append(r.output_text.strip())
    print(f"temperature={temperatura}: {nombres}")
''')

md(r"""
`top_p` es la alternativa a `temperature`: **usa uno u otro, nunca los dos**. En Claude 4.5 y posteriores la API
rechaza combinarlos.

En producción, empieza con `temperature` entre 0.2 y 0.3 y súbela solo si necesitas creatividad.

## 3.2 · max_output_tokens
""")

code(r'''
# 3.2 · Tres techos de salida
for limite in (50, 200, 800):
    r = openai_client.responses.create(
        model=MODEL,
        instructions=PRODUCTION_SYSTEM_PROMPT,
        input=USER_QUESTION,
        max_output_tokens=limite,
    )
    motivo = r.incomplete_details.reason if r.incomplete_details else "-"
    print(f"max_output_tokens={limite:>4} → status={r.status:<10} motivo={motivo:<18} "
          f"salida={r.usage.output_tokens} tokens")
''')

md(r"""
`max_output_tokens` es un **techo de seguridad**, no un control de longitud: con 50 la respuesta se corta a medias
(`status="incomplete"`). La longitud real se pide en el system prompt.

En Anthropic (`max_tokens`) es **obligatorio**; en OpenAI y Gemini, opcional.

## 3.3 · stop y seed

Estos dos van por la interfaz **Chat Completions**, la otra API de OpenAI (la volveremos a ver con LiteLLM).
""")

code(r'''
# 3.3 · stop: el modelo se para al generar la secuencia
r = openai_client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "List the 6 phases of a software project, numbered 1. to 6."}],
    stop=["4."],
)
print(r.choices[0].message.content)
print("finish_reason:", r.choices[0].finish_reason)
''')

code(r'''
# 3.3 · seed: misma semilla, misma respuesta (casi siempre)
salidas = []
for _ in range(3):
    r = openai_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Invent a two-sentence story about a database."}],
        temperature=1.0,
        seed=42,
    )
    salidas.append(r.choices[0].message.content)
    print(f"[{r.system_fingerprint}] {r.choices[0].message.content}\n")

print("¿Las tres iguales?", len(set(salidas)) == 1)
''')

md(r"""
`seed` es reproducibilidad **best effort**: si cambia el `system_fingerprint` (el backend del proveedor), puede
cambiar la respuesta.

## 3.4 · Resumen de parámetros

| Tarea | temperature | max_output_tokens | Otros |
|---|---|---|---|
| Extracción de datos (facturas, formularios) | 0 – 0.2 | justo para el JSON | *structured outputs* |
| Clasificación / etiquetado | 0 | pequeño | `stop` o etiquetas cerradas |
| Asistente técnico, soporte | 0.2 – 0.4 | 300 – 800 | system prompt con formato |
| Redacción, resúmenes | 0.5 – 0.7 | según el texto | |
| Brainstorming, naming | 0.8 – 1.2 | pequeño | varias muestras |

Son puntos de partida, no verdades. Los **modelos de razonamiento** (familia gpt-5 con razonamiento, o-series)
no aceptan la mayoría de estos parámetros: se controlan con `reasoning.effort`.

## 3.5 · Herramientas integradas

Hasta ahora el modelo solo sabe lo que aprendió en el entrenamiento: nada reciente, nada privado y no ejecuta
código. Las herramientas integradas las ejecuta **el proveedor en sus servidores**; el modelo decide cuándo
usarlas y todo ocurre **en una sola llamada**.

| Herramienta | OpenAI (Responses API) | Anthropic (Messages API) |
|---|---|---|
| Búsqueda web | `web_search` | `web_search_20250305` (habilitar en la Console) |
| Búsqueda en documentos | `file_search` (vector stores) | — (Files API + contexto) |
| Ejecutar código | `code_interpreter` | `code_execution` |
| Controlar un ordenador | `computer_use_preview` | `computer_use` |
| Servidores MCP remotos | `mcp` | conector MCP |

## 3.6 · web_search con OpenAI
""")

code(r'''
# 3.6 · web_search (OpenAI)
DEVDAY = "What were the most important announcements at OpenAI DevDay 2025? Three bullet points."

r_web = openai_client.responses.create(
    model="gpt-4o",  # no todos los modelos soportan la herramienta: gpt-4o sí
    tools=[{"type": "web_search"}],
    input=DEVDAY,
)
print(r_web.output_text)
print()
print(resumen_uso("gpt-4o", r_web.usage.input_tokens, r_web.usage.output_tokens))
print("Pasos:", [item.type for item in r_web.output])
''')

code(r'''
# 3.6 · Las fuentes, en las annotations
fuentes = {}
for item in r_web.output:
    if item.type == "message":
        for parte in item.content:
            for a in getattr(parte, "annotations", None) or []:
                if a.type == "url_citation":
                    fuentes[a.url] = a.title

for url, titulo in fuentes.items():
    print(f"- {titulo}\n  {url}")
''')

md(r"""
Si tu producto busca en la web, **enseñar las fuentes no es opcional**: es UX y es confianza.

## 3.7 · web_search con Anthropic

Puede fallar si la organización no ha habilitado la búsqueda web en la Claude Console: es una decisión de
gobernanza del administrador.
""")

code(r'''
# 3.7 · web_search (Anthropic)
try:
    if anthropic_client is None:
        raise RuntimeError("No hay ANTHROPIC_API_KEY configurada.")
    r_claude = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,  # obligatorio en Anthropic
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": DEVDAY}],
    )
    for bloque in r_claude.content:
        if bloque.type == "text":
            print(bloque.text, end="")
            for c in getattr(bloque, "citations", None) or []:
                print(f"  [{c.url}]", end="")
    print()
    print(resumen_uso("claude-haiku-4-5", r_claude.usage.input_tokens, r_claude.usage.output_tokens))
except Exception as e:
    print(f"⚠️ La búsqueda web de Anthropic no está disponible: {type(e).__name__}: {e}")
    print("Revisa: clave de Anthropic con saldo y 'Web search' habilitado en la Claude Console (Settings → Privacy).")
''')

md(r"""
Tres diferencias con OpenAI:

1. **Sintaxis versionada**: `web_search_20250305`. Anthropic fecha sus herramientas.
2. **Hay que habilitarla** en la Console.
3. **Control explícito** con `max_uses`: cuántas búsquedas puede hacer en una llamada.

Misma funcionalidad, filosofías distintas: Anthropic prioriza control y gobernanza; OpenAI, simplicidad.

## 3.8 · Otras herramientas

- **`file_search`** (OpenAI): RAG gestionado. Subes documentos y OpenAI los trocea y vectoriza. Es exactamente lo
  que construiremos nosotros en el **Módulo 3**, para tener criterio entre usar lo del proveedor o hacerlo propio.
- **`code_interpreter` / `code_execution`**: ejecuta Python en un sandbox. El modelo deja de sumar «de cabeza».
- **`computer_use`**: el modelo maneja un ordenador con capturas, ratón y teclado.
- **MCP remoto**: herramientas propias expuestas al modelo. Lo veremos en el **Módulo 5**, con agentes.

---
# Bloque 4 · Comparativa de proveedores en vivo

## 4.1 · Misma pregunta, distinto proveedor
""")

# =============================================================================
# Bloque 4
# =============================================================================

code(r'''
# 4.1 · El escenario y el system prompt común
COMPARISON_SYSTEM_PROMPT = """You are a staff data engineer advising a SaaS team.

Answer in this structure:
1. Recommendation (one sentence).
2. Why, with numbers: query latency, storage and operational cost.
3. When the other option would be better.

Constraints: at most 200 words. Do not answer "it depends" without quantifying. No vendor marketing."""

SCENARIO = """Our SaaS runs on PostgreSQL 16. The events table has 50M rows and grows 2M rows per month.
The analytics dashboard (aggregations by customer and by month) now takes 8-12 seconds to load.
Should we add a columnar store (e.g. ClickHouse) or stay on Postgres with read replicas and better indexes?"""

import time
resultados = {}
''')

code(r'''
# 4.1 · OpenAI (Responses API)
t0 = time.time()
r_oa = openai_client.responses.create(
    model="gpt-4o-mini",
    instructions=COMPARISON_SYSTEM_PROMPT,
    input=SCENARIO,
    temperature=0.2,
)
resultados["openai · gpt-4o-mini"] = ("gpt-4o-mini", r_oa.usage.input_tokens, r_oa.usage.output_tokens,
                                      time.time() - t0, len(r_oa.output_text.split()))
print(r_oa.output_text)
print()
print(resumen_uso("gpt-4o-mini", r_oa.usage.input_tokens, r_oa.usage.output_tokens))
''')

code(r'''
# 4.1 · Anthropic (Messages API)
try:
    if anthropic_client is None:
        raise RuntimeError("No hay ANTHROPIC_API_KEY configurada.")
    t0 = time.time()
    r_an = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        system=COMPARISON_SYSTEM_PROMPT,           # en Anthropic el system va aparte
        messages=[{"role": "user", "content": SCENARIO}],
        max_tokens=600,                            # obligatorio
        # el SDK actual de Anthropic ya no acepta temperature en messages.create
    )
    texto = r_an.content[0].text
    resultados["anthropic · claude-haiku-4-5"] = ("claude-haiku-4-5", r_an.usage.input_tokens,
                                                  r_an.usage.output_tokens, time.time() - t0, len(texto.split()))
    print(texto)
    print()
    print(resumen_uso("claude-haiku-4-5", r_an.usage.input_tokens, r_an.usage.output_tokens))
except Exception as e:
    print(f"⚠️ Anthropic no disponible: {type(e).__name__}: {e}")
''')

code(r'''
# 4.1 · Lado a lado
print(f"{'Proveedor · modelo':<32}{'entrada':>9}{'salida':>9}{'palabras':>10}{'segundos':>10}{'coste $':>12}")
for etiqueta, (modelo, t_in, t_out, seg, palabras) in resultados.items():
    print(f"{etiqueta:<32}{t_in:>9}{t_out:>9}{palabras:>10}{seg:>10.1f}{calcular_coste(modelo, t_in, t_out):>12.6f}")
''')

md(r"""
- ¿Cuál es más útil? ¿Cuál respeta mejor el formato? ¿Alguna dice «it depends» sin cuantificar?
- ¿Por qué Anthropic suele contar **más tokens de entrada** para el mismo texto? Cada proveedor tiene su
  tokenizador: los tokens no se pueden comparar entre proveedores.

## 4.2 · Misma pregunta, distinto tier de modelo
""")

code(r'''
# 4.2 · Tiers de OpenAI
openai_models = [
    "gpt-4o-mini",
    "gpt-5.4-mini",   # coméntalo si tu cuenta no tiene acceso
    "gpt-5.4",        # coméntalo si tu cuenta no tiene acceso
]

for modelo in openai_models:
    t0 = time.time()
    r = openai_client.responses.create(model=modelo, instructions=COMPARISON_SYSTEM_PROMPT, input=SCENARIO)
    seg = time.time() - t0
    resultados[f"openai · {modelo}"] = (modelo, r.usage.input_tokens, r.usage.output_tokens, seg,
                                         len(r.output_text.split()))
    print(f"=== {modelo} · {seg:.1f} s · {resumen_uso(modelo, r.usage.input_tokens, r.usage.output_tokens)}")
    print(r.output_text)
    print()
''')

code(r'''
# 4.2 · Tu turno — tiers de Anthropic
anthropic_models = [
    "claude-haiku-4-5-20251001",
    # "claude-sonnet-4-6",
]

for modelo in anthropic_models:
    try:
        if anthropic_client is None:
            raise RuntimeError("No hay ANTHROPIC_API_KEY configurada.")
        r = anthropic_client.messages.create(model=modelo, system=COMPARISON_SYSTEM_PROMPT, max_tokens=600,
                                             messages=[{"role": "user", "content": SCENARIO}])
        print(f"=== {modelo} · {resumen_uso(modelo, r.usage.input_tokens, r.usage.output_tokens)}")
        print(r.content[0].text, "\n")
    except Exception as e:
        print(f"⚠️ {modelo}: {type(e).__name__}: {e}")
''')

code(r'''
# 4.2 · ¿Cuánto más caro es cada tier?
base = calcular_coste("gpt-4o-mini", 1_000_000, 1_000_000)
for modelo in ["gpt-4o-mini", "gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4", "claude-haiku-4-5", "claude-sonnet-4-6"]:
    p_in, p_out = precio(modelo)
    print(f"{modelo:<20} entrada ${p_in:>5.2f}/M · salida ${p_out:>6.2f}/M · "
          f"{calcular_coste(modelo, 1_000_000, 1_000_000) / base:>5.1f}× gpt-4o-mini")
''')

md(r"""
## 4.3 · Criterios de selección

- Un chatbot de soporte que responde FAQs: ¿qué modelo?
- Análisis de contratos legales de 50 páginas: ¿cambia la elección?
- 10.000 usuarios: ¿el mismo modelo para todos, o uno barato por defecto y escalar cuando haga falta?

En producción lo habitual es el **routing / cascada**: un modelo barato para el 80 % de las peticiones y uno
premium solo cuando la tarea lo pide. Lo construimos en la **Sesión 3**.

---
# Bloque 5 · Agregadores: una interfaz, varios proveedores

## 5.2 · LiteLLM en vivo
""")

# =============================================================================
# Bloque 5
# =============================================================================

code(r'''
# 5.2 · El mismo código para los dos proveedores
import litellm
litellm.suppress_debug_info = True

WEBHOOKS_SYSTEM = "You are a pragmatic backend engineering lead. Answer in at most 150 words, with a clear recommendation."
WEBHOOKS_QUESTION = ("We receive 500 Stripe webhooks per second in our Rails API. Should we process them synchronously "
                     "in the request, or push them to a queue and process them in background workers?")

for modelo in ["openai/gpt-4o-mini", "anthropic/claude-haiku-4-5-20251001"]:
    try:
        resp = litellm.completion(
            model=modelo,  # ← lo único que cambia
            messages=[
                {"role": "system", "content": WEBHOOKS_SYSTEM},
                {"role": "user", "content": WEBHOOKS_QUESTION},
            ],
            temperature=0.2,
            max_tokens=400,
        )
        print(f"=== {modelo} · entrada {resp.usage.prompt_tokens} · salida {resp.usage.completion_tokens} · "
              f"${litellm.completion_cost(resp):.6f}")
        print(resp.choices[0].message.content, "\n")
    except Exception as e:
        print(f"⚠️ {modelo}: {type(e).__name__}: {str(e)[:160]}\n")
''')

md(r"""
Tres diferencias con las llamadas directas del Bloque 4:

| | Llamada directa (Responses API) | LiteLLM (formato Chat Completions) |
|---|---|---|
| Entrada | `instructions` + `input` | `messages` con roles |
| Texto | `resp.output_text` | `resp.choices[0].message.content` |
| Tokens | `resp.usage.input_tokens` | `resp.usage.prompt_tokens` |

LiteLLM usa **Chat Completions** como idioma común: por eso conviene conocer las dos APIs de OpenAI.

## 5.3 · Cambiar de proveedor en una línea
""")

code(r'''
# 5.3 · evaluate_technical_decision()
DECISION_SYSTEM = """You are a principal engineer. Evaluate the technical decision you receive.
Reply with: Verdict (GO / NO-GO / NEEDS DATA), then the two strongest reasons, then one thing to measure first.
At most 120 words."""

def evaluate_technical_decision(decision: str, model: str = "openai/gpt-4o-mini") -> str:
    resp = litellm.completion(
        model=model,
        messages=[{"role": "system", "content": DECISION_SYSTEM}, {"role": "user", "content": decision}],
        temperature=0.2,
        max_tokens=300,
    )
    return resp.choices[0].message.content

DECISION = "Move our 3 GB Postgres database to a managed serverless database to save on ops work."

print(evaluate_technical_decision(DECISION))
# print(evaluate_technical_decision(DECISION, model="anthropic/claude-haiku-4-5-20251001"))
''')

md(r"""
En la **Sesión 3** convertimos esto en la capa de proveedores del proyecto, con **fallback automático**: si OpenAI
se cae, la aplicación pasa a Anthropic sin que el usuario lo note.

---
# Bloque 6 · Tokens: cómo funcionan y cuánto cuestan

## 6.1 · Anatomía de los tokens
""")

# =============================================================================
# Bloque 6
# =============================================================================

code(r'''
# 6.1 · Mismo contenido, distintos formatos
import json
import tiktoken

enc = tiktoken.get_encoding("o200k_base")      # tokenizador de gpt-4o, gpt-4o-mini y la familia gpt-5
enc_viejo = tiktoken.get_encoding("cl100k_base")  # el de gpt-4 y gpt-3.5 (2023)

TEXTOS = {
    "Inglés": "We are migrating our payment service from a monolith to microservices. "
              "Which risks should we consider before we start, and how long will it take?",
    "Español": "Estamos migrando nuestro servicio de pagos de un monolito a microservicios. "
               "¿Qué riesgos deberíamos considerar antes de empezar y cuánto tiempo llevará?",
    "Código Python": "def total(items):\n    return sum(i.price * i.quantity for i in items if i.active)",
    "JSON": json.dumps({"customer_id": 4821, "amount_eur": 129.90, "currency": "EUR", "status": "paid"}),
    "PRODUCTION_SYSTEM_PROMPT": PRODUCTION_SYSTEM_PROMPT,
}

print(f"{'Texto':<26}{'caracteres':>11}{'palabras':>10}{'o200k':>8}{'cl100k':>8}{'car./token':>12}")
for nombre, texto in TEXTOS.items():
    n = len(enc.encode(texto))
    n_viejo = len(enc_viejo.encode(texto))
    print(f"{nombre:<26}{len(texto):>11}{len(texto.split()):>10}{n:>8}{n_viejo:>8}{len(texto) / n:>12.1f}")

es, en = TEXTOS["Español"], TEXTOS["Inglés"]
for etiqueta, e in (("o200k (hoy)", enc), ("cl100k (2023)", enc_viejo)):
    print(f"\nEspañol frente a inglés con {etiqueta}: {len(e.encode(es)) / len(e.encode(en)) - 1:+.0%} tokens")
''')

code(r'''
# 6.1 · Token a token
FRASE = "¿Cuánto cuesta migrar una base de datos PostgreSQL a Amazon Aurora?"

ids = enc.encode(FRASE)
piezas = [enc.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids]
print(f"{len(ids)} tokens:")
print(" | ".join(piezas))
''')

code(r'''
# 6.1 · Tu turno: tokeniza tu texto o tu system prompt del Bloque 2
MI_TEXTO = "Escribe aquí tu texto"

ids = enc.encode(MI_TEXTO)
print(len(ids), "tokens →", " | ".join(enc.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids))
''')

md(r"""
## 6.2 · Entrada vs salida: la asimetría que define tu factura
""")

code(r'''
# 6.2 · Misma pregunta, tres longitudes de respuesta
medidas = []
for palabras in (50, 200, 500):
    r = openai_client.responses.create(
        model=MODEL,
        instructions=PRODUCTION_SYSTEM_PROMPT.replace("at most 250 words", f"about {palabras} words"),
        input=USER_QUESTION,
    )
    p_in, p_out = precio(MODEL)
    coste_in = r.usage.input_tokens * p_in / 1e6
    coste_out = r.usage.output_tokens * p_out / 1e6
    medidas.append((r.usage.input_tokens, r.usage.output_tokens))
    print(f"~{palabras:>3} palabras · entrada {r.usage.input_tokens:>4} tok (${coste_in:.6f}) · "
          f"salida {r.usage.output_tokens:>4} tok (${coste_out:.6f}) · la salida es el "
          f"{coste_out / (coste_in + coste_out):.0%} del coste")
''')

code(r'''
# 6.2 · Proyección a escala: 10.000 usuarios × 5 llamadas/día × 30 días
LLAMADAS_MES = 10_000 * 5 * 30
t_in, t_out = medidas[1]  # la respuesta mediana de la celda anterior

print(f"{LLAMADAS_MES:,} llamadas/mes con {t_in} tokens de entrada y {t_out} de salida por llamada\n")
filas = []
for modelo in ["gpt-4o-mini", "gpt-5.4-nano", "gpt-5.4-mini", "claude-haiku-4-5", "gpt-5.4", "claude-sonnet-4-6"]:
    filas.append((modelo, calcular_coste(modelo, t_in, t_out) * LLAMADAS_MES))
barato = filas[0][1]
for modelo, mes in filas:
    print(f"{modelo:<20} ${mes:>10,.0f}/mes   {mes / barato:>5.1f}×")
''')

md(r"""
## 6.3 · El coste oculto de las conversaciones multi-turno

Cada llamada **reenvía todo el historial**.
""")

code(r'''
# 6.3 · Incident response en 5 turnos
INCIDENT_SYSTEM = "You are an SRE helping during a production incident. Be concise: at most 120 words per answer."
TURNOS = [
    "p99 latency of our checkout API jumped from 200 ms to 3 s ten minutes ago. Where do we start?",
    "CPU is normal, but the database connection pool is at 100% usage.",
    "We deployed a new version 15 minutes ago that adds a query to load the customer's loyalty points.",
    "The new query has no index on customer_id and the table has 40M rows. Rollback or hotfix?",
    "We rolled back and latency is recovering. What should go in the postmortem?",
]

historial = []
filas = []
acumulado = 0.0
for n, mensaje in enumerate(TURNOS, start=1):
    historial.append({"role": "user", "content": mensaje})
    r = openai_client.responses.create(model=MODEL, instructions=INCIDENT_SYSTEM, input=historial)
    historial.append({"role": "assistant", "content": r.output_text})
    coste = calcular_coste(MODEL, r.usage.input_tokens, r.usage.output_tokens)
    acumulado += coste
    filas.append((n, r.usage.input_tokens, r.usage.output_tokens, coste, acumulado))

print(f"{'Turno':>5}{'entrada':>9}{'salida':>8}{'coste turno $':>15}{'acumulado $':>14}")
for n, t_in, t_out, coste, acum in filas:
    print(f"{n:>5}{t_in:>9}{t_out:>8}{coste:>15.6f}{acum:>14.6f}")
print(f"\nEl turno 5 envía {filas[-1][1] / filas[0][1]:.1f}× más tokens de entrada que el turno 1.")
''')

code(r'''
# 6.3 · La gráfica: tokens y coste turno a turno
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

turnos = [f[0] for f in filas]
entrada = [f[1] for f in filas]
salida = [f[2] for f in filas]
coste_turno = [f[3] for f in filas]
coste_acumulado = [f[4] for f in filas]

# Del verde al rojo a medida que la conversación (y la factura) crece
colores = plt.cm.RdYlGn_r([0.1 + 0.8 * i / max(len(filas) - 1, 1) for i in range(len(filas))])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8))

# Izquierda: lo que se envía (todo el historial) frente a lo que se recibe
ax1.bar(turnos, entrada, color=colores, edgecolor="black", linewidth=0.6, label="entrada (historial completo)")
ax1.bar(turnos, salida, bottom=entrada, color="#B0B7C3", edgecolor="black", linewidth=0.6, label="salida (respuesta)")
for x, e in zip(turnos, entrada):
    ax1.text(x, e / 2, str(e), ha="center", va="center", fontsize=9, fontweight="bold")
ax1.set_title("Tokens de cada turno")
ax1.set_ylabel("Tokens")
ax1.legend(loc="upper left")

# Derecha: coste de cada turno (barras) y coste acumulado (línea con el área pintada)
ax2.fill_between(turnos, coste_acumulado, color="#D62728", alpha=0.15)
ax2.plot(turnos, coste_acumulado, color="#D62728", marker="o", linewidth=2.5, label="coste acumulado")
ax2.bar(turnos, coste_turno, color=colores, edgecolor="black", linewidth=0.6, width=0.5, label="coste del turno")
for x, a in zip(turnos, coste_acumulado):
    ax2.annotate(f"${a:.6f}", (x, a), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
ax2.set_ylim(0, max(coste_acumulado) * 1.18)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:.4f}"))
ax2.set_title("Coste por turno y acumulado")
ax2.set_ylabel("Dólares")
ax2.legend(loc="upper left")

for ax in (ax1, ax2):
    ax.set_xlabel("Turno de la conversación")
    ax.set_xticks(turnos)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

fig.suptitle(f"{MODEL}: el turno {turnos[-1]} envía {entrada[-1] / entrada[0]:.1f}× más tokens de entrada que el turno 1",
             fontweight="bold")
fig.tight_layout()
plt.show()
''')

code(r'''
# 6.3 · El system prompt se paga en cada turno
tokens_prompt = len(enc.encode(PRODUCTION_SYSTEM_PROMPT))
for turnos in (1, 5, 20):
    total = tokens_prompt * turnos
    print(f"{turnos:>2} turnos → {total:>6,} tokens de entrada solo en system prompt "
          f"(${calcular_coste(MODEL, total, 0):.6f} con {MODEL}, ${calcular_coste('gpt-5.4', total, 0):.6f} con gpt-5.4)")
''')

md(r"""
Cómo se mitiga (lo trabajamos en sesiones posteriores):

- Truncar el historial (ventana deslizante).
- Resumir los turnos antiguos.
- *Prompt caching*: Anthropic cobra los aciertos de caché al 10 % del precio de entrada.
- `previous_response_id` en la Responses API: el historial se queda en el servidor de OpenAI.

En un producto con conversaciones largas, gestionar el contexto **no es una optimización: es viabilidad económica**.

---
# Bloque 7 · Arquitecturas reales y cierre

Para cada producto: ¿cómo abstrae el prompting? ¿Qué modelo usa probablemente? ¿Cómo gestiona los tokens?
¿Hace routing entre modelos?

| Producto | Abstracción | Modelo | Tokens | Routing |
|---|---|---|---|---|
| GitHub Copilot | Prompt construido con el fichero, imports y comentarios | Pequeño para autocompletar, grande para el chat | Fichero actual y vecinos, no el repo | Sí |
| Soporte tipo Intercom / Zendesk AI | Políticas + datos del cliente + historial de tickets | Gama media | Prompt largo: el caching es clave | A veces |
| Análisis de documentos tipo NotebookLM | El usuario sube documentos y pregunta | Ventana de contexto grande | 50 páginas = 50.000+ tokens por pregunta | Sí → **RAG, Módulo 3** |

## Extra · Las tres interfaces lado a lado
""")

# =============================================================================
# Bloque 7 · Extra
# =============================================================================

code(r'''
# Extra · Misma pregunta en las tres interfaces
SYSTEM = "You are a concise technical advisor. Answer in at most 60 words."
QUESTION = "When should a startup move from a monolith to microservices?"

# 1 · Responses API (OpenAI directo)
r1 = openai_client.responses.create(model="gpt-4o-mini", instructions=SYSTEM, input=QUESTION)
print("1 · Responses API ·", r1.usage.input_tokens, "→", r1.usage.output_tokens, "tokens\n", r1.output_text, "\n")

# 2 · Messages API (Anthropic)
try:
    if anthropic_client is None:
        raise RuntimeError("No hay ANTHROPIC_API_KEY configurada.")
    r2 = anthropic_client.messages.create(model="claude-haiku-4-5-20251001", system=SYSTEM, max_tokens=200,
                                          messages=[{"role": "user", "content": QUESTION}])
    print("2 · Messages API ·", r2.usage.input_tokens, "→", r2.usage.output_tokens, "tokens\n", r2.content[0].text, "\n")
except Exception as e:
    print(f"2 · Messages API · ⚠️ {type(e).__name__}: {e}\n")

# 3 · LiteLLM (formato Chat Completions)
r3 = litellm.completion(model="openai/gpt-4o-mini",
                        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": QUESTION}])
print("3 · LiteLLM ·", r3.usage.prompt_tokens, "→", r3.usage.completion_tokens, "tokens\n",
      r3.choices[0].message.content)
''')

md(r"""
## Cierre

1. La calidad de un producto con IA la diseña quien desarrolla, no el usuario. El system prompt es vuestra
   herramienta principal.
2. No existe el mejor modelo: existe el mejor modelo para vuestro caso de uso, presupuesto y volumen.
3. Los tokens son la moneda de este mundo. Controlarlos es controlar vuestro margen.

**Próxima sesión (2):** nace el proyecto del máster, un estimador de proyectos con FastAPI, y la arquitectura CAG.
""")


def build() -> None:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    }
    nb.cells = [nbf.v4.new_markdown_cell(t) if kind == "md" else nbf.v4.new_code_cell(t) for kind, t in CELLS]
    nbf.write(nb, OUT)
    print(f"{OUT.name}: {sum(1 for k, _ in CELLS if k == 'code')} celdas de código, "
          f"{sum(1 for k, _ in CELLS if k == 'md')} de texto")


if __name__ == "__main__":
    build()
