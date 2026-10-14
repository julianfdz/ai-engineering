# Guion de Julián · Sesión 6 LIDR · Data-driven AI

> Mi guion personal para dar la clase: qué digo, qué diapo pongo, qué fichero abro y qué comando lanzo.
> Las diapos son las del **deck de alumnos**: `Sesion06-Julian-Fernandez.pdf` (30 diapos).
> El guion oficial completo está en [guion-directo.md](guion-directo.md).

---

## 🔧 Antes de empezar (5 min antes)

**Dónde lanzo TODO:** en **PowerShell**, siempre desde la carpeta del worktree de la S6:

```powershell
cd "C:\Users\jferc\Documents\Bussines\BUHO\repo auxiliar\LIDR\ai-engineering-fork-julian\ai-engineering-s06"
```

1. Abrir **Docker Desktop** y esperar a que el motor esté verde.
2. Comprobar que los 5 contenedores están sanos (`healthy`):

   ```powershell
   docker compose -p aieng-s06live ps
   ```

   Si alguno está parado, levantarlos **sin** reconstruir:

   ```powershell
   docker compose -p aieng-s06live up -d
   ```

3. Pasar el preflight (tienen que salir 8 ✅):

   ```powershell
   docker compose -p aieng-s06live exec estimator python scripts/preflight_s06.py
   ```

**Ventanas abiertas:**

- **VS Code** con la carpeta `ai-engineering-s06` (el código de la sesión).
- **El PDF** de alumnos para proyectar.
- **El navegador** con http://localhost:8000/docs (Swagger, para la demo web).
- **PowerShell** ya situado en la carpeta de arriba.

> ⚠️ Todos los comandos llevan `-p aieng-s06live`. Sin eso, Docker no encuentra los contenedores.

---

## 📖 Glosario rápido

| Término | Qué es |
|---|---|
| **PII** | *Personally Identifiable Information*: información personal identificable (nombres, emails, teléfonos, DNI…) |
| **CAG** | Meter todo el conocimiento dentro del prompt y cachearlo |
| **RAG** | Guardar el conocimiento fuera (vectores) y recuperar solo lo relevante en cada pregunta |
| **Lost in the middle** | El modelo atiende peor lo que está a mitad de un prompt largo: pierde la información del centro |
| **Document** | La entidad base de la sesión: cualquier fichero (PDF, JSON, Excel…) convertido a texto + metadatos |
| **Metadatos** | Datos sobre los datos: de dónde viene, cuándo, quién es el responsable, si tiene PII… |
| **Cuarentena** | Un registro dudoso que no entra al RAG pero se guarda para que lo revise una persona |

---

## 1 · El ejercicio: estresar el CAG

# 🖥️ DIAPO 4 — "¿Qué restricción del CAG se rompió primero?"

*(Antes, 30 segundos con la **diapo 2** para presentarme.)*

- Preguntar quién ha hecho el ejercicio, qué experiencia han tenido y si han sacado alguna conclusión.
- El ejercicio era **estresar el sistema**. Lo que tienen que haber notado:
  - **Más coste** y **más lentitud** a medida que crece la información.
  - Que mucha información ya es un reto en sí: aparecen **grietas en la memoria y en la calidad**.
  - **Lost in the middle**: se pierde la información de la mitad del prompt porque se pierde la atención.
- Apuntar en la tabla de la diapo los números de 3–4 alumnos y **cortar al cuarto**.

---

## 2 · Enfoque y objetivo de la sesión

# 🖥️ DIAPO 3 — "Lo que vamos a ver hoy"

- Qué tienen que llevarse de hoy: un corpus **listo y defendible** antes de vectorizar.
- Hoy **no vectorizamos nada**: preparamos los datos para que merezcan ser vectorizados.

---

## 3 · Data-driven AI como metodología

# 🖥️ DIAPO 5 — "Data-driven AI"

*(La **diapo 6** — "Cada problema de la IA genérica, una pieza" — refuerza esta idea si hay tiempo.)*

- Data-driven AI es una **metodología de trabajo**: todo el foco y la importancia están en los **datos**.
- El dato de internet no es fiable. Todo se construye con los **datos privados** de la empresa, del proyecto, del negocio.
- La idea clave: **depender de los datos, no del modelo**.

---

## 4 · RAG vs fine-tuning

# 🖥️ DIAPO 7 — "RAG vs Fine-tuning · cinco dimensiones"

- **Muy importante saber diferenciarlos.**
- No significa que RAG sea perfecto ni que el fine-tuning no haga falta nunca: a veces sí hace falta, pero hay que saber cuándo.
- **Limitaciones del RAG:** el error típico es *chunkear* mucha información a lo loco y que luego no funcione. Los programadores nos ponemos a crear muchos vectores, pero **si no reflejan la verdad, no sirven de nada**.
- **Embeddings y vectores → Sesión 7.** Si preguntan, respuesta única: *"eso es la Sesión 7"*.

---

## 5 · Las restricciones del CAG

