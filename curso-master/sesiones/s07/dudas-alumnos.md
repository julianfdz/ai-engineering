# Sesión 07 — Dudas y entregas de alumnos (vía George, Slack)

> Notas para decidir qué respondemos en el directo. George propone responder **en directo**:
> "así da la sensación de que miramos las dudas y los ejercicios de todos".

---

## 1. Gabriel Suárez — entrega del ejercicio 7

- Entrega: https://github.com/gabogosp/master-ai-engineering/tree/session-07/pre-exercise
- Mensaje:

  > Encontré algo que vale la pena discutir en el directo: la pareja de textos semánticamente
  > cercanos dio **0.5957**, por debajo del umbral orientativo de 0.6 (lo dejé documentado tal
  > cual en vez de forzar el resultado, ya que los textos/modelo/dimensión/métrica son fijos por
  > consigna).
  >
  > Agregué tests unitarios (27, todos mockeados) aunque la consigna los marcaba como opcionales
  > para este ejercicio.

**Nota:** es exactamente el mismo 0,5957 del sanity check de la rama oficial
(`app/generation/rag/SANITY_CHECK.md`, pareja A). Encaja con su comentario: los umbrales de
similitud dependen del modelo y de la redacción, no son constantes universales.

---

## 2. Miguel Ángel Camacho — dudas

- Entrega: https://github.com/biomacam/estimador-cag/tree/session07/pre-exercise
- Mensaje (a George):

  > - En el ejercicio, en el paso 4 se comenta: *"Recomendación de tamaño de batch: 100 chunks
  >   por llamada. Esto es importante para no martillear la API con peticiones serializadas."*
  >
  >   Fuera del contexto del RAG, si yo tuviese que extraer la información de digamos 1000 PDFs
  >   de presupuestos con un LLM, adoptaría como estrategia crear un pipeline similar al de la
  >   sesión 6, en el que primero extraigo a texto plano la información de los PDFs. El objetivo
  >   sería aligerar el proceso del LLM y el consumo de tokens. En este tipo de pipelines, ¿sería
  >   indicado hacer una llamada al LLM por PDF leído o, como en el caso de los chunks, sería
  >   recomendable hacer una llamada con la información acumulada de n documentos? Y si es así,
  >   ¿cuál sería el valor recomendado de n?
  >
  > - Como observación sobre la última clase, coincido con el instructor en que el contenido era
  >   demasiado para una sola sesión. Me hubiese gustado que hubiese habido tiempo para comentar
  >   un poco más el código y verlo en ejecución. La parte de la pipeline de extracción y limpieza
  >   de datos creo que nos puede servir para multitud de tipos de proyectos y la vi interesante.
  >   Y la parte de Alembic y la BBDD en Postgres no se explica apenas en el material de la lección
  >   y del ejercicio, y hubiese estado bien alguna pequeña explicación durante la sesión en vivo.
  >
  > - Otra duda que quería trasladar, que no sé si es mito o leyenda... A la hora de extraer
  >   información de un documento con un LLM, ¿es útil incluir un índice al inicio del documento
  >   para ayudar al LLM a extraer la información con mayor rapidez/exactitud?

**Resumen de lo que pide:**

1. Extracción masiva con LLM: ¿una llamada por documento o agrupar *n* documentos por llamada?
   ¿Qué *n*?
2. *Feedback*: la S6 fue demasiado contenido; quería más código en ejecución y una explicación de
   **Alembic y Postgres**.
3. ¿Ayuda poner un **índice al principio** del documento para que el LLM extraiga mejor?

---

## 3. Qué respondemos (pendiente)

- [ ] Decidir qué se contesta en directo y en qué momento de la clase.
