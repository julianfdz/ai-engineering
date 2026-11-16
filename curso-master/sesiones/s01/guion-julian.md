# Línea de formación · Sesión 1 · LLMs y setup de entorno de trabajo

> Diapo a diapo: **qué contar**, **qué celda ejecutar** y **qué preguntar**. Todo pasa en un notebook:
> `notebook/sesion-01-version-julian.ipynb`. Cada celda de código empieza con un rótulo (`# 2.2 · Iteración 4 …`), que es
> lo mismo que pone la franja «En el código» de cada diapo. Para saltar a una celda en Jupyter, Ctrl+F con el rótulo.
>
> Primera sesión de un grupo nuevo (edición 11): mucha pregunta al grupo y poca prisa en el Bloque 1.

---

## Antes de empezar (15 min antes)

**PowerShell (comandos):**

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-main\curso-master\sesiones\s01\notebook"
```

```powershell
uv run jupyter lab sesion-01-version-julian.ipynb
```

Se abre en el navegador (<http://localhost:8888>). Ejecuta las tres celdas de **Configuración inicial** y comprueba
que dicen `OpenAI: OK` y `Anthropic: OK`.

- Si Anthropic dice «falta ANTHROPIC_API_KEY», pega la clave en `notebook\.env`, línea `ANTHROPIC_API_KEY=sk-ant-…`,
  y en Jupyter **Kernel → Restart Kernel** (el `.env` se lee al arrancar).
- Respaldo: `sesion-01-version-julian-ejecutado.ipynb` tiene todas las salidas de la prueba del 16/11. Si una celda falla
  en directo, se enseña esa.
- Los alumnos trabajan con **su copia en Colab** del notebook de LIDR. El nuestro sigue la misma estructura y además
  funciona en Colab (lee los Secrets 🔑).

**Pestañas:** el notebook, las diapos (`Sesion01-Julian-Fernandez.pdf`) y, para el Bloque 4, la página de precios
de OpenAI (<https://developers.openai.com/api/docs/pricing>).

Coste de ejecutar el notebook entero: **unos 0,07 $**, casi todo de la búsqueda web.

---

## Bloque 1 · Setup y puesta en común · 10 min

### Diapo 2 · Hoy

- 💬 «Hoy no hay proyecto todavía: hay una llamada a un LLM y la vamos a mirar como producto». Nace en la S2.
- 💬 La frase que atraviesa la sesión: **el usuario no hace prompting**.

### Diapo 3 · Tres celdas antes de empezar

- ▶️ `# Config 1 · Dependencias` → cuatro ✅ con las versiones.
- ▶️ `# Config 2 · Claves y clientes` → «Clients configured successfully». Enseña `leer_clave()`: en Colab lee los
  Secrets y en local el `.env`. Nunca una clave escrita en el código.
- ▶️ `# Config 3 · Función de costes` → «Cost calculation function loaded». `PRICES` son dólares por **millón** de
  tokens, entrada y salida por separado. Comprobados el 16/11.
- 🙋 Preguntas: «¿A alguien no le funcionó el ejercicio previo?», «¿Quién usó OpenAI, quién Anthropic, quién los
  dos?», «¿Quién llegó a ver los tokens y el coste?».
- ⚠️ Errores típicos: Secrets sin permiso de acceso para el notebook · `RateLimitError` que habla de crédito (cuenta sin
  saldo) · claves cruzadas (`sk-` frente a `sk-ant-`) · avisos de gradio/typer en Colab (ya filtrados).
- ⏱️ Si pasa de 12 min, los problemas individuales se dejan para el final.

---

## Bloque 2 · Del prompt del usuario al prompt del producto · 25 min

### Diapo 4 · La respuesta genérica

- ▶️ `# 2.1 · Sin system prompt`. Sale una respuesta de **521 palabras en 15 apartados**.
- 🙋 «¿Pondríais esto en un producto?» · «¿Se lo daríais a un cliente que paga?» · «Si la calidad depende de que el
  usuario escriba un buen prompt, ¿cuántos usuarios tendrán buenas respuestas?».
- 💬 La calidad homogénea es responsabilidad del desarrollador.

### Diapo 5 · El system prompt como contrato de calidad

