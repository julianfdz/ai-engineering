# Sesión 1 — LLMs y setup de entorno de trabajo (contexto)

> Material de Julián para la clase del 17/11/2026: primera sesión de la **edición 11**, con un grupo nuevo.
> Fuente: el Notion de LIDR (edición 2026-09, donde la dio Juanjo Expósito) en
> `LIDR\edicion-26-09\s01-llms-y-setup-de-entorno-de-trabajo\sesion-notion.md`.

## 1. De qué va

Es la puerta de entrada del máster. Todavía no hay proyecto ni repositorio: la sesión es **un notebook**. Se hace
la llamada más básica a un LLM y se mira desde el punto de vista de producto: quién diseña la calidad, qué decide
cada parámetro, cómo cambia todo de un proveedor a otro y cuánto cuesta.

| Bloque | Qué | Minutos |
|---|---|---|
| 1 | Setup: las tres celdas de configuración en verde, puesta en común del ejercicio previo | 10 |
| 2 | Del prompt del usuario al prompt del producto: 4 iteraciones, revisor de PR naive/producción, consistencia | 25 |
| 3 | Parámetros (temperature, max_output_tokens, stop, seed) y herramientas integradas (web_search) | 20 |
| 4 | Comparativa en vivo: OpenAI frente a Anthropic y tiers de modelo; criterios de selección | 20 |
| 5 | Agregadores: LiteLLM, cambiar de proveedor en una línea | 12 |
| 6 | Tokens: tokenización, asimetría entrada/salida, coste de las conversaciones | 20 |
| 7 | Productos reales, las tres interfaces lado a lado y mapa del máster | 13 |

**Propósito en cuatro líneas:**

1. Que el grupo salga sabiendo llamar a OpenAI y a Anthropic por API, y leer la respuesta: texto, tokens y coste.
2. Cambiar el chip: en un producto, el usuario no hace prompting. El system prompt es la herramienta de quien desarrolla.
3. Dar criterio para elegir modelo y proveedor (calidad, coste y latencia) y para no atarse a uno (agregadores).
4. Que los tokens se vean como dinero, porque es la base de todo lo que se optimiza en las sesiones 2-5.

**Después:** la S2 crea el proyecto del máster (estimador de proyectos con FastAPI) y la arquitectura CAG. La S3
convierte lo del Bloque 5 en la capa de proveedores con fallback, y la S5 retoma el coste multi-turno con la
memoria comprimida.

## 2. Ejercicio previo

Conectar con un LLM por API: enviar una pregunta y recibir la respuesta, en Colab o con un script local. La guía
habla de niveles: «¿Alguien llegó al L3 y vio los tokens y el coste?».

En la puesta en común conviene preguntar quién usó OpenAI, quién Anthropic y quién los dos, y detectar quién tiene
experiencia previa con APIs de LLMs.

## 3. En local

- Notebook: `curso-master/sesiones/s01/notebook/sesion-01-en-vivo.ipynb`. Lo genera `build_notebook.py` y sigue
  los siete bloques de la guía. Cada celda de código empieza con un rótulo (`# 2.2 · Iteración 4 …`), que es lo
  que citan las diapositivas.
- **Sin Docker**: la S1 no tiene código del proyecto. Entorno `uv` en la misma carpeta (`.venv` de 410 MB, ya
  instalado) con openai 3.51, anthropic 2.8, tiktoken 0.14 y litellm 1.109.
- Claves en `notebook/.env` (no se sube; plantilla en `.env.example`). Hoy solo tiene la de OpenAI.
- El mismo notebook funciona en **Colab**: allí lee las claves de Secrets (🔑) e instala las dependencias solo.
- Ejecución completa guardada en `sesion-01-en-vivo-ejecutado.ipynb`, como respaldo si algo falla en directo.

## 4. Diferencias con la guía de LIDR

- **No tenemos el notebook oficial** (`sesion-01-notebook-sesion-en-vivo.ipynb`): no está en el repo ni en Drive.
  El nuestro reproduce bloque a bloque lo que describe la guía, con los mismos nombres (`USER_QUESTION`,
  `PRODUCTION_SYSTEM_PROMPT`, `review_pull_request_naive()`, `review_pull_request()`, `COMPARISON_SYSTEM_PROMPT`,
  `openai_models`, `evaluate_technical_decision()`). Si los alumnos reciben el de LIDR, la estructura coincide.
