# Sesión 12 — Introducción a agentes de IA · Guion

## 1. ¿Qué es un agente de IA?

### La definición en una frase

Un agente es un LLM metido en un bucle, con **herramientas** que puede invocar
y un **objetivo** — donde es el propio modelo, y no tu código, quien decide en
cada paso qué hacer a continuación.

La frase que separa las aguas y sobre la que pivota toda la sesión:

> **En un pipeline, el control de flujo vive en el código.
> En un agente, el control de flujo vive en el modelo.**

Todo lo que hemos construido hasta hoy (S4–S11) es lo primero. Hoy cruzamos.

### El bucle (razonar → actuar → observar)

1. **Razonar**: el modelo mira el objetivo y lo que sabe hasta ahora, y decide
   la siguiente acción.
2. **Actuar**: emite una llamada a una herramienta con sus argumentos
   (`search_budgets({"query": "integración SAP"})`).
3. **Observar**: tu código ejecuta la herramienta y le devuelve el resultado.
   Con esa observación, vuelta al paso 1.

El bucle termina cuando el modelo decide que ya tiene lo que necesita (un
turno sin llamada a herramienta) — con una red de seguridad de código:
`max_iterations`, porque a un modelo no se le deja decidir *indefinidamente*.

### Aplicado a NUESTRO proyecto

Llevamos tres sesiones estimando desde una transcripción con un **pipeline
fijo** (S9–S11): `reformular → recuperar → generar`. Siempre los mismos pasos,
en el mismo orden, decididos por código. Funciona muy bien... mientras la
transcripción sea *un* proyecto.

¿Y si la reunión mezcla tres encargos que no tienen nada que ver — un backend
de negocio, una integración con ERP y una app móvil? Una única búsqueda en los
presupuestos históricos mezcla los tres temas y recupera ruido. Lo que
querrías es: busca precedentes del backend, *luego* busca los del ERP, *luego*
los de la app, y ajusta cada búsqueda según lo que encontró la anterior.
¿Cuántas búsquedas? ¿En qué orden? **Depende de la transcripción** — y eso es
exactamente lo que un pipeline no puede decidir y un agente sí.

Nuestro agente (`app/generation/agentic/`):

- **El bucle**: `agent_loop.py::run_estimation_agent` — escrito A MANO sobre
  la Responses API de OpenAI, sin framework. Es deliberado: el objetivo de la
  sesión es *ver* el bucle, no esconderlo tras una librería.
- **Las tres herramientas** (`agent_tools.py`):
  - `search_budgets` — busca en los presupuestos históricos (envuelve el
    `retrieve()` real de la S10).
  - `derive_task_hours` — deriva las horas por consenso de los vecinos.
  - `validate_estimate` — comprueba la coherencia del resultado.
- **Detalles del oficio** que se ven en el código: los errores de una
  herramienta se le devuelven al modelo como texto (para que se autocorrija en
  el siguiente turno, en vez de tumbar el bucle), el estado se encadena con
  `previous_response_id` (el servidor recuerda el razonamiento), y
  `max_iterations=10` acota el peor caso.
- **Ejecutarlo**: `scripts/run_agent_s12.py` — imprime la traza `STEP N`
  (razonamiento → tool → resultado), que es la radiografía del bucle. La traza
  de ejemplo committeada: `exercises/session-12/example_trace_complex.txt`.

Señalar en la traza: el agente hace *distinto número de búsquedas según la
transcripción*. Con la simple, 1–2; con la compleja, una por componente. Nadie
programó eso — es la decisión del modelo. Eso ES ser un agente.

### Dos ejemplos de fuera, para ver que el patrón es el mismo

**1. Un agente de programación (Claude Code, Cursor...).** Objetivo: "arregla
este test que falla". Herramientas: leer fichero, editar fichero, ejecutar
tests, buscar en el código. El bucle en acción: ejecuta los tests → observa el
error → abre el fichero implicado → edita → re-ejecuta → sigue fallando →
lee otro fichero → edita → re-ejecuta → verde → para. Nadie escribió ese
orden: con otro bug, la secuencia habría sido otra. Fijaos en que es
literalmente nuestro bucle con otras herramientas — y en el mismo detalle de
oficio que nuestro `agent_loop.py`: el error del test se le devuelve al modelo
como observación, y de ahí sale la corrección.

**2. Un agente de soporte al cliente.** Objetivo: "resuelve este ticket".
Herramientas: consultar pedido, consultar política de devoluciones, emitir
reembolso, escalar a un humano. Llega "mi pedido no llegó y quiero mi dinero":
el agente consulta el pedido (¿consta entregado?), según eso consulta la
política (¿dentro de plazo?), y decide entre reembolsar o escalar. Otro ticket
distinto activa otras herramientas en otro orden. Aquí se ve además la cara de
**seguridad**: a este agente le das `emitir_reembolso` con un límite de
importe, y `escalar_a_humano` existe precisamente porque el agente debe saber
cuándo NO decidir él — la versión con dientes de nuestro `max_iterations`.

### Y la contra-lección (para cerrar la sección)

Un agente no es "mejor" que un pipeline: es **más caro, más lento y menos
predecible** (cada decisión es una llamada al LLM, y dos ejecuciones pueden no
hacer lo mismo). La regla del oficio:

> Si conoces el flujo de antemano → pipeline (determinista, barato, depurable).
> Si el flujo depende de la entrada → agente.

Por eso el proyecto CONSERVA el pipeline S9–S11 como camino por defecto y el
agente es un camino adicional para el caso que lo justifica. Esta tensión
reaparece en la S13 (grafos: flujo fijo otra vez, pero explícito) y estalla en
la S14 (¿cuánto control le cedes al modelo? — supervisor).

---

## 2. [PENDIENTE] La Responses API y el bucle a mano

## 3. [PENDIENTE] Las herramientas: esquemas estrictos y dispatch

## 4. [PENDIENTE] Demo en vivo con la transcripción compleja

## 5. [PENDIENTE] Ejercicio de los alumnos