- ▶️ `# 2.2 · La pregunta del usuario (no cambia)`: enseña `preguntar()`. `instructions` es el system prompt e
  `input` lo que escribe el usuario.
- ▶️ Las cuatro iteraciones, una a una. Tras cada una: **«¿Qué ha cambiado? ¿Por qué?»**.

| Iteración | Palabras (prueba del 16/11) | Qué comentar |
|---|---|---|
| 1 · Rol | 548 | Más técnica… y más larga. El rol solo no basta |
| 2 · + audiencia + formato | 241 | El salto grande: prosa, 250 palabras |
| 3 · + comportamiento | 227 | Declara supuestos («Assuming…») y da consecuencias concretas |
| 4 · Contrato de producción | 194 | Abre con la decisión crítica y cierra con el riesgo olvidado |

- 💬 Cada línea es una **decisión de producto**: el equivalente a las reglas de negocio de una web.

### Diapo 6 · Abstraer al usuario del prompting

- ▶️ `# 2.3 · El diff que revisamos`: 6 líneas de código de pagos con fallos (inyección SQL, IVA sin redondear,
  euros en lugar de céntimos en Stripe, UPDATE de todos los pedidos del cliente).
- ▶️ `# 2.3 · review_pull_request_naive()`: 818 tokens, sin veredicto, mezcla lo grave con docstrings.
- ▶️ `# 2.3 · review_pull_request()`: primera línea `BLOCK` y hallazgos por gravedad.
- 🙋 «Si fuerais el autor del PR, ¿cuál preferiríais?» · «El usuario escribió 6 líneas; el modelo recibió 172 palabras
  de system prompt más el input formateado. El usuario no ve nada de eso».
- 💬 Este patrón (el producto construye el prompt; el usuario aporta datos) es la base del CAG de la S2.
- ⏱️ La celda «Tu turno» es opcional. Si el bloque pasa de 28 min, se salta.

### Diapo 7 · Consistencia

- ▶️ `# 2.4 · temperature 1.0 + prompt vago`: cuatro respuestas con enfoques distintos.
- ▶️ `# 2.4 · temperature 0.1 + prompt preciso`: en la prueba salieron **las cuatro idénticas**.
- 🙋 «¿Es aceptable que dos usuarios reciban respuestas de calidad diferente a la misma pregunta?».
- 💬 Puente al Bloque 3: las palancas son temperature, max_output_tokens y structured outputs (S4).

---

## Bloque 3 · Parámetros y herramientas integradas · 20 min

### Diapo 8 · Parámetros esenciales

- ▶️ `# 3.1 · Misma pregunta, tres temperaturas`. Ni con 0.0 sale idéntico (CostCalc Pro, CostWise, CostWise).
- 💬 `top_p` es la alternativa: uno u otro, nunca los dos. En Claude 4.5 y posteriores la API lo rechaza.
- ▶️ `# 3.2 · Tres techos de salida`: con 50 y 200 sale `incomplete`; con 800, `completed` con 253 tokens.
  **Es un techo, no un control de longitud**. En Anthropic es obligatorio.
- ▶️ `# 3.3 · stop` y `# 3.3 · seed`. Van por **Chat Completions** (la otra API de OpenAI, que reaparece en el
  Bloque 5). En la prueba, con `seed=42` las tres respuestas salieron **distintas**: reproducibilidad *best effort*.
- ⏱️ Si vas justo, la de seed se comenta sin ejecutar.

### Diapo 9 · Puntos de partida por tipo de tarea

- 📄 Markdown 3.4. Tabla de valores de partida.
- 🙋 «¿Qué temperature para extraer datos de facturas? ¿Y para brainstorming?».
- 💬 Los modelos de razonamiento se controlan con `reasoning.effort`. Matiz que comprobé: `gpt-5.4` **sí acepta**
  `temperature` cuando no activas el razonamiento.

### Diapo 10 · Herramientas integradas

- 📄 Markdown 3.5 (sin código): el modelo no sabe nada reciente ni privado y no ejecuta código. Las herramientas las
  ejecuta el proveedor y todo pasa en una llamada.
