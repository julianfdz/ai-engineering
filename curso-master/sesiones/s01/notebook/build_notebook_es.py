"""Genera la versión con los prompts en español del notebook de la Sesión 1.

Parte de las mismas celdas que build_notebook.py y solo traduce el texto que se lee: system prompts,
preguntas del usuario, mensajes que se imprimen y alguna frase del Markdown. El código, los nombres de
variables y los parámetros de las APIs se quedan igual, y los rótulos de las celdas («# 2.2 · …») también,
para que las diapositivas y el guion sigan apuntando a la misma celda.

Se mantiene en inglés a propósito la frase «Inglés» de la celda 6.1: ahí se comparan los tokens de un mismo
texto en inglés y en español.

    uv run python build_notebook_es.py
    # → sesion-01-version-julian_español.ipynb
"""

from __future__ import annotations

import nbformat as nbf

import build_notebook as base

OUT = base.HERE / "sesion-01-version-julian_español.ipynb"

# (texto original, traducción). Cada original tiene que aparecer al menos una vez: si alguien cambia
# build_notebook.py y una traducción deja de encajar, el script falla en vez de dejar inglés suelto.
TRADUCCIONES: list[tuple[str, str]] = [
    # --- Portada y configuración ------------------------------------------------------------------
    (
        "**Máster en AI Engineering · LIDR · Julián Fernández**",
        "**Máster en AI Engineering · LIDR · Julián Fernández**\n\n*Versión con los prompts en español.*",
    ),
    ('print("Clients configured successfully")', 'print("Clientes configurados correctamente")'),
    ('print("Cost calculation function loaded")', 'print("Función de cálculo de costes cargada")'),
    # --- Bloque 2 ---------------------------------------------------------------------------------
    (
        "\"We're migrating our payment service from a monolith to microservices. What should we consider?\"",
        '"Estamos migrando nuestro servicio de pagos de un monolito a microservicios. ¿Qué deberíamos tener en cuenta?"',
    ),
    (
        '"You are a senior software architect with experience in distributed systems."',
        '"Eres un arquitecto de software sénior con experiencia en sistemas distribuidos."',
    ),
    (
        """You are a senior software architect with 15+ years of experience building payment infrastructure.

Your audience: backend developers with 5+ years of experience who have never led a migration like this one.

Format: plain prose, no bullet lists, at most 250 words. Every paragraph must contain an actionable insight.""",
        """Eres un arquitecto de software sénior con más de 15 años de experiencia construyendo infraestructura de pagos.

Tu audiencia: desarrolladores backend con más de 5 años de experiencia que nunca han liderado una migración como esta.

Formato: prosa corrida, sin listas de viñetas, como máximo 250 palabras. Cada párrafo debe contener una idea accionable.""",
    ),
    (
        """Behaviour:
- When you mention a trade-off, state its concrete consequence (latency, cost, team effort or risk).
- If the question lacks context, state your assumptions explicitly before answering.
- Do not recommend specific vendors or commercial products.
- Mention at least one non-obvious risk.""",
        """Comportamiento:
- Cuando menciones un compromiso (trade-off), indica su consecuencia concreta (latencia, coste, esfuerzo del equipo o riesgo).
- Si a la pregunta le falta contexto, explicita tus supuestos antes de responder.
- No recomiendes proveedores ni productos comerciales concretos.
- Menciona al menos un riesgo que no sea obvio.""",
    ),
    (
        """You are a principal engineer who has led the migration of a PCI-DSS compliant payment platform
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
- Do not use filler phrases like "Great question!" or "It depends" without quantifying.""",
        """Eres un ingeniero principal que ha liderado la migración de una plataforma de pagos con certificación PCI-DSS,
que procesa más de 1.000 millones de dólares al año, de un monolito a microservicios.

Audiencia: desarrolladores backend con más de 5 años de experiencia que nunca han liderado una migración como esta.

Estructura de la respuesta (síguela al pie de la letra):
1. Empieza con la decisión más crítica que deben tomar primero, en una sola frase.
2. Después da 2-3 consideraciones. Para cada una: qué hacer, por qué y qué pasa si se equivocan.
3. Cierra con un riesgo que los equipos suelen pasar por alto.

Restricciones:
- Prosa corrida, como máximo 250 palabras.
- Si a la pregunta le falta contexto, indica tus supuestos en una frase.
- Cada compromiso (trade-off) debe incluir una consecuencia concreta.
- No recomiendes proveedores ni productos comerciales.
- No uses frases de relleno como «¡Buena pregunta!» ni «Depende» sin cuantificar.""",
    ),
    (
        "## 2.3 · Abstraer al usuario del prompting — naive vs production",
        "## 2.3 · Abstraer al usuario del prompting — versión ingenua frente a versión de producción",
    ),
    ('instructions="You are a code reviewer."', 'instructions="Eres un revisor de código."'),
    (
        """You are a senior backend engineer reviewing pull requests for a payments team.
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
- Never invent context that is not in the diff.""",
        """Eres un ingeniero backend sénior que revisa pull requests para un equipo de pagos.
El código de pagos maneja dinero real y datos personales, así que la corrección y la seguridad van primero.

Criterios de revisión, en estricto orden de prioridad:
1. Seguridad: inyección, secretos, tratamiento inseguro de datos personales o de tarjetas.
2. Exactitud con el dinero: redondeo, unidades (céntimos frente a euros), divisa, cobros duplicados, idempotencia.
3. Consistencia de los datos: qué pasa si un paso falla a mitad (transacciones, reintentos).
4. Legibilidad y tests, solo si los puntos anteriores están limpios.

Formato de salida (Markdown):
- Primera línea: un veredicto, exactamente uno de APROBAR, PEDIR CAMBIOS o BLOQUEAR.
- Después, una lista numerada de hallazgos, del más grave al menos grave. Cada hallazgo: gravedad (crítica/mayor/menor),
  la línea exacta, qué está mal y un fragmento corregido.
- Como máximo 5 hallazgos. No incluyas detalles de estilo si hay algún hallazgo crítico.

Comportamiento:
- Sé directo y concreto. Sin elogios ni relleno.
- Si no estás seguro de que algo sea un bug, di qué tendrías que comprobar.
- Nunca inventes contexto que no esté en el diff.""",
    ),
    ('service: str = "payments"', 'service: str = "pagos"'),
    (
        'f"Language: {language}\\nService: {service}\\n\\nDiff to review:\\n```diff\\n{diff}\\n```"',
        'f"Lenguaje: {language}\\nServicio: {service}\\n\\nDiff a revisar:\\n```diff\\n{diff}\\n```"',
    ),
    (
        '"""You are ...\n\nAudience: ...\n\nFormat: ...\n\nConstraints:\n- ..."""',
        '"""Eres ...\n\nAudiencia: ...\n\nFormato: ...\n\nRestricciones:\n- ..."""',
    ),
    ('instructions="Help the user."', 'instructions="Ayuda al usuario."'),
    (
        '"What is the main risk of migrating payments to microservices? Answer in one or two sentences."',
        '"¿Cuál es el principal riesgo de migrar los pagos a microservicios? Responde en una o dos frases."',
    ),
    (
        """Answer in exactly this format and nothing else:
Risk: <one noun phrase, at most 6 words>
Why: <one sentence, at most 20 words>""",
        """Responde exactamente con este formato y nada más:
Riesgo: <un sintagma nominal, como máximo 6 palabras>
Por qué: <una frase, como máximo 20 palabras>""",
    ),
    (
        '"What is the main risk of migrating payments to microservices?"',
        '"¿Cuál es el principal riesgo de migrar los pagos a microservicios?"',
    ),
    # --- Bloque 3 ---------------------------------------------------------------------------------
    (
        '"Suggest one name for a SaaS that estimates the cost of software projects. Reply with the name only."',
        '"Sugiere un nombre para un SaaS que estima el coste de proyectos de software. Responde solo con el nombre."',
    ),
    (
        '"List the 6 phases of a software project, numbered 1. to 6."',
        '"Enumera las 6 fases de un proyecto de software, numeradas del 1. al 6."',
    ),
    (
        '"Invent a two-sentence story about a database."',
        '"Inventa una historia de dos frases sobre una base de datos."',
    ),
    (
        '"What were the most important announcements at OpenAI DevDay 2025? Three bullet points."',
        '"¿Cuáles fueron los anuncios más importantes del OpenAI DevDay 2025? Tres viñetas."',
    ),
    # --- Bloque 4 ---------------------------------------------------------------------------------
    (
        """You are a staff data engineer advising a SaaS team.

Answer in this structure:
1. Recommendation (one sentence).
2. Why, with numbers: query latency, storage and operational cost.
3. When the other option would be better.

Constraints: at most 200 words. Do not answer "it depends" without quantifying. No vendor marketing.""",
        """Eres un ingeniero de datos de nivel staff que asesora a un equipo de SaaS.

Responde con esta estructura:
1. Recomendación (una frase).
2. Por qué, con números: latencia de las consultas, almacenamiento y coste operativo.
3. Cuándo sería mejor la otra opción.

Restricciones: como máximo 200 palabras. No respondas «depende» sin cuantificar. Nada de marketing de proveedores.""",
    ),
    (
        """Our SaaS runs on PostgreSQL 16. The events table has 50M rows and grows 2M rows per month.
The analytics dashboard (aggregations by customer and by month) now takes 8-12 seconds to load.
Should we add a columnar store (e.g. ClickHouse) or stay on Postgres with read replicas and better indexes?""",
        """Nuestro SaaS funciona sobre PostgreSQL 16. La tabla de eventos tiene 50 millones de filas y crece 2 millones al mes.
El panel de analítica (agregaciones por cliente y por mes) tarda ahora entre 8 y 12 segundos en cargar.
¿Añadimos un almacén columnar (por ejemplo, ClickHouse) o nos quedamos en Postgres con réplicas de lectura y mejores índices?""",
    ),
    ("¿Alguna dice «it depends» sin cuantificar?", "¿Alguna dice «depende» sin cuantificar?"),
    # --- Bloque 5 ---------------------------------------------------------------------------------
    (
        '"You are a pragmatic backend engineering lead. Answer in at most 150 words, with a clear recommendation."',
        '"Eres un líder de ingeniería backend pragmático. Responde en 150 palabras como máximo, con una recomendación clara."',
    ),
    (
        '("We receive 500 Stripe webhooks per second in our Rails API. Should we process them synchronously "\n'
        '                     "in the request, or push them to a queue and process them in background workers?")',
        '("Recibimos 500 webhooks de Stripe por segundo en nuestra API de Rails. ¿Los procesamos de forma síncrona "\n'
        '                     "dentro de la petición, o los metemos en una cola y los procesan workers en segundo plano?")',
    ),
    (
        """You are a principal engineer. Evaluate the technical decision you receive.
Reply with: Verdict (GO / NO-GO / NEEDS DATA), then the two strongest reasons, then one thing to measure first.
At most 120 words.""",
        """Eres un ingeniero principal. Evalúa la decisión técnica que recibes.
Responde con: Veredicto (ADELANTE / NO SEGUIR / FALTAN DATOS), después las dos razones de más peso y después una cosa que medir primero.
Como máximo 120 palabras.""",
    ),
    (
        '"Move our 3 GB Postgres database to a managed serverless database to save on ops work."',
        '"Pasar nuestra base de datos Postgres de 3 GB a una base de datos serverless gestionada para ahorrar trabajo de operaciones."',
    ),
    # --- Bloque 6 ---------------------------------------------------------------------------------
    # 6.2 acorta o alarga el prompt de producción reescribiendo su límite de palabras
    (
        '.replace("at most 250 words", f"about {palabras} words")',
        '.replace("como máximo 250 palabras", f"unas {palabras} palabras")',
    ),
    ("# 6.3 · Incident response en 5 turnos", "# 6.3 · Respuesta a un incidente en 5 turnos"),
    (
        '"You are an SRE helping during a production incident. Be concise: at most 120 words per answer."',
        '"Eres un SRE que ayuda durante un incidente en producción. Sé conciso: como máximo 120 palabras por respuesta."',
    ),
    (
        '"p99 latency of our checkout API jumped from 200 ms to 3 s ten minutes ago. Where do we start?"',
        '"La latencia p99 de nuestra API de checkout ha pasado de 200 ms a 3 s hace diez minutos. ¿Por dónde empezamos?"',
    ),
    (
        '"CPU is normal, but the database connection pool is at 100% usage."',
        '"La CPU está normal, pero el pool de conexiones de la base de datos está al 100 % de uso."',
    ),
    (
        "\"We deployed a new version 15 minutes ago that adds a query to load the customer's loyalty points.\"",
        '"Hace 15 minutos desplegamos una versión nueva que añade una consulta para cargar los puntos de fidelización del cliente."',
    ),
    (
        '"The new query has no index on customer_id and the table has 40M rows. Rollback or hotfix?"',
        '"La consulta nueva no tiene índice en customer_id y la tabla tiene 40 millones de filas. ¿Rollback o hotfix?"',
    ),
    (
        '"We rolled back and latency is recovering. What should go in the postmortem?"',
        '"Hemos hecho rollback y la latencia se está recuperando. ¿Qué debería ir en el postmortem?"',
    ),
    # --- Extra ------------------------------------------------------------------------------------
    (
        '"You are a concise technical advisor. Answer in at most 60 words."',
        '"Eres un asesor técnico conciso. Responde en 60 palabras como máximo."',
    ),
    (
        '"When should a startup move from a monolith to microservices?"',
        '"¿Cuándo debería una startup pasar de un monolito a microservicios?"',
    ),
]


def traducir(texto: str, usados: set[int]) -> str:
    for i, (original, traduccion) in enumerate(TRADUCCIONES):
        if original in texto:
            texto = texto.replace(original, traduccion)
            usados.add(i)
    return texto


def build() -> None:
    usados: set[int] = set()
    celdas = [(kind, traducir(t, usados)) for kind, t in base.CELLS]

    sin_usar = [TRADUCCIONES[i][0][:70] for i in range(len(TRADUCCIONES)) if i not in usados]
    if sin_usar:
        raise SystemExit("Traducciones que ya no encajan en build_notebook.py:\n- " + "\n- ".join(sin_usar))

    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    }
    nb.cells = [nbf.v4.new_markdown_cell(t) if kind == "md" else nbf.v4.new_code_cell(t) for kind, t in celdas]
    nbf.write(nb, OUT)
    print(f"{OUT.name}: {len(TRADUCCIONES)} traducciones aplicadas, "
          f"{sum(1 for k, _ in celdas if k == 'code')} celdas de código, {sum(1 for k, _ in celdas if k == 'md')} de texto")


if __name__ == "__main__":
    build()