# 🖥️ DIAPO 10 — "Las cuatro restricciones del CAG"

*(Si quieres dar el mapa antes: **diapo 9**, "El viaje del dato, cinco piezas".)*

- Las cuatro tienen que estar en verde **a la vez**: context window, coste, latencia y lost-in-the-middle.
- Es un **AND, no un OR**: basta con que falle una.

---

## 6 · El código que decide si el CAG es viable

# 🖥️ DIAPO 11 — "Dónde vive: architecture.py"

**📂 VS Code:** `estimator/app/ingestion/architecture.py`

- Enseñar `CAGViability`: analiza si es viable usar un CAG. Señalar que `viable` es un `all([...])`.
- Enseñar `recommend_architecture` y los cuatro ejes.

**▶️ Lanzar (PowerShell, en la carpeta `ai-engineering-s06`):**

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.architecture
```

**Sale:** `Viabilidad CAG: NO viable` · `Restricciones en rojo: context_window, latency, lost_in_the_middle` · `Recomendación arquitectónica: RAG`.

*(Opcional: **diapos 12 y 13** con el árbol CAG / RAG / híbrido.)*

---

## 7 · El antipatrón: vectorizar primero, mirar después

# 🖥️ DIAPO 14 — "Antipatrón: vectorizar primero, mirar después"

- Recalcar el error de **primero vectorizar y luego mirar los datos**. Es al revés: primero conviene **normalizar**.
  - Quizá transformar cosas a JSON.
  - Limpiar.
  - Pasarlos por una IA uno a uno quitando erratas, información que sobra, información redundante…
- **El caos documental de las empresas:** primero deberían haber digitalizado para poder entrar a la IA, pero muchas no lo han hecho. **No se puede empezar la casa por el tejado** si trabajan con documentos sueltos o con ERPs de hace 20 años.

**📂 VS Code:** `estimator/data/seed/` → enseñar las carpetas `budgets/` y `transcripts/` (y el `rate_card_2024.xlsx` suelto).

---

## 8 · Catalogar: metadatos y prefiltro

# 🖥️ DIAPO 15 — "El catálogo es código, no documentación"

- La idea ahora es **catalogar toda la información** del RAG y crear **metadatos** (datos sobre los datos) para hacerles un **prefiltro**.
- Inspeccionar los datos antes de decidir nada.

**📂 VS Code:** `estimator/app/ingestion/catalog/models.py`

- Enseñar las tres decisiones: `include`, `review` y `exclude`.
- Si no es `include`, el **motivo es obligatorio**.

**📂 VS Code:** `estimator/data/catalog/catalog.yaml`

- Es un fichero YAML sin más, algo simple, pero con la información bien puesta.

> 💡 **Matiz para no liarla:** en el código de la sesión la decisión la toma **una persona** (el YAML se escribe a mano). Que **la IA procese el documento y lo catalogue ella misma** es una idea mía y una extensión muy buena para proponer, pero no es lo que hace este repo.

---

## 9 · Inspeccionar los datos

**▶️ Lanzar (PowerShell, en la carpeta `ai-engineering-s06`):**

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.catalog.inspect data/seed
```

**Sale:** `budgets 6 files` · `transcripts 3 files` · `seed 1 files latest=2024-01-12 formats=xlsx`.

→ Señalar el XLSX: **última modificación de enero de 2024**. Es la "fuente podrida".

Y para ver el catálogo validado (**3 fuentes, solo 1 incluida**):

```powershell
docker compose -p aieng-s06live exec estimator python -m app.ingestion.catalog.loader data/catalog/catalog.yaml
```

*(Sale un `RuntimeWarning` de Python al principio: es inofensivo, ignorarlo.)*

---

## 10 · Loader, parser y Document

# 🖥️ DIAPO 16 — "Tres capas, responsabilidades separadas"

- La diferencia entre **loader** y **parser**, porque no es lo mismo:
  - El **loader** trae el documento (los bytes).
  - El **parser** es uno por tipo de documento: el que lo sabe leer.
- Y la entidad **Document**: la base del RAG o de la base de conocimiento. Me da igual si era PDF, Excel o JSON: para mí ya son datos en un abstracto *Document*, y además lleva **metadatos**.
- **Document es la entidad clave de esta sesión.**
- El loader que tenemos ahora es en local, pero es fácilmente intercambiable. Lo normal es tener **varios loaders, varios parsers y una sola entidad Document**, y construir el catálogo encima.

# 🖥️ DIAPO 17 — "El Document canónico y los parsers"

**📂 VS Code:**

- `estimator/app/ingestion/documents/models.py` → el `Document`
- `estimator/app/ingestion/loaders/filesystem.py` → el loader local
- `estimator/app/ingestion/parsers/` → `budget_json.py` y `transcript_txt.py`

*(Opcional: **diapos 18 y 19** con offline vs online y la demo de ingesta. Ver "Demo web" abajo.)*

---

## 11 · Madurez documental y saltos de precisión

