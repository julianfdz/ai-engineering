# Línea de formación · Sesión 5 · Funcionalidades avanzadas

> Diapo a diapo: **qué contar**, **qué código abrir** (y qué parte), **qué lanzar en la terminal** y **qué enseñar
> en la interfaz**. Las rutas son relativas a `estimator/` salvo las de Rails (`estimator-web/`). En VS Code abre la
> carpeta `ai-engineering-s05`; Ctrl+P con el nombre del fichero y Ctrl+G con el número de línea. Las diapos llevan la
> misma ruta en su franja «En el código».
>
> Formato de la clase: **no se teclea código**. Todo está implementado; se abre, se explica y se ejecuta.

---

## Antes de empezar (10 min antes)

**PowerShell (comandos):**

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s05"
```

```powershell
docker compose -p aieng-s05live up -d
```

```powershell
docker compose -p aieng-s05live ps
```

Los cuatro contenedores `s05-*` deben salir `healthy`. Después pega una vez estos helpers:

```powershell
$B = "http://localhost:8000"
function nueva { (curl.exe -s -X POST "$B/sessions" | ConvertFrom-Json).session_id }
function estima($sid, $texto, $ruta = "estimate", $detalle = "medium") { curl.exe -s -X POST "$B/sessions/$sid/$ruta" --form-string "transcript=$texto" -F project_type=web_saas -F detail_level=$detalle -F output_format=phases_table | ConvertFrom-Json }
function info($sid) { curl.exe -s "$B/sessions/$sid" | ConvertFrom-Json }
```

En los comandos de abajo los textos van sin tildes: curl.exe en PowerShell 5.1 las rompe. En la web sí van con tildes.

**Pestañas del navegador:**

- Web: <http://localhost:3000> (estimación conversacional, con los **Demo presets** arriba)
- Swagger: <http://localhost:8000/docs>
- RedisInsight: <http://localhost:8001>

**VS Code** (carpeta `ai-engineering-s05`), con estos ficheros abiertos:
`app/sessions/models.py`, `app/sessions/compression/anchors.py`, `app/sessions/compression/policy.py`,
`app/sessions/tier_resolver.py`, `app/prompts/estimation/v3/system.j2`, `evals/golden_dataset.json`,
`evals/metrics.py`, `app/services/estimation.py`, `app/schemas/critic.py`, `app/services/boss.py`.

**Configuración local** (`estimator/.env`, no se sube): `PRIMARY_MODEL=gpt-4o` y `CRITIC_MODEL=gpt-4o`. Con el
`gpt-4o-mini` del guion la estimación devolvía **502** a menudo: no conseguía que las fases sumaran el total ni con 6
reintentos. Para enseñar el crítico pequeño (más iteraciones y falsos positivos), cambia `CRITIC_MODEL=gpt-4o-mini` y
recrea el servicio:

```powershell
docker compose -p aieng-s05live up -d --force-recreate estimator
```

---

## Apertura · 5 min

### Diapo 1 · Portada · Diapo 2 · Hoy

- Flipped classroom: el ejercicio se da por hecho. Hora 1, base conversacional + tres mejoras. Hora 2, Actor-Critic-Boss.
- Aviso: hoy no se teclea, se lee código y se ejecuta.

---

## Bloque 0 · El ejercicio · 15 min

### Diapo 3 · Lo que traéis del ejercicio previo

- 💻 **`app/sessions/models.py`**: `Message` (l. 38), `ConversationHistory` (l. 48), `ProjectMetadata` (l. 122) y su
  `merge_with()` (l. 143): lo escalar se pisa, las listas se suman sin duplicar.
- 💻 **`app/sessions/metadata_extractor.py`** → `update_metadata()` (l. 37): si el LLM falla, devuelve la metadata
  anterior y la conversación sigue.
- 💻 **`app/routers/sessions.py`**: `create_session` (l. 80), `get_session` (l. 89), `_resolve_session_and_enrich`
  (l. 109, el prólogo compartido por los dos endpoints), `estimate_in_session` (l. 185).
- 💻 **`app/attachments/extractor.py`**: `_SUPPORTED_EXTS` (l. 43), `_extract_pdf` (l. 50), `_extract_docx` (l. 66),
  `extract_text` (l. 74, trunca), `enrich_transcript` (l. 118, las marcas `--- attachment ---`).

### Diapo 4 · El orden de los mensajes

- 💻 **`app/services/estimation.py`** líneas 232-234: `[system] + historial + user`. El system no se guarda porque
  se re-renderiza con la metadata del turno.
- Repasa los cinco errores frecuentes de la diapo; pregunta quién se topó con cuál.

### Diapo 5 · Adjuntos: camino A vs B

- A (PDF directo al modelo) acopla al proveedor; B (extracción local) deja el wrapper agnóstico. El proyecto usa B.
- Pregunta: «¿alguien fue por el camino A? ¿Qué tal el acoplamiento?».

---

## Bloque 1 · Compresión con anclas · 15 min

### Diapo 6 · Estrategias de historial

- Ventana, resumen, anclas, híbrida. El fallo de la ventana: en el turno 7 se pierde el «firmamos NDA» del turno 1.
- 💻 `app/config.py` → `MAX_CONVERSATION_TURNS = 6` (l. 54): cuenta **pares**, así que caben 12 mensajes.

### Diapo 7 · Compresión híbrida

- 💻 **`app/sessions/models.py`** → `to_messages()` (l. 84): resumen como mensaje `user` sintético + anclas + ventana.
- 💻 **`app/sessions/models.py`** → `append()` (l. 70): **ya no recorta**. Lee el docstring en voz alta.
- 💻 **`app/sessions/compression/policy.py`** → `apply()` (l. 55): el bucle que saca pares de dos en dos; y
  `apply_compression()` (l. 101), la fachada que usa el servicio (`estimation.py` l. 265).
- 💻 `app/prompts/conversation_summary/v1/system.j2`: la regla «INTEGRATE»: se rehace el resumen entero, no se encadena.

### Diapo 8 · Anclas

- 💻 **`app/sessions/compression/anchors.py`** → `_HEURISTIC_PATTERNS` (l. 46): las 8 reglas; `detect()` (l. 99);
  modo LLM opcional `_detect_llm()` (l. 121).

### Diapo 9 · Demo: ocho turnos

⌨️ Terminal (tarda ~30 s, un turno cada 3-6 s):

```powershell
$S = nueva
estima $S "Turn1: we signed the NDA before this call. Estimate a CRM for the sales team, team of 3." | Out-Null
2..8 | ForEach-Object { estima $S "Turn$($_): refinamos alcance y anadimos features sobre el mismo CRM, manteniendo el mismo equipo." "estimate" "summary" | Out-Null; info $S | Select-Object message_count, anchors_count, summary_chars }
```

Sale: mensajes hasta 12 y se quedan ahí; en el turno 7 `anchors_count` pasa a 2 (el NDA); en el 8 aparece el resumen
(908 caracteres en nuestra prueba).

🖥️ **Interfaz:** cualquier conversación de varios turnos en <http://localhost:3000>: el panel lateral enseña
**Window**, **Anchors kept** y **Summary of evicted turns**.

💬 El remate: el tier solo es executive en el turno 1. El resolver mira el texto del turno y la metadata, no las anclas.
Pregunta abierta: ¿debería?

---

## Bloque 2 · Tier dinámico · 15 min

### Diapo 10 · Tiers

- 💻 **`app/prompts/estimation/v3/system.j2`** → bloque `<audience>` (l. 28-50): un único prompt con Jinja por tier.
- 💻 **`app/sessions/tier_resolver.py`** → `class Tier` (l. 41): hereda de `str`, por eso viaja en formularios y JSON.

### Diapo 11 · El resolver

- 💻 **`app/sessions/tier_resolver.py`**: regex (l. 64-74; NDA incluye `confidential`), `_has_nda` (l. 77),
  `_technical_audience` (l. 103: exige **2 palabras técnicas distintas**), `_RULES` (l. 112: el orden manda),
  `resolve_tier()` (l. 120: override primero, try/except por regla).
- 💻 `app/services/estimation.py` l. 210: la llamada y el cacheo en `session.last_resolved_tier`.

⌨️ Terminal:

```powershell
$S1 = nueva; estima $S1 "Estimar plataforma de e-commerce con catalogo de 5000 productos, buscador, carrito y checkout con Stripe. Equipo de 4 personas con React y Node." | Out-Null; info $S1 | Select-Object last_resolved_tier, last_tier_rule
```

```powershell
$S2 = nueva; estima $S2 "Heads-up, firmamos NDA antes de la llamada. Estimar plataforma de e-commerce con catalogo de 5000 productos, buscador, carrito y checkout con Stripe. Equipo de 4 personas con React y Node." | Out-Null; info $S2 | Select-Object last_resolved_tier, last_tier_rule
```

Salen `default / default` y `executive / nda_detected`.

🖥️ **Interfaz:** Demo presets → «Tier · sin NDA», «Tier · con NDA» y «Tier · developer» (Kubernetes + Kafka +
Terraform → `developer / technical_audience`). Pulsa **Send turn** y mira **Resolved tier** en el panel. Para cada
demo, **New conversation** primero.

⚠️ Con el tier executive el modelo a veces responde «Out of scope» (el bloque executive pide honestidad y se
retrae). Nos pasó en 2 de 3 pruebas; en la última dio 80.000 €. Si sale, úsalo: es justo lo que caza el golden set
(caso 007).

💬 Lo que vimos al probar: «equipo de 2 personas» **no** da `pm` en el primer turno, porque el tamaño del equipo llega
a la metadata después de resolver el tier.

---

## Bloque 3 · Golden dataset · 15 min

### Diapo 12 · El dataset

- 💻 **`evals/golden_dataset.json`**: abre el caso 001 y uno adversarial (006, inyección).
- 💻 **`evals/dataset.py`** → `GoldenCase` (l. 29): casi todo son rangos.

### Diapo 13 · Las métricas y lo que dijeron

- 💻 **`evals/metrics.py`**: `SchemaAdherenceMetric` (l. 37), `CostBoundsMetric` (l. 76), `ContentRecallMetric`
  (l. 114). Binarias a propósito: el `details` dice qué arreglar.
- 💻 `evals/run.py` → `_run_case_in_process` (l. 112): sesión nueva por caso, para que no se contaminen.

⌨️ Terminal (8 casos ≈ 1 min 30 s; lánzalo al empezar el bloque y sigue hablando):

```powershell
docker compose -p aieng-s05live exec estimator python -m evals.run --mode actor --limit 8 --output /app/evals/actor.json 2>$null | Select-String "case-|passing|schema_adherence:|cost_bounds:|content_recall:"
```

Nuestro resultado (gpt-4o): **5/8**. Fallan 004 (coste), 007 (NDA: «Out of scope») y 008 (HIPAA: coste fuera de
rango). El JSON queda en `estimator/evals/actor.json` para enseñar los `details`.

---

## Bloque 4 · El patrón Actor-Critic-Boss · 10 min

### Diapo 14 · Tres roles

- Dibuja el bucle. Los dos fallos que evita: bucle infinito (sin Boss) y sesgo de confirmación (crítica en texto libre).
- 💻 `app/routers/sessions.py` l. 214: `POST /sessions/{id}/estimate-acb`.

---

## Bloque 5 · Actor · 10 min

### Diapo 15 · El actor

- 💻 **`app/services/estimation.py`** → `estimate_conversational()` (l. 182): recorre los 8 pasos. El orden
  guardrail de salida (l. 259) → append + `apply_compression` (l. 265) → `update_metadata` (l. 274).
- 💻 **`app/services/estimation.py`** → `estimate_with_acb()` (l. 288) y el closure `_actor()` (l. 331).
- 💻 **`app/prompts/estimation/v3/user.j2`** l. 18: el `{% if critic_feedback %}`. Cero ramas en Python.
- En la sesión solo se guarda la respuesta final (l. 377-386); los borradores no.

---

## Bloque 6 · Critic · 15 min

### Diapo 16 · El crítico

- 💻 **`app/schemas/critic.py`**: las 7 categorías (l. 28), `CriticVerdict` (l. 42), `CriticIssue` con
  `field_path` (l. 45), `CriticFeedback` y su validador `iteration_requires_blocking_issue` (l. 74).
- 💻 **`app/prompts/critic/v1/system.j2`**: lee los bloques `<heuristics>`, `<verdict_rules>` y `<rules>`.
- 💻 **`app/services/critic.py`** → `review()` (l. 44) y el fallback `critic_failed_fallback_accept` (l. 72).

💬 Lo que vimos al probar: el crítico devolvió `accept` **con** un issue `critical` en la lista. El validador impide
iterar sin problemas graves, pero no impide aceptar con ellos. Buena pregunta: ¿añadiríais esa regla?

---

## Bloque 7 · Boss · 15 min

### Diapo 17 · El Boss

- 💻 **`app/services/boss.py`**: `ActorCallable` (l. 49), `run()` (l. 61), `_decide()` (l. 117, nueve líneas),
  `_synthesize_fallback()` (l. 128: avisos delante, confianza a la mitad con suelo de 30).
- 💻 `app/config.py` → `BOSS_MAX_ITERATIONS = 3` (l. 77).

### Diapo 18 · Demo ACB

⌨️ Terminal:

```powershell
$A = nueva; $a = estima $A "Estimar plataforma compleja: marketplace de servicios con pagos, KYC, chat, app movil, panel admin, multi-idioma. Equipo de 2 personas en 6 semanas." "estimate-acb" "detailed"; $a.acb.iterations | Select-Object iteration, critic_verdict, decision_after, issue_summary | Format-List; $a.acb.final_decision
```

Y el mismo texto en modo actor para comparar:

```powershell
$A2 = nueva; (estima $A2 "Estimar plataforma compleja: marketplace de servicios con pagos, KYC, chat, app movil, panel admin, multi-idioma. Equipo de 2 personas en 6 semanas." "estimate" "detailed").result | Select-Object total_cost_eur, total_duration_weeks, confidence_pct
```

🖥️ **Interfaz:** Demo presets → «ACB · CRM + Stripe» (normalmente `accept` a la primera) y «ACB · marketplace
imposible» (sale `reject → synthesize` o `needs_iteration → accept`, depende de la ejecución). Ya vienen con
**Actor-Critic-Boss** marcado. Debajo del resultado, la **traza** desplegada con cada iteración.

Tiempos reales: 6-12 s con el crítico gpt-4o; 20-30 s con gpt-4o-mini (tres rondas y `synthesize`).

---

## Bloque 8 · Trade-offs y cierre · 10 min

### Diapo 19 · ¿Compensa?

⌨️ Si da tiempo (≈ 1 min 30 s):

```powershell
docker compose -p aieng-s05live exec estimator python -m evals.run --mode acb --limit 8 --output /app/evals/acb.json 2>$null | Select-String "case-|passing"
```

Nuestro resultado: actor **5/8**, ACB **6/8**. Ganó el 004 (ETL); el 007 (NDA) falla en los dos.

### Diapo 20 · La interfaz

- 🖥️ Recorre la pantalla: Demo presets, Audience tier (el override), Estimation mode, panel lateral, traza.
- 💻 Rails: `estimator-web/app/services/estimator_ai/client.rb` (`estimate_in_session_acb`, `build_estimate_body`),
  `app/controllers/chat_sessions_controller.rb` (`PRESETS`, el switch de `mode`, `refresh_metadata_snapshot`),
  `app/views/chat_sessions/_form.html.erb`, `_metadata_panel.html.erb`, `_estimation_result.html.erb`.
- La rama oficial no traía esta parte de la web (el Anexo D del guion); está montada en nuestra rama local.

### Diapo 21 · Cierre · Diapo 22 · ROTI · Diapo 23 · Gracias

- Las cuatro preguntas para pensar. Siguiente sesión: S6, Data-driven AI.
