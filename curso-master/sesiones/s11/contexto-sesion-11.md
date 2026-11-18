# Sesión 11 — RAG avanzado: generación y calidad (contexto)

> Edición 2026-09 · miércoles 18/11/2026, 17:30–19:30 · Mentor: Julián · TA: George Kutsia.
> Primera vez que Julián da esta sesión. Con este grupo ya ha dado la S6 (14/10), la S7 (21/10) y la S10 (11/11);
> la S8 y la S9 las dio Juan Pablo Mesa.
> Fuente: Notion de LIDR (exportado a `LIDR\edicion-26-09\s11-rag-avanzado-generacion-y-calidad\`). Sesión con mejor
> ROTI: edición 2026-04, Antonio Pérez (4,50).

## 1. De qué va

La S9 y la S10 fueron la mitad de **recuperación** del RAG. Esta es la mitad de **generación**: que la estimación
no solo cite, sino que la cifra se sostenga con lo que cita, que el contexto de entrada sea mejor, que las fuentes
contradictorias se vean y que todo se pueda **medir** antes y después de desplegar.

**El arco:** citada (S9) → verificable (ejercicio: el `chunk_id` existe) → fundamentada (hoy: la cifra se deduce
de la cita) → medible (hoy: RAGAS como puerta y como monitor).

**Hilo conductor:** la tabla RAGAS que traen del ejercicio es el marcador. Cada técnica se mide contra ese
baseline: medir → mejorar → medir.

## 2. Ejercicio previo (rama `session_11`)

- **Citación verificable por línea**: `SourceReference{chunk_id, document_id, evidence}`, `TaskItem.grounded` +
  `sources`, y `verify_citations` (grounded / dangling / insufficient) con un reintento correctivo.
- **Baseline RAGAS**: golden set de 5 consultas con `ground_truth` en días, las 4 métricas y su tabla
  (`evals/RAGAS_BASELINE_S11.md`).

| Métrica | Media | Lectura |
|---|---|---|
| `context_precision` | 1,00 | trae lo relevante |
| `context_recall` | 0,11 | el juez no casa días con horas |
| `faithfulness` | 0,55 | la cita existe, la cifra no siempre se deduce |
| `answer_relevancy` | 0,03 | métrica mal planteada para un brief frente a una tabla |

169 líneas, 116 grounded, 53 sin datos y 0 colgantes.

## 3. El directo (rama `session_11_live`) · 120 min

| # | Bloque | Min | Demo clave |
|---|---|---|---|
| 1 | Pre-vuelo + errores | 15 | 5 comprobaciones; `demo_verify_citations_s11.py` → PASS |
| 2 | Leer la tabla RAGAS | 15 | 4 métricas, 2 ejes; la peor métrica de cada uno |
| 3 | Detección de alucinaciones | 25 | `/stages/verify`: atribución falsa → `degraded` |
| 4 | Augmentation + síntesis | 25 | contexto −30 % tokens; caso 40/90 → rango |
| 5 | Evaluación en dos modos | 20 | `eval_generation_s11.py --gate` (exit code) / `--monitor` |
| 6 | Ampliar e indexar el corpus | 12 | `POST /embeddings/index/runs` async → el corpus crece |
| — | Cierre | 8 | el arco de calidad; puente a agentes (S12) |

Todo el código nuevo del servicio IA vive en `app/generation/rag/quality/` (`hallucination.py`,
`augmentation.py`, `synthesis.py`) y se engancha solo a través del conductor `rag/estimator.py` (paso 4:
augmentation; paso 6.5: gate). Los tres interruptores (`HALLUCINATION_GATE_ENABLED`, `AUGMENTATION_ENABLED`,
`SYNTHESIS_ENABLED`) se cambian en caliente con `PUT /api/v1/config/retrieval`.

## 4. En local

- Worktree `ai-engineering-fork-julian\ai-engineering-s11`, rama **`session_11_live_local`** (desde
  `origin/session_11_live`, subida al fork). Proyecto **`-p aieng-s11live`**, contenedores `s11-*`, puertos
  8000 (API) y 3000 (web).
- Parches locales, igual que en la S7 y la S10: Dockerfile con torch CPU + `es_core_news_md` + NLTK, override con
  `container_name` `s11-*` y montaje de `evals/`, scripts de Rails a LF. Imagen del servicio IA: 5,7 GB (datos de
  Docker en D:).
- `estimator/.env` y `estimator-web/.env` copiados de la S10 (`RETRIEVAL_API_KEY=demo-retrieval-key`,
  `ESTIMATE_API_KEY=demo-estimate-key`). Las variables de la S11 no hace falta ponerlas: los valores por defecto de
  `config.py` son los del guion (gate on, juez `gpt-5-mini`, tolerancia 0,5, augmentation on, síntesis on, umbral
  0,35).
- Venv aislado de RAGAS: `estimator\.ragas-venv` (ragas 0.4.4, 425 MB, ignorado por git).
- Cada fichero que se abre en clase lleva arriba una cabecera en español «Julián · Sesión 11 · …» con para qué
  sirve y cuatro puntos de lo que hay que enseñar.

### Interfaz añadida en local

La web oficial trae la sección Corpus / Índice (sin enlace en el menú) y, en el wizard, el rango de horas en ámbar.
No tenía forma de enseñar el gate, la augmentation ni los interruptores: el paso de generación del wizard es solo
estructura desde la S10, así que su panel de «Gate semántico» no aparece nunca.

| Menú | Ruta | Qué hace |
|---|---|---|
| **Calidad** → Gate | `/rag/quality` | 5 casos (atribución falsa, porción honesta, exceso tolerado, abstención, los cuatro), con o sin juez y con evidencia completa o solo «120 h» |
| Calidad → Fuentes en conflicto | `/rag/quality?tab=conflict` | horas por tarea con módulo, nombre y descripción; consenso, dispersión, rango y vecinos |
| Calidad → Augmentation | `/rag/quality?tab=augment` | el mismo bloque `<sources>` sin y con augmentation, lado a lado, con tokens y orden |
| Calidad → Interruptores | `/rag/quality?tab=toggles` | los tres interruptores de la S11 (Redis, sin reiniciar) |
| **Corpus** | `/rag/index_runs` | la sección oficial, ahora en el menú; el formulario trae relleno el proyecto KYC |

Ficheros: `Rag::QualityController`, `EstimatorAi::QualityClient`, `app/views/rag/quality/show.html.erb`, rutas en
`config/routes.rb`. Las demos aceptan también GET, así que cada una tiene enlace directo (ver el guion).

## 5. Verificado en local el 17/11/2026

| Demo | Resultado |
|---|---|
| Stack | 5 contenedores sanos; migración `0005_session11_hnsw_multi_index` aplicada |
| Corpus | 60 componentes + 1.547 tareas (1.543 + 4 del fixture) en `budget_chunks`; 11 transcripciones; 8 docs técnicos; total 1.626 |
| Tests de la S11 | 52 pasan (gate, síntesis, augmentation, citación, indexación, endpoints) |
| `demo_verify_citations_s11.py` | 4 líneas: 2 grounded, 1 dangling (999), 1 insufficient → **ACCEPTANCE: PASS** |
| Gate sin juez, 90 d sobre 120 h | `degraded`, «claims 90d but the cited evidence supports ~15d», desviación 5,0 |
| Gate, los cuatro casos | ancla: 2 grounded, 1 degraded, 1 insufficient |
| Gate + juez, evidencia completa | 1 grounded, 2 degraded (también la de 20 d), 1 insufficient · 7 s |
| Gate + juez, evidencia «120 h» | 0 grounded, 3 degraded: el juez rechaza también la porción honesta |
| Augmentation, banca móvil (8 fuentes) | 1.061 → **740 tokens (−30 %)**; orden 2·1·3·4·868… → 2·3·868…4·1 |
| Conflicto, descripción «Multi-channel delivery…» | vecinos 90/40/15/23/23 h; consenso 39 h, fiabilidad 0,19, dispersión 0,71 → **rango 15–90 h** (estable en 3 repeticiones) |
| Conflicto, descripción del guion | solo entra el de 40 h → rango 15–40 h |
| Sin análogo («Quantum teleporter calibration») | sin horas (fila roja) |
| EXPLAIN | Seq Scan (12 ms); con `enable_seqscan=off` → Index Scan HNSW (1,3 ms); la consulta con `vector` a secas no puede usar el índice |
| Ampliación (KYC, 3 componentes) | job 202 → completed en 0,3 s; 1.607 → 1.610 chunks; «biometric KYC onboarding…» pasa de 0,465 (tarea genérica) a **0,167** (el proyecto nuevo, top 3) |
| Documento repetido | job `completed` con 0 procesados |
| Web | home, Calidad (4 pestañas y sus formularios), Corpus, Añadir información, wizard y Ajustes: 200 |

### Re-verificado el 18/11 con saldo nuevo

| Demo | Resultado |
|---|---|
| Gate por la web | ancla 2/1/1 · con juez 1/2/1 · juez con evidencia «120 h» 0/3/1 (igual que el 17/11) |
| Conflicto | 15–90 h, consenso 39 h, dispersión 0,71, vecinos 90/40/15/23/23 |
| Augmentation | 1.061 tokens sin augmentation (8 fuentes), mismo orden |
| Corpus por la web | KYC de 0,465 a **0,167**, 1.607 → 1.610; repetido → `documents_skipped=1` |
| **Puerta del Bloque 5** (`--gate --config full --limit 2`) | faithfulness 0,551 · answer_relevancy 0,039 · context_precision 1,000 · context_recall 0,312 · 0 colgantes → **GATE: DEPLOY, exit 0** · 28 líneas degradadas por el gate |
| **Monitor** (mismas muestras) | faithfulness 0,535 · answer_relevancy 0,039 · 0 colgantes |
| Tiempos | recoger 5,5 min (2 × gpt-5 + juez), puntuar 83 s la puerta y 65 s el monitor |

La recogida está commiteada en `estimator/evals/s11_full.json` como plan B. Con 2 de las 5 consultas la tabla es
orientativa: el baseline se hizo con las 5.

Después de cada prueba se borró lo añadido (`DELETE FROM documents WHERE source_path LIKE 'corpus-expansion::%'`) y
el historial de la web (`Rag::IndexRun.delete_all`) para hacer la demo en directo desde 1.607 y con la lista vacía.

## 6. Diferencias con el guion de LIDR

- **El caso 40 h / 90 h no sale 40–90.** Con la descripción del guion («push, email and SMS with retries») el
  vecino de 90 h no entra en el top 5: sale **15–40 h**. Con la descripción «Multi-channel delivery (push, email,
  SMS) with a durable queue, per-channel retry and backoff and delivery receipts» entran los dos y sale **15–90 h**:
  el mínimo lo pone una tarea del corpus base, porque el rango es el min/max de los vecinos. Subir `top_k` (la
  contingencia del guion) lo empeora: con 10 o 15 vecinos la dispersión baja y no hay rango.
- **El módulo cuenta.** La búsqueda de horas usa módulo + nombre + descripción: la misma tarea bajo el módulo
  «Demo» pierde el vecino de 40 h. En Calidad el módulo es un campo.
- **El EXPLAIN del guion sale Seq Scan, no Index Scan.** Con 1.607 filas el planificador elige recorrer la tabla.
  Para enseñar que el índice casa: `SET enable_seqscan = off;` delante (mismo comando con `-c` doble, ver el guion).
- **La búsqueda final del Bloque 6 usa `$EST` y da 401**: `/v1/retrieval/search` pide la clave de recuperación
  (`demo-retrieval-key`).
- **El presupuesto de ejemplo del Bloque 6 no se recupera después**: su texto es tan pobre («OAuth2 login»,
  descripción «auth») que no entra en el top 3 de «OAuth2 login authentication backend». Se usa el proyecto KYC.
- **La tolerancia y el umbral de contradicción no se cambian en caliente**: `PUT /api/v1/config/retrieval` solo
  acepta los tres interruptores (y los de la S10). `HALLUCINATION_NUMERIC_TOLERANCE` y
  `SYNTHESIS_CONTRADICTION_THRESHOLD` se leen del `.env` (hay que recrear el contenedor).
- **El juez no tiene tolerancia.** El ancla deja pasar hasta +50 %; el juez rechaza cualquier exceso sobre las horas
  citadas y, si la evidencia es solo «120 h», rechaza también las líneas honestas porque no nombra el trabajo.
- **La compresión pierde nombres de componente**: `extract_key_points` solo conserva líneas con un dígito o «::».
  En los chunks reales la línea «Component: Transaction ledger service» no tiene ninguna de las dos y desaparece.
  El «::» solo aparece en el ejemplo de juguete del guion.
- **`_apply_config` del script de evaluación cambia los ajustes del proceso, pero manda Redis**: si un interruptor
  está cambiado en caliente, las configs `baseline/gate/augment/full` no lo pisan. Dejarlos en «Por defecto»
  antes de comparar.
- **Prerrequisitos en Windows**: los `uv run` del guion en el host necesitarían instalar el proyecto entero (torch
  incluido). Se ejecuta todo dentro del contenedor (`docker compose -p aieng-s11live exec estimator python …`) y
  solo la puntuación de RAGAS en `.ragas-venv`.
- En el guion pone «Módulo 3»; en el índice del máster es el Módulo 4 (Arquitectura RAG). El deck usa el 4.

## 7. Material para clase

| Pieza | Fichero | Qué es |
|---|---|---|
| Deck de Julián | [`Sesion11-Julian-Fernandez.pdf`](Sesion11-Julian-Fernandez.pdf) | 23 diapos: portada, 20 de contenido con franja «En el código» y cifras de la ejecución local, ROTI y gracias |
| Generador | [`deck/build_deck.py`](deck/build_deck.py) | motor de la S7 + franja de la S5; `python build_deck.py` |
| Capturas | `curso-master/assets/s11-ui-*.png` | Calidad → Gate, Fuentes en conflicto, Interruptores y Corpus |
| Línea de formación | [`guion-julian.md`](guion-julian.md) | diapo a diapo: qué contar, qué fichero abrir y en qué línea, qué lanzar en PowerShell y qué enseñar en la web |
| Guion de LIDR | [`guion-directo.md`](guion-directo.md) | copia del Notion con una nota local al principio |

El Notion no trae imágenes de diapositivas para esta sesión (solo marcadores `[SLIDE: …]`); las Google Slides de
LIDR solo abren con la cuenta de LIDR.

## 8. Pendiente

- [x] Saldo de OpenAI: recargado el 18/11 (la clave es la misma; no hizo falta recrear el contenedor).
- [x] Tablero del Bloque 5 precalculado (config `full`, 2 consultas) y en la diapo 15.
- [x] Captura de Calidad → Fuentes en conflicto (`assets/s11-ui-conflict.png`) en la diapo 13.
- [ ] `--compare` de las cuatro configs: no se ha lanzado (4 × 5 consultas con gpt-5, unos 50 min). No hace falta
  para la clase.
