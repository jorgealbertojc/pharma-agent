# 🧪 Pharma Agent Lab - lab.jorgealberto.jaime.pharma

Laboratorio para construir un agente conversacional farmacéutico con RAG, memoria persistente e inventario en tiempo real. El sistema integra **Ollama**, **Pinecone**, **Redis**, **LangChain** y **LangGraph** para ofrecer respuestas contextuales, sugerencias de sobreventa y consultas sobre medicamentos.

---

## 🚀 Requisitos

- Docker y Docker Compose
- Python 3.12+
- GPU NVIDIA (opcional, para aceleración de Ollama)
- Git (para clonar el repositorio)

---

## 📁 Estructura del proyecto

```
pharma-agent/
├── .env                         # Variables de entorno (configuración)
├── .gitignore
├── pyproject.toml               # Dependencias y configuración del proyecto
├── README.md                    # Este archivo
├── docker-compose.yml           # Servicios: ollama, pinecone, redis, webdis
│
├── docker/                      # Archivos de configuración para contenedores
│   └── webdis.json              # Configuración de Webdis (apunta a Redis)
│
├── src/                         # Código fuente principal
│   ├── __init__.py
│   │
│   ├── core/                    # Capa fundamental
│   │   ├── __init__.py
│   │   ├── config.py            # Configuración con Pydantic Settings
│   │   ├── enums.py             # Enums (Environments, LogLevels, IndexMetric)
│   │   ├── models.py            # Modelos de datos (Medicamento, Inventario, etc.)
│   │   └── exceptions.py        # Excepciones personalizadas
│   │
│   ├── rag/                     # Sistema de RAG (documentos externos)
│   │   ├── __init__.py
│   │   ├── embeddings.py        # Configuración de embeddings (Ollama)
│   │   ├── indexer.py           # Indexación de documentos en Pinecone
│   │   ├── retriever.py         # Recuperación de contexto
│   │   └── prompts.py           # Templates de prompts RAG
│   │
│   ├── inventory/               # Conector a Google Sheets (inventario)
│   │   ├── __init__.py
│   │   ├── client.py            # Conexión a Google Sheets API
│   │   ├── schema.py            # Mapeo de columnas a modelos Pydantic
│   │   ├── cache.py             # Cache en Redis para evitar saturar la API
│   │   └── updates.py           # (Opcional) Webhooks para actualizaciones
│   │
│   ├── memory/                  # Memoria conversacional (persistente)
│   │   ├── __init__.py
│   │   ├── base.py              # Interfaz abstracta BaseMemory
│   │   ├── buffer.py            # Memoria en RAM (BufferMemory)
│   │   └── persistent.py        # Memoria persistente con Redis (PersistentMemory)
│   │
│   ├── tools/                   # Herramientas para el agente (LangChain Tools)
│   │   ├── __init__.py
│   │   ├── search_inventory.py  # Buscar en inventario (nombre/marca)
│   │   ├── search_docs.py       # Buscar en RAG (libros/documentos)
│   │   ├── suggest_upsell.py    # Sugerir productos relacionados
│   │   └── format_response.py   # Formatear respuesta (Markdown/estructurado)
│   │
│   ├── agent/                   # Orquestador con LangGraph
│   │   ├── __init__.py
│   │   ├── graph.py             # Definición del grafo de LangGraph
│   │   ├── nodes.py             # Nodos del grafo (tool calling, memory, etc.)
│   │   ├── state.py             # Estado compartido del agente
│   │   └── executor.py          # Loop principal (interacción con usuario)
│   │
│   └── entrypoints/             # Puntos de entrada al sistema
│       ├── __init__.py
│       ├── cli.py               # Línea de comandos (agente interactivo)
│       └── api.py               # (Futuro) API REST con FastAPI
│
├── tests/                       # Pruebas unitarias e integración
│   ├── unit/
│   │   ├── test_config.py       # Tests de configuración
│   │   ├── test_memory.py
│   │   └── ...
│   └── integration/
│       ├── test_rag.py
│       └── test_agent.py
│
├── scripts/                     # Utilidades administrativas
│   ├── setup_index.py           # Indexa documentos en Pinecone (ejecución única)
│   ├── seed_inventory.py        # Carga inicial de inventario (mock o real)
│   └── clean_redis.py           # Limpieza de sesiones expiradas en Redis
│
└── docs/                        # Documentación del proyecto
    ├── architecture.md
    ├── api_reference.md
    └── deployment.md
```

