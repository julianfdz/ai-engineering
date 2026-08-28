# Jinja2 — plantillas para prompts

## Qué es

Jinja2 es un **motor de plantillas** para Python: genera texto mezclando
partes fijas con huecos que se rellenan con datos en runtime. El equivalente
en el mundo Rails es ERB (los `.html.erb` del business-backend). Es open
source (licencia BSD-3), del proyecto **Pallets** — la misma familia que
Flask, y de hecho Flask lo trae de serie. Nació para generar HTML; el curso lo
reutiliza para generar prompts, el "HTML de la era LLM". (El nombre es un
juego de palabras: *jinja* es "templo" en japonés — temple ↔ template.)

## La sintaxis en tres piezas

```jinja
{{ description }}                     ← hueco: se sustituye por la variable

{% if critic_feedback %}              ← condicional: el bloque solo aparece
  ...                                    en el texto final si se cumple
{% endif %}

{% for issue in critic_feedback.issues %}
- [{{ issue.severity }}] {{ issue.description }}     ← bucle: una línea por elemento
{% endfor %}
```

## Por qué usar esto en vez de un f-string

Para un prompt fijo con dos variables, un f-string es perfectamente válido (y
las sesiones 9–14 del proyecto lo hacen así). Jinja2 gana cuando el prompt es
**dinámico** — una función de la situación:

1. **Lógica declarativa dentro del texto.** "Si hay feedback del crítico,
   añade esta sección con un bullet por problema" se escribe en el sitio donde
   aplica, y el prompt completo se lee de arriba a abajo tal y como lo verá el
   LLM. En f-string esa lógica se saca fuera (construir el bloque aparte,
   concatenar condicionalmente, cuidar los `\n`) y el prompt queda despiezado
   en variables que hay que ensamblar mentalmente.
2. **El prompt como fichero de datos, no como código.** La plantilla vive en
   su propio fichero de texto: quien no sabe Python puede leerla y editarla,
   y los diffs de git muestran el cambio del prompt limpio, sin código
   alrededor.
3. **Versionado por carpetas.** `v1/`, `v2/`, `v3/` conviven; la versión es un
   parámetro en runtime, la API devuelve `prompt_version` en cada respuesta, y
   las cachés particionan por versión (cambias el prompt y no se sirven
   respuestas viejas).

Regla práctica: **f-string hasta que el prompt tenga secciones condicionales,
versiones o editores no-programadores; a partir de ahí, plantillas.**

## Dónde verlo en el proyecto

- Las plantillas: `ai-service/app/foundation/prompts/` — `estimation/v1..v3/`,
  `critic/v1/`, `conversation_summary/`, `metadata_extraction/`, cada una con
  su `system.j2` + `user.j2`.
- El renderizado: `app/foundation/prompts/loader.py::render_estimation_prompt`.
- El ejemplo estrella de prompt dinámico: `estimation/v3/user.j2` — la sección
  `<critic_feedback>` solo existe en los reintentos del flujo Actor-Crítico;
  en la primera llamada el LLM ni la ve. Mismo template, dos prompts distintos
  según la situación.
- El contraste: los prompts de las sesiones 9–14 (RAG, agentes, grafos,
  supervisor) son f-strings inline junto a su lógica — decisión pedagógica de
  localidad, no la práctica que se recomienda para producción.