- ▶️ `# 3.6 · web_search (OpenAI)`, con gpt-4o (no todos los modelos la soportan). Pasos: `web_search_call` →
  `message`. **Lo ejecuta solo el profe**, para no gastar crédito de los alumnos.
- ▶️ `# 3.6 · Las fuentes, en las annotations` → los enlaces a las páginas que leyó. 💬 Enseñar las fuentes no es opcional.
- 💬 El dato que impacta: esa llamada son **17.509 tokens de entrada y 0,048 $**, unas 360 veces una llamada normal.
  Lo que lee de la web se cobra como entrada.
- ▶️ `# 3.7 · web_search (Anthropic)`. Si falla, el `try/except` lo explica. Tres diferencias: herramienta versionada
  (`web_search_20250305`), hay que habilitarla en la Console, y `max_uses`.

### Diapo 11 · Lo que los proveedores venden y nosotros construiremos

- 📄 Markdown 3.8, sin ejecutar. `file_search` → «exactamente lo que construiremos en el Módulo 3». MCP → Módulo 5.
- ⏱️ Si el bloque pasa de 23 min, esta diapo va en 30 segundos.

---

## Bloque 4 · Comparativa de proveedores · 20 min

### Diapo 12 · Misma pregunta, distinto proveedor y distinto tier

- ▶️ `# 4.1 · El escenario…`: PostgreSQL 16, 50M filas, +2M al mes, dashboard de 8-12 s.
- ▶️ `# 4.1 · OpenAI (Responses API)` y `# 4.1 · Anthropic (Messages API)`. Señala las diferencias: en Anthropic el
  `system` va aparte y `max_tokens` es obligatorio.
- ▶️ `# 4.1 · Lado a lado`.
- 🙋 «¿Cuál es más útil? ¿Cuál respeta el formato? ¿Alguna dice "it depends" sin cuantificar?» · «¿Por qué Anthropic
  cuenta más tokens de entrada?» → cada proveedor tiene su tokenizador.
- ▶️ `# 4.2 · Tiers de OpenAI` (unos 17 s en total):

| Modelo | Tiempo | Coste | Qué aporta |
|---|---|---|---|
| gpt-4o-mini | 3,2 s | 0,00013 $ | Postgres con réplicas; cifras vagas («$500/month») |
| gpt-5.4-mini | 3,8 s | 0,00149 $ | Tabla resumen: de 8-12 s a 50-300 ms |
| gpt-5.4 | 10,0 s | 0,0051 $ | Particiones, réplicas y un umbral claro (200-500M filas) |

- 🙋 «¿Justifica 38 veces más coste la diferencia, para **esta** pregunta?» «¿Para qué tareas sí se notaría?».

### Diapo 13 · No existe «el mejor modelo»

- ▶️ `# 4.2 · ¿Cuánto más caro es cada tier?`: gpt-5.4 es **23×** gpt-4o-mini (la guía de LIDR dice 16×; los precios
  han cambiado).
- 🙋 Tres escenarios: chatbot de FAQs · contratos de 50 páginas · 10.000 usuarios con el mismo modelo o no.
- 💬 Routing / cascada: modelo barato para el 80 %, premium cuando haga falta. Lo construimos en la S3.

---

## Bloque 5 · Agregadores · 12 min

### Diapo 14 · LiteLLM

- 💬 Sin diapo previa: un solo proveedor es un riesgo (caídas, precios, rate limits) y cada SDK es distinto.
- ▶️ `# 5.2 · El mismo código para los dos proveedores`. Lo único que cambia es el string del modelo.
- 💬 Tres diferencias con el Bloque 4: `messages` en vez de `instructions` + `input`, `choices[0].message.content`
  en vez de `output_text`, `prompt_tokens` en vez de `input_tokens`. LiteLLM habla **Chat Completions**.
- ▶️ `# 5.3 · evaluate_technical_decision()`. Descomenta la línea de Anthropic y vuelve a ejecutar: el mismo
  código con otro proveedor.
- 💬 «En la Sesión 3 esto es la capa de proveedores con fallback: si OpenAI se cae, pasa a Anthropic sin que el
  usuario lo note».

---

## Bloque 6 · Tokens · 20 min

### Diapo 15 · Los tokens no son palabras