- **Español frente a inglés**: la guía dice «~30 % más tokens en español». Con el tokenizador actual de OpenAI
  (`o200k_base`) la diferencia casi desaparece: +3 %, frente a +33 % con el de 2023. La celda 6.1 compara con el de 2023 (`cl100k_base`) para que se
  vea de dónde viene la cifra.
- **«El turno 5 cuesta más que los 4 anteriores juntos»**: no se cumple en nuestra ejecución (0,00023 $ frente a
  0,00054 $). Lo que sí se ve es que el turno 5 envía 13 veces más tokens de entrada que el turno 1.
- **gpt-5.4 frente a gpt-4o-mini**: la guía dice «≈16×» en el 4.2 y «15-20×» en el 6.2. Con los precios del
  16/11/2026 son **23×** (2,50/15 $ frente a 0,15/0,60 $ por millón).
- **gpt-5.4 acepta `temperature`** cuando no se activa el razonamiento. Lo dejo dicho porque la guía da a entender
  que los modelos de razonamiento no aceptan esos parámetros.
- **El ID `claude-sonnet-4-6-20250514` de la guía no existe**: usamos `claude-sonnet-4-6`.
- **`seed` no garantiza nada**: con `seed=42` y temperature 1.0, las tres respuestas salieron distintas con el
  mismo `system_fingerprint`. Es un buen ejemplo de «best effort».

## 5. Pendiente antes de clase (Julián)

- **Clave de Anthropic con saldo**: no hay ninguna configurada. Sin ella, las celdas 3.7, 4.1 (Anthropic), 4.2
  (Tu turno), 5.2 (segundo modelo) y el Extra muestran un aviso controlado en vez de la respuesta. Pegarla en
  `notebook/.env` (`ANTHROPIC_API_KEY=sk-ant-…`).
- **Web search habilitado en la Claude Console** de esa organización, para la demo 3.7.
- Las diapositivas de Google de LIDR (enlace en el Notion) no se pueden abrir desde esta cuenta. Nuestro deck es
  `Sesion01-Julian-Fernandez.pdf`.

## 6. Resultados verificados (16/11/2026, la ejecución guardada en `sesion-01-en-vivo-ejecutado.ipynb`)

| Demo | Resultado |
|---|---|
| 2.1 sin system prompt | 521 palabras en 15 apartados con títulos |
| 2.2 iteraciones 1 → 4 | 548 → 241 → 227 → 194 palabras; la 4 abre con la decisión crítica y cierra con el riesgo |
| 2.3 revisor naive | 818 tokens, sin veredicto; mezcla la inyección SQL con docstrings |
| 2.3 revisor de producción | `BLOCK` y 5 hallazgos por gravedad (inyección SQL critical, redondeo, céntimos de Stripe…) |
| 2.4 consistencia | temperature 0.1 + formato exacto: 4 respuestas idénticas |
| 3.1 temperature | 0.0: CostCalc Pro, CostWise, CostWise · 1.5: CostCrafters, CostOrchard, CostPioneer |
| 3.2 max_output_tokens | 50 y 200 → `incomplete`; 800 → `completed` con 253 tokens |
| 3.6 web_search (gpt-4o) | Apps SDK, AgentKit y GPT-5 Pro; 17.509 tokens de entrada, 0,048 $ |
| 4.2 tiers | gpt-4o-mini 3,2 s / 0,00013 $ · gpt-5.4-mini 3,8 s / 0,00149 $ · gpt-5.4 10,0 s / 0,0051 $ |
| 6.1 tokens | español frente a inglés: +3 % con o200k, +33 % con cl100k |
| 6.2 proyección (1,5 M llamadas/mes) | gpt-4o-mini 263 $ · gpt-5.4 6.176 $ (23,5×) · claude-sonnet-4-6 6.336 $ |
| 6.3 multi-turno | entrada 58 → 754 tokens en 5 turnos; 0,00077 $ acumulado |
| Notebook entero | 3 min 20 s y unos 0,07 $ (casi todo es la búsqueda web) |

## 7. Dudas que se repitieron en la edición anterior

Del resumen de la S1 de la edición 2026-09:

- Cómo abstraerse del proveedor y cuándo usar un agregador.
- Cómo evaluar la calidad frente al coste para elegir modelo.
- Qué pertenece al contexto y cuánto hay que reenviar.
- Cómo reducir el consumo con límites, caching y elección de modelo.
- Cómo escribir prompts robustos sin depender del prompting del usuario.

En el chat salieron OpenRouter, DeepSeek, Gemini, Artificial Analysis y OpenCode.