---

## ⚙️ Configuración

1. **Clona el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd pharma-agent
   ```

2. **Crea el archivo `.env`** (copia de `.env.example` o con los valores por defecto)
   ```env
   # Entorno y logs
   AGENT_ENVIRONMENT=development
   AGENT_LOG_LEVEL=INFO
   AGENT_NAME=pharma-assistant

   # Ollama / Modelos
   IA_MODEL_HOST=http://localhost:11434
   IA_MODEL_EMBEDDED_NAME=nomic-embed-text
   IA_MODEL_AGENT_NAME=llama3.2
   IA_MODEL_API_KEY=
   IA_MODEL_TEMPERATURE=0.0

   # Pinecone
   PINECONE_HOST=http://localhost:5081
   PINECONE_INDEX_NAME=lab
   PINECONE_INDEX_DIMENSIONS=768
   PINECONE_INDEX_METRIC=cosine

   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB_INDEX=0
   REDIS_TTL_SECONDS=   # vacío o None = sin expiración
   ```

3. **Levanta los servicios con Docker Compose**
   ```bash
   docker-compose up -d
   ```
   Esto inicia:
   - **Ollama** (servidor de modelos LLM)
   - **Pinecone** (índice vectorial para RAG)
   - **Redis** (persistencia de memoria y caché)
   - **Webdis** (API HTTP para Redis)

4. **Verifica que todos los contenedores estén saludables**
   ```bash
   docker-compose ps
   ```

5. **Instala las dependencias de Python** (usando `uv` o `pip`)
   ```bash
   uv sync
   # o
   pip install -e .
   ```

---

## 🧪 Uso básico

### Indexar documentos (libro) en Pinecone
```bash
uv run python -m scripts.setup_index
```

### Ejecutar el agente en modo CLI
```bash
uv run python -m src.entrypoints.cli
```

### Ejecutar pruebas unitarias
```bash
uv run python -m pytest tests/unit/ -v
```

---

## 📦 Dependencias principales

- `pydantic-settings` – Configuración tipada y validación.
- `langchain`, `langchain-community`, `langgraph` – Orquestación de cadenas y agentes.
- `langchain-pinecone` – Integración con Pinecone.
- `langchain-ollama` – Integración con Ollama.
- `redis` – Cliente Redis para persistencia.
- `pinecone-client` – Cliente para Pinecone (local).
- `google-api-python-client` – Conexión a Google Sheets (futuro).
- `pytest` – Tests unitarios e integración.

---

## 🧠 Arquitectura resumida

1. **Configuración** (`src/core/config.py`) – Carga variables de entorno y expone `settings`.
2. **RAG** (`src/rag/`) – Indexa documentos en Pinecone y recupera fragmentos relevantes.
3. **Memoria** (`src/memory/`) – Almacena historial conversacional (en RAM o persistente en Redis).
4. **Inventario** (`src/inventory/`) – Conector a Google Sheets con caché en Redis.
5. **Herramientas** (`src/tools/`) – Funciones que el agente puede invocar (buscar inventario, RAG, upsell).
6. **Agente** (`src/agent/`) – Orquestador con LangGraph que decide qué herramienta usar en cada turno.
7. **Puntos de entrada** (`src/entrypoints/`) – CLI y (futura) API REST.

---

## 🔄 Próximos pasos

- [ ] Desarrollar el conector a Google Sheets (`inventory/client.py`).
- [ ] Implementar las herramientas (`tools/search_inventory.py`, `tools/search_docs.py`).
- [ ] Construir el grafo del agente con LangGraph (`agent/graph.py`).
- [ ] Añadir tests de integración para el flujo completo.
- [ ] Crear una interfaz web (FastAPI + Streamlit) para demostración.

---

## 📄 Licencia

Este proyecto es un laboratorio educativo. Todos los derechos reservados.

---

**Hecho con ❤️ para aprender y construir un agente farmacéutico útil.**