- ▶️ `# 6.1 · Mismo contenido, distintos formatos`. Columnas `o200k` (tokenizador de hoy) y `cl100k` (el de 2023).
- 💬 **Aquí corrijo la guía**: dice que el español gasta un 30 % más que el inglés. Eso era con el tokenizador
  antiguo; en la prueba, **+33 % con cl100k frente a +3 % con o200k**. La lección no cambia:
  **se mide con el tokenizador de tu modelo**.
- 💬 El JSON sale caro, y el `PRODUCTION_SYSTEM_PROMPT` son 185 tokens que se pagan **en cada turno**.
- ▶️ `# 6.1 · Token a token`: «¿Cu | ánto | cuesta | migr | ar…», 15 tokens. Los acentos y las palabras raras se
  parten.
- 🙋 `# 6.1 · Tu turno`: que tokenicen su system prompt del Bloque 2.

### Diapo 16 · Entrada frente a salida

- ▶️ `# 6.2 · Misma pregunta, tres longitudes`: la salida pasa del 75 % al 91 % del coste.
- ▶️ `# 6.2 · Proyección a escala`: 1,5 M llamadas al mes. gpt-4o-mini **263 $** frente a gpt-5.4 **6.176 $**.
- 🙋 «¿Cuál es la diferencia mensual entre gpt-4o-mini y gpt-5.4?» → 23,5×.
- 💬 Acortar respuestas mueve más la factura que recortar el prompt.

### Diapo 17 · El coste oculto de las conversaciones

- ▶️ `# 6.3 · Incident response en 5 turnos`. La entrada pasa de 58 a 754 tokens: cada turno reenvía todo el historial.
- 💬 La guía dice que el turno 5 cuesta más que los cuatro anteriores juntos. En nuestra prueba **no** (0,00023 $
  frente a 0,00054 $). Lo honesto: crece rápido, y con conversaciones de 20-50 turnos sí se dispara.
- ▶️ `# 6.3 · El system prompt se paga en cada turno`: 20 turnos son 3.700 tokens solo de system prompt.
- 💬 Mitigaciones, como anticipo: truncar, resumir, prompt caching (Anthropic cobra los aciertos al 10 %),
  `previous_response_id`. La memoria comprimida de verdad llega en la S5.
- ⏱️ Si el bloque pasa de 23 min, las mitigaciones se nombran y ya.

---

## Bloque 7 · Arquitecturas reales y cierre · 13 min (protegido: nunca menos de 10)

### Diapo 18 · Arquitecturas reales

- 💬 Cuatro preguntas por producto: ¿cómo abstrae el prompting? ¿Qué modelo usa? ¿Cómo gestiona los tokens?
  ¿Hace routing?
- Copilot (fichero + imports; modelo pequeño inline y grande en el chat) · soporte tipo Intercom (políticas largas →
  caching) · NotebookLM (50 páginas = 50.000 tokens por pregunta → «esto es RAG, Módulo 3»).
- ▶️ `# Extra · Misma pregunta en las tres interfaces`: Responses API, Messages API y LiteLLM.

### Diapo 19 · Lo que os lleváis hoy

- 💬 Las tres frases de cierre (en la diapo).
- 💬 Mapa del máster: S2 nace el proyecto (FastAPI + CAG) · S3-5 producto CAG completo · S6-11 RAG · S12-14
  agentes · S15-16 producción.
- 💬 Indicaciones: material asíncrono de la S2 y el notebook se queda en su Drive.
- Encuesta ROTI: se abre 15 minutos antes del final.

---

## Si algo falla en directo

| Síntoma | Qué hacer |
|---|---|
| Una celda de OpenAI tarda o da error | Enseñar la salida en `sesion-01-version-julian-ejecutado.ipynb` |
| `AuthenticationError` de Anthropic | Clave sin saldo o mal pegada: seguir con OpenAI y comentar la celda de respaldo |
| 3.7 dice que web search no está habilitado | Es parte de la lección: es una decisión de gobernanza del admin |
| `RateLimitError` | Esperar 20 s; en el 4.2, quitar `gpt-5.4` de `openai_models` |
| Jupyter no arranca | `uv sync` en la carpeta `notebook` y otra vez `uv run jupyter lab` |