# 🖥️ DIAPO 20 — "La madurez documental marca el techo de precisión"

- Esta madurez documental y este detalle **hay que saberlos de antemano**, porque luego vienen las quejas y los problemas con el cliente, con el jefe de proyecto, etc.
- **Los saltos de precisión:**
  - Tener un resultado de un **60 %** de precisión es fácil.
  - De un **60 a un 80 %** ya es un salto enorme, metiendo cosas como las que estamos viendo hoy.
  - Pasar cerca del **100 %**, o sin errores, en una adopción de IA agéntica o RAG ya son **meses de trabajo**, o directamente imposible por la propia IA.

---

## 12 · Limpieza y validación

# 🖥️ DIAPO 21 — "Cuatro familias de suciedad" → DIAPO 22 — "Limpiar y validar son dos pasos distintos"

**▶️ Lanzar (PowerShell, en la carpeta `ai-engineering-s06`):**

```powershell
docker compose -p aieng-s06live exec estimator python scripts/demo_cleaning_s06.py
```

**Sale:** `input_rows: 5` · `valid_rows: 3` · `quarantined_rows: 1` · `discarded_rows: 1` · descartada `BUDGET-2024-0004 -50000` · en cuarentena `BUDGET-2024-0002`.

# 🖥️ DIAPO 23 — "Lo que sale de verdad en la demo"

- 6 ficheros → 5 filas: el dedup fusionó las dos versiones de `BUDGET-2024-0005`.
- **Ojo:** la que va a cuarentena es la 0002 (por su fecha `12/03/2024`), **no** la del `"TBD"`. La limpieza no pudo reparar esa fecha y la validación la cazó: por eso son dos pasos distintos.

---

## ➕ Lo que todavía no está en mi guion (propuesta, por si da tiempo)

### 13 · PII y pseudonimización

# 🖥️ DIAPO 24 — "Tres modos de filtración semántica"

- Pregunta al chat: ¿cuál es la más peligrosa? → **la inferencia**.

# 🖥️ DIAPO 25 — "Empezar por el fallo: Presidio en inglés"

**📂 VS Code:** `estimator/app/ingestion/pii/analyzer.py`

- Presidio por defecto va en inglés y **no detecta "Laura Fernández"**. Falla en silencio.

# 🖥️ DIAPO 26 — "Mismo valor → mismo pseudónimo"

**▶️ Lanzar (PowerShell, en la carpeta `ai-engineering-s06`):**

```powershell
docker compose -p aieng-s06live exec estimator python scripts/demo_pii_s06.py
```

**Sale:** la transcripción con nombres, emails e ids sustituidos por otros falsos y verosímiles. Comentar los **falsos positivos** (un código de cliente sustituido por un nombre): es el precio de Presidio en español.

# 🖥️ DIAPO 27 — "Derecho al olvido (GDPR art. 17)"

- Sin la mapping table, borrar a un cliente es imposible.

### 14 · Cierre

# 🖥️ DIAPO 28 — "Cinco piezas: el corpus ya es defendible"

- La Sesión 7: chunking, embeddings y pgvector.

# 🖥️ DIAPO 29 — ROTI → DIAPO 30 — ¡Gracias!

---

## 🌐 Demo web (alternativa a la terminal)

**La web de Rails (`localhost:3000`) no tiene nada de la Sesión 6**: solo el chat de la S5 y las estimaciones de la S4. Para enseñar la ingesta con interfaz gráfica, usar el **Swagger** del servicio de IA:

1. Abrir **http://localhost:8000/docs** → bajar a la sección **ingestion**.
2. **`POST /api/v1/ingestion/runs`** → *Try it out* → en el cuerpo poner:

   ```json
   {"source_name": "presupuestos_json"}
   ```

   → *Execute* → respuesta **202** con un `job_id` y `"status": "pending"`.
3. Copiar el `job_id` → **`GET /api/v1/ingestion/jobs/{job_id}`** → *Try it out* → pegarlo → *Execute* → `"status": "completed"`, `"documents_count": 6`.
4. Repetir el paso 2 con `"rate_card_xlsx"` → **400** (fuente excluida) y con `"no_existe"` → **404**.

**Lo mismo desde PowerShell** (aquí `curl` no sirve: en PowerShell es otro comando y rompe las comillas del JSON):

```powershell
$r = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/ingestion/runs -ContentType 'application/json' -Body '{"source_name":"presupuestos_json"}'
$r
Invoke-RestMethod "http://localhost:8000/api/v1/ingestion/jobs/$($r.job_id)" | Format-List
```

**El "cameo" de Rails** (Rails como cliente HTTP de la ingesta, desde la terminal):

```powershell
docker compose -p aieng-s06live exec estimator-web bin/rails runner 'c = EstimatorAi::IngestionClient.new; j = c.trigger_ingestion(source_name: :presupuestos_json.to_s); p j; sleep 2; p c.job_status(j.fetch(:job_id.to_s))'
```
