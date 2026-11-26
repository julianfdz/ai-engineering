# Cómo preparamos una clase del máster

Guía para Claude. Julián da sesiones sueltas del Máster en AI Engineering de LIDR, en varias ediciones a la vez
(2609, 2026-10…). Preparar una clase significa dejar montado y probado todo lo de **esa** sesión, con material para
proyectar, material para los alumnos y un guion propio. Respuestas en español; comandos en PowerShell, siempre
con su `cd`.

## Reglas fijas

| Regla | Por qué |
|---|---|
| El repo oficial `LIDR\ai-engineering` **no se toca nunca**. Todo va al fork `julianfdz/ai-engineering`. | Es de LIDR; el fork es nuestro. |
| El fork es **público**: nunca se suben `.env`, claves, emails ni material interno de LIDR (el Notion vive fuera de git, en `LIDR\edicion-26-09\`). | Cualquiera puede leerlo. |
| Solo se trabaja en **la sesión del día**: no se levantan ni se tocan contenedores ni ramas de otras sesiones. Leer el material de otra sesión para copiar el formato sí vale (se dice en una línea). | Lo pidió así; los stacks chocan entre sí. |
| **No usar su ordenador**: nada de computer-use ni clics en sus apps. Abrir con `code`, `start` o `Start-Process` sí vale; lo que haya que pulsar dentro, se le indica. | Trabaja a la vez y le roba el foco. |
| **No gastar en OpenAI sin decirlo.** Primero, demos que no llaman a un LLM y salidas reales ya guardadas. Si algo cuesta, se dice cuánto y se espera el sí. Recargar saldo es cosa suya. | No quiere sorpresas en la factura. |
| El material de alumnos (deck, PDF de comandos, cabeceras) va **sin comentarios internos** ni bromas. | Lo ven los alumnos. |
| Las **diapos originales de LIDR no se tocan**: ni orden, ni texto, ni diseño. Solo se les puede añadir la franja «En el código» / «En los tests». Lo nuestro va en una diapo nueva **justo detrás** de la original que amplía. | Julián prepara las clases con las grabaciones de otras ediciones, que usan las originales; si cambian, él y los alumnos pierden el hilo. |
| Sin tareas programadas ni servicios automáticos. | No los quiere. |
| Al terminar, **commit y push de todo** (rama local de la sesión y `main`). | «Súbelo todo». |

## Cuándo

- **El día antes** (o la mañana de la clase): el stack levantado y sano, las demos probadas y el material hecho. La
  primera build pesada de cada «era» de dependencias (torch) nunca cinco minutos antes.
- **Justo antes de clase**: abrir las ventanas (apartado 9).
- **Después de la clase**: `docker compose -p aieng-sNNlive down` (borra los contenedores y conserva los volúmenes) y
  actualizar la memoria de la sesión.

## Qué montamos, en orden

1. **Contexto.** Leer `sesiones/sNN/contexto-sesion-NN.md`, `guion-directo.md` (el guion oficial de LIDR), el
   Notion de la edición y la memoria de la sesión. Si ya se dio en otra edición, mover lo viejo a
   `sNN/anterior-<edición>/` con `git mv`. Situar la sesión respecto a las dos anteriores y las dos siguientes
   (índice en `sesiones/00-listado.md`).
2. **Entorno aislado.** Un worktree por sesión, `ai-engineering-fork-julian\ai-engineering-sNN`, en la rama
   `session_NN_live_local` (sale de `origin/session_NN_live`). Parches de Windows en esa rama:
   - Dockerfile con `TORCH_CPU_ONLY` y los modelos que haga falta (spaCy, NLTK);
   - `docker-compose.override.yml` con `container_name: sNN-*` y los montajes de `scripts/` y `evals/`;
   - `estimator-web/bin/*` en LF;
   - `.env` copiado y nunca commiteado.

   Se levanta con `docker compose -p aieng-sNNlive up -d --build` y después se pasa el pre-flight de la sesión. El
   `-p` da a cada sesión sus propios volúmenes; los datos de Docker viven en `D:\Docker\wsl`.
3. **Probar todas las demos** y guardar la salida real de cada una en `sNN/comandos/salidas/NN_*.txt`. Lo que no
   cuadre con el guion de LIDR (números, líneas, comportamientos) se anota en el contexto, en «Diferencias con el
   guion».
4. **Cabeceras en el código.** Cada fichero que se abre en clase lleva arriba una cabecera
   `# ── Sesión N · <título> ──…` en español, que explica para qué sirve. Va en un commit en la rama local.
   Después se recalculan las líneas que se citan, porque la cabecera las desplaza.
5. **Deck** (`sNN/deck/build_deck.py`, que sale en `SesionNN-Julian-Fernandez.pdf`).
   - **Motor:** el de la S2 o la S5 (`s02/deck/build_deck.py` añade la franja de tests; los dos usan el de la
     S7), con PyMuPDF sobre la plantilla de LIDR. ROTI y «Gracias» salen de la plantilla.
   - **Diapos originales:** las Google Slides oficiales de la sesión (enlace en el Notion), exportadas a PDF como
     `deck/plantilla-lidr-sNN.pdf`, entran **sin tocar** y en su orden; las nuestras, detrás de la que amplían
     (como en la S7). Si no hay acceso (piden la cuenta de LIDR), se dice y se monta el deck propio.
   - **Franja «En el código»:** en cada diapo de contenido, grande (11 pt), con `ruta`, función y línea,
     **verificadas con grep** contra la rama. Si la demo es en la web, empieza por «Interfaz: …».
   - **Franja «En los tests»** (debajo, en verde): el test que comprueba lo que cuenta la diapo, con fichero,
     nombre y línea. Más una diapo con todos los tests de la sesión y qué bloque cubre cada uno.
   - **Diapo «Para qué sirve hoy y dónde encaja»** justo después de «Hoy»: las dos sesiones anteriores y las dos
     siguientes en una línea de tiempo, el propósito de la sesión y por qué ahora (como en la S7 de la 2026-10).
   - **Diapo «El ejercicio previo»** (la primera tras la portada, antes de «Hoy»): el objetivo en dos líneas, las
     reglas y, en lista, los pasos o ficheros que había que implementar, cada uno con su fichero y línea en la rama
     de clase. Sale del enunciado de la plataforma o del Notion; si no se tiene, pedirle a Julián el enlace del post.
     No se resuelve el ejercicio en clase: la diapo es para situar.
   - **Capturas:** reales, en `curso-master/assets/sNN-*.png`.
   - **Revisión:** renderizar las páginas y mirarlas antes de darlo por bueno.
6. **PDF de comandos para alumnos** (`sNN/comandos/build_comandos.py`): genera un HTML y Edge headless lo pasa a
   PDF con `--print-to-pdf`; sale en `SNN-comandos-y-salidas.pdf`.
   - **Cada paso:** «Para qué sirve», el comando (genérico, sin nuestro `-p`, con alternativa en PowerShell), la
     salida real, «Cómo leerla» y «Lo comprueba» (el comando del test relacionado). Una sección propia para
     ejecutar los tests. Tono formal: es un documento de referencia, no una chuleta ni habla a Julián.
   - **Salidas de pago, una sola vez:** cada respuesta completa se guarda en `salidas/NN_*.json` y no se repite;
     con ellas se genera además una página `historico-sNN.html` para enseñarlas en clase.
   - **Probar también los comandos de PowerShell** (con una petición que dé 422, que es gratis).
   - **«Prueba tú»:** ejercicios ejecutados de verdad, con su salida.
   - **Peso:** el despliegue va breve; los ejemplos y su comentario, desarrollados.
7. **Guion propio** (`sNN/guion-julian.md`): diapo a diapo, con los comandos de PowerShell probados con
   `-p aieng-sNNlive`, qué fichero y qué línea abrir en VS Code, qué sale en cada demo y una tabla «Si algo falla».
8. **Web.** Si la sesión tiene interfaz en Rails, comprobar si la web oficial cubre las demos. Si no, se añaden en la
   rama local menús o presets: Demo presets en la S5, Búsqueda / Corpus / Histórico en la S10, Calidad en la S11. Si
   una demo es lenta o cuesta, se precarga un histórico para enseñarlo, con permiso. Si no hay nada en la web, la
   interfaz es el Swagger (`http://localhost:8000/docs`).
9. **Abrir antes de clase:**
   - VS Code con la carpeta del worktree y los ficheros **en el orden de la clase**, cada uno en su línea:
     `code . -g fichero:línea fichero:línea …`;
   - el deck y el PDF de comandos;
   - la web o el Swagger, con las pestañas del histórico si lo hay.
10. **Subir.** Commit y push de la rama local (worktree) y de `main` (materiales). Si un pptx o un PDF grande da
    HTTP 408: `git -c http.postBuffer=524288000 push`.
11. **Memoria.** Actualizar la nota de la sesión (`lidr-sNN-local.md`) y su línea en `MEMORY.md`: worktree,
    proyecto, comportamientos reales de las demos y estado del stack.

## Estructura de cada sesión (`curso-master/sesiones/sNN/`)

| Fichero | Qué es | Lo ven |
|---|---|---|
| `contexto-sesion-NN.md` | Descripción oficial, ejercicio previo, artículos y diferencias reales con el guion | Julián |
| `guion-directo.md` | Guion oficial de LIDR | Julián |
| `guion-julian.md` | Guion propio, diapo a diapo | Julián |
| `deck/build_deck.py` → `SesionNN-Julian-Fernandez.pdf` | Diapos | Alumnos |
| `comandos/build_comandos.py` + `salidas/` → `SNN-comandos-y-salidas.pdf` | Comandos con salida real | Alumnos |
| `anterior-<edición>/` | Material de una edición anterior | — |

## Trampas conocidas (Windows + Docker)

- **Docker Desktop no arranca por un `.sock.stale`:** matar los procesos de Docker y renombrar a la vez
  `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`. Nunca «Reset to factory defaults».
- **Rails muere con `ruby\r`:** los `bin/*` están en CRLF; pasarlos a LF.
- **`UnicodeEncodeError` (cp1252) en Python:** usar `PYTHONUTF8=1`.
- **PowerShell 5.1 rompe tildes y comillas al llamar a `curl`:** usar `curl.exe --form-string` y textos sin tildes.
- **Edge pinta una cuadrícula blanca sobre los PDF según el zoom** (costuras entre baldosas de 200 px): es Edge, sale
  hasta con páginas que son una sola imagen. Los decks y el PDF de comandos se abren y se proyectan en **Chrome**.
- **`Get-Content -Raw` + `ConvertTo-Json` en PowerShell 5.1** mete propiedades ocultas (`PSPath`…) en el JSON:
  leer con `[IO.File]::ReadAllText(...)` y enviar el body como bytes UTF-8.
- **El `/health` falla justo después de tocar código:** es la recarga de uvicorn; repetir a los 10 s.
- **Choques de nombres y puertos:** no levantar dos stacks de la misma era a la vez (los `container_name` y los
  puertos son fijos).
