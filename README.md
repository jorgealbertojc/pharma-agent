# Pharma Agent

🤖 **Agente farmacéutico inteligente** con capacidades de RAG, búsqueda en inventario, sugerencias de venta adicional y memoria conversacional.

---

## 📦 Módulos completados

| Módulo | Descripción |
|--------|-------------|
| **Core** | Configuración centralizada (`pydantic-settings`), modelos de datos y jerarquía de excepciones personalizadas. |
| **RAG** | Indexación y recuperación de documentos (`Pinecone`, `Ollama` embeddings) con soporte para búsqueda por similitud, MMR y umbral de puntuación. |
| **Inventory** | Cliente para Google Sheets, caché en Redis, modelos Pydantic y orquestador de actualizaciones. |
| **Memory** | Memoria conversacional en RAM y persistente (Redis) con límites de mensajes y tokens. |
| **Tools** | Conjunto de herramientas: formateo de respuestas, búsqueda en inventario, búsqueda en documentos (RAG) y sugerencias de upsell. |
| **Agent** | Agente conversacional con LangGraph: nodos para RAG, inventario, upsell y generación de respuesta, con memoria persistente. |
| **Entrypoints** | API REST con FastAPI y CLI interactivo. |

---

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://gitlab.com/jorgealberto.jaime/pharma-agent.git
cd pharma-agent

# Crear entorno virtual e instalar dependencias
uv sync
```

---

## ⚙️ Configuración

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Ollama
IA_MODEL_HOST=http://localhost:11434
IA_MODEL_EMBEDDED_NAME=nomic-embed-text
IA_MODEL_AGENT_NAME=llama3.2
IA_MODEL_TEMPERATURE=0.0

# Pinecone (local)
PINECONE_HOST=http://localhost:5081
PINECONE_INDEX_NAME=rag-lab
PINECONE_INDEX_DIMENSIONS=768
PINECONE_INDEX_METRIC=cosine
PINECONE_API_KEY=pclocal

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_INDEX=0
REDIS_TTL_SECONDS=3600

# Google Sheets
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-sheets-key.json
SPREADSHEET_ID=1YdwowSe3lofJOV7mx1M6grMJEmWTAJ0kW1GfS239NBM
```

---

## 🐳 Servicios con Docker Compose

```bash
# Levantar todos los servicios
docker-compose up -d

# Verificar estado
docker-compose ps
```

Servicios incluidos:
- Ollama (servidor de modelos LLM)
- Pinecone (índice vectorial local)
- Redis (persistencia y caché)
- Webdis (API HTTP para Redis)

---

## 🧠 Uso del agente

### CLI interactivo

```bash
uv run python -m src.entrypoints.cli
```

### CLI con pregunta única

```bash
uv run python -m src.entrypoints.cli --question "¿Qué es el ibuprofeno?"
```

### API REST

```bash
# Iniciar el servidor FastAPI
uv run uvicorn src.entrypoints.api:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints disponibles:**
- `GET /health` → estado del servicio
- `POST /query` → consultar al agente

**Ejemplo de petición:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es la dosis de paracetamol?"}'
```

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
uv run python -m pytest tests/ -v

# Tests unitarios
uv run python -m pytest tests/unit/ -v

# Tests de integración
uv run python -m pytest tests/integration/ -v
```

---

## 📂 Estructura del proyecto

```
src/
├── agent/          # Agente conversacional con LangGraph
├── core/           # Configuración, modelos y excepciones
├── entrypoints/    # API REST y CLI
├── inventory/      # Cliente Google Sheets, caché, modelos
├── memory/         # Memoria conversacional (RAM/Redis)
├── rag/            # RAG: indexación, recuperación, embeddings
└── tools/          # Herramientas: formateo, búsquedas, upsell
```

---

## 🛠️ Tecnologías principales

- **LangChain**, **LangGraph** – Orquestación de agentes y RAG
- **Pydantic v2** – Validación y configuración
- **FastAPI** – API REST
- **Pinecone** – Índice vectorial local
- **Redis** – Caché y memoria persistente
- **Ollama** – Modelos LLM locales
- **Google Sheets API** – Inventario en tiempo real
- **pytest** – Tests unitarios e integración

---

## 📄 Licencia

Este proyecto es un laboratorio educativo. Todos los derechos reservados.

---

**Hecho con ❤️ para aprender y construir un agente farmacéutico útil.**
