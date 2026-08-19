# lab.jorgealberto.jaime.pharma

## Estructura de Archivos y Documentos

### Estructura de Archivos

```text
.
├── .env
├── .gitignore
├── pyproject.toml
├── README.md
├── docker-compose.yml          # Redis + Pinecone + Ollama
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                   # Capa fundamental
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings
│   │   ├── models.py           # Pydantic models (Medicamento, Inventario, etc.)
│   │   └── exceptions.py       # Excepciones personalizadas
│   │
│   ├── rag/                    # RAG (lectura de documentos externos)
│   │   ├── __init__.py
│   │   ├── indexer.py          # Indexa documentos en Pinecone
│   │   ├── retriever.py        # Recuperación de contexto
│   │   ├── embeddings.py       # Configuración de embeddings
│   │   └── prompts.py          # Templates de prompts RAG
│   │
│   ├── inventory/              # Conector a Google Sheets
│   │   ├── __init__.py
│   │   ├── client.py           # Conexión a Google Sheets API
│   │   ├── schema.py           # Mapeo de columnas a modelos Pydantic
│   │   ├── cache.py            # Cache de inventario en Redis (evita saturar API)
│   │   └── updates.py          # (Opcional) Webhooks para actualizaciones
│   │
│   ├── memory/                 # Memoria persistente (ya tienes)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── buffer.py
│   │   └── persistent.py
│   │
│   ├── tools/                  # Herramientas para el agente (LangChain Tools)
│   │   ├── __init__.py
│   │   ├── search_inventory.py # Tool: buscar en inventario por nombre/marca
│   │   ├── search_docs.py      # Tool: buscar en RAG (libros/documentos)
│   │   ├── suggest_upsell.py   # Tool: sugerir productos relacionados
│   │   └── format_response.py  # Tool: formatear respuesta en Markdown/estructurado
│   │
│   ├── agent/                  # El orquestador (LangGraph/Agente)
│   │   ├── __init__.py
│   │   ├── graph.py            # Definición del grafo de LangGraph
│   │   ├── nodes.py            # Nodos del grafo (tool calling, memory, etc.)
│   │   ├── state.py            # Estado compartido del agente
│   │   └── executor.py         # Loop principal (interacción con usuario)
│   │
│   └── entrypoints/            # Puntos de entrada al sistema
│       ├── __init__.py
│       ├── cli.py              # Línea de comandos (como tu agente actual)
│       └── api.py              # (Futuro) API REST con FastAPI
│
├── tests/                      # Tests unitarios e integración
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_inventory.py
│   │   └── test_memory.py
│   └── integration/
│       ├── test_rag.py
│       └── test_agent.py
│
├── scripts/                    # Utilidades
│   ├── setup_index.py          # Indexa documentos (se ejecuta una vez)
│   ├── seed_inventory.py       # Carga inicial de inventario (mock o real)
│   └── clean_redis.py          # Limpieza de sesiones en Redis
│
└── docs/                       # Documentación del proyecto
    ├── architecture.md
    ├── api_reference.md
    └── deployment.md
```

### Descripción de Decisiones Claves

1. `src/core/` → Separación clara de configuraciones y modelos.

- `config.py` con Pydantic Settings (inmutable, validado).
- `models.py` define Medicamento, Inventario, Consulta, Respuesta. Esto centraliza el esquema de datos, crítico cuando integras Google Sheets y RAG.

2. `src/inventory/` → Aislado del RAG.

- El inventario es una fuente de datos completamente distinta al libro de texto (que está en Pinecone). Requiere su propio cliente, cache (para no saturar Google Sheets), y esquema de validación.
- El cache en Redis guarda el inventario completo con un TTL (ej. 5 minutos) para evitar consultas constantes a Google Sheets.

3. `src/tools/` → El corazón del agente.

- Cada herramienta es una función aislada que el agente puede invocar según la intención del usuario.
- `search_inventory.py`: Busca por nombre comercial o componente activo (usando fuzzy matching o embeddings).
- `search_docs.py`: Llama al RAG para preguntas sobre marcas, interacciones, etc.
- `suggest_upsell.py`: Usa reglas de negocio (ej. "si pide ibuprofeno, sugerir paracetamol").

4. `src/agent/` → Orquestación con LangGraph (no LangChain puro).

- LangGraph es el estándar para agentes con estado y toma de decisiones. El agente decide en cada turno qué herramienta usar (inventario, RAG, o responder directamente).
- `state.py` define el estado del agente: historial (de PersistentMemory), inventario cacheado, última herramienta usada.
- `executor.py` implementa el bucle que mencionaste: while True: pregunta → procesar → responder.

5. `src/entrypoints/` → Puertas de entrada desacopladas.

- `cli.py` es tu agente actual, pero ahora importa agent/executor.py. Si en el futuro añades una API, solo creas api.py sin tocar la lógica.

6. `scripts/` → Operaciones administrativas.

- `setup_index.py`: indexa documentos en Pinecone (ejecución única).
- `seed_inventory.py`: carga datos de prueba (o reales desde Google Sheets).
- `clean_redis.py`: utilidad para borrar sesiones expiradas.

7. `tests/` → Pruebas unitarias e integración.

- En producción, cada módulo debe tener tests. Esto asegura que el agente no falle al cambiar el esquema de Google Sheets o el modelo de embeddings.
