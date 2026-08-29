# Guion del curso — listado de sesiones

Índice del máster: 17 entradas (sesión 0 de bienvenida + 16 sesiones + proyecto
final), organizadas en 6 módulos. La nota larga de cada sesión va en su carpeta
(`s12/`, ...).

| # | Sesión | Módulo | Descripción |
|---|--------|--------|-------------|
| 00 | Bienvenida | Pre-curso | Presentación del programa y del rol de AI Engineer, metodología (flipped classroom), stack tecnológico y configuración del entorno: local, Google Colab y las APIs y modelos que se usan todo el curso. |
| 01 | LLMs y setup de entorno de trabajo | M1 · Fundamentos de productos con IA | Primeras llamadas por API a OpenAI, Anthropic y Gemini: estructura de una llamada, parámetros de los modelos de razonamiento, tokenización avanzada y comparativa de modelos 2026. |
| 02 | Primeros pasos de arquitectura CAG | M2 · Arquitecturas CAG | Nace el proyecto (scaffolding FastAPI) y la arquitectura CAG: qué es Cache Augmented Generation, gestión efectiva de contexto y arquitectura de conversaciones con modelos. |
| 03 | Patrones de diseño para wrappers de modelos | M2 · Arquitecturas CAG | El wrapper del LLM como pieza central: abstracción de proveedores con fallback, cacheo inteligente de respuestas, streaming de respuestas largas y observabilidad/trazabilidad. |
| 04 | Productos IA avanzados | M2 · Arquitecturas CAG | Del chat a la interfaz de producto: plantillas de prompts desde backend, extracción de datos estructurados, guardrails de validación y cacheo semántico de respuestas. |
| 05 | Funcionalidades avanzadas | M2 · Arquitecturas CAG | Memoria conversacional vs historial, contexto dinámico de fuentes externas, prompts adaptativos por tier de usuario, testing/evaluación con LLMs y el patrón Actor-Critic-Boss. |
| 06 | Fundamentos de data-driven AI | M3 · Data-driven AI | Stress test del CAG para medir dónde rompe, auditoría e inventario de datos, pipeline de extracción multi-formato, limpieza/normalización y PII + GDPR en la ingesta. |
| 07 | Embeddings y representación vectorial | M3 · Data-driven AI | Del texto a la geometría semántica: qué son los embeddings, selección de modelos con sus trade-offs, y estrategias profesionales de chunking aplicadas a los presupuestos y transcripciones del proyecto. |
| 08 | Bases de datos vectoriales | M3 · Data-driven AI | Migración a pgvector y endpoint de búsqueda: por qué existen las BBDD vectoriales, anatomía de los índices (HNSW, IVFFlat, DiskANN), diseño de esquema y tuning hacia producción. |
| — | Proyecto Final Master AI Engineering | Proyecto final | El proyecto integrador del máster. |
| 09 | Fundamentos de RAG | M4 · Arquitectura RAG | Del CAG estático al flujo RAG: las cuatro etapas y por qué el retrieval domina, reformulación de queries, retrieval con threshold y filtros, augmentation y el retriever aislado como servicio securizado. |
| 10 | Técnicas de recuperación | M4 · Arquitectura RAG | Recuperación avanzada: reranking (y cómo medir si compensa), búsqueda híbrida, expansión y descomposición de consultas, multi-índice con routing y filtrado contextual/temporal. |
| 11 | RAG avanzado — generación y calidad | M4 · Arquitectura RAG | La mitad de generación: content augmentation, síntesis de fuentes que se contradicen, citación verificable, detección de alucinaciones, reindexación/versionado de embeddings y evaluación con RAGAS. |
| 12 | **Introducción a agentes de IA** | M5 · Orquestación de agentes | El salto de pipeline a agente: el modelo pasa a decidir el control de flujo. Function calling en la práctica (tools, schemas, contrato), el bucle agéntico paso a paso escrito a mano, patrones de diseño de tools y cuánto cuesta un agente. |
| 13 | Orquestación de agentes | M5 · Orquestación de agentes | Del bucle manual al grafo con LangGraph: StateGraph (nodos, aristas, estado), reducers y checkpointers para persistencia, paralelismo y enrutado condicional, manejo de errores y observabilidad (LangSmith/Logfire). |
| 14 | Sistemas multi-agente y patrones avanzados | M5 · Orquestación de agentes | Cuándo un multi-agente deja de ser "un grafo con más nodos": el supervisor construido a mano con Command, comunicación entre agentes, human-in-the-loop sobre el checkpointer, competición/síntesis y mínimo privilegio + auditoría. |
| 15 | Puesta en producción I — arquitectura e infra | M6 · Despliegue y producción | Qué entendemos por producción: partir en servicios, contenerización con Docker, documentación del sistema, CI/CD con tokens y despliegue en cloud. |
| 16 | Puesta en producción II — calidad y observabilidad | M6 · Despliegue y producción | LLMOps: golden set de producción, evaluación en producción y tratamiento de regresiones, un sistema que sabe decir "no lo sé", observabilidad, coste/latencia/A-B testing y modelos en local. |
