# lab.jorgealberto.jaime.pharma

## Directory and Files strcuture

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
