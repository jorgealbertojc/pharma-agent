# AGENTS.md

## Directrices para agentes de IA que contribuyen al proyecto Pharma Agent

Este documento define las reglas, convenciones y principios que los agentes (humanos o de IA) deben seguir al modificar, extender o mantener el código base de **Pharma Agent**. Estas reglas han sido extraídas de la evolución del proyecto y representan las decisiones de diseño adoptadas durante su desarrollo.

---

## 1. Principios generales

### 1.1. Separación de responsabilidades
- Cada módulo debe tener una única responsabilidad bien definida.
- No mezcles lógica de negocio con infraestructura (por ejemplo, no pongas lógica de RAG dentro de un endpoint de API).
- Usa inyección de dependencias para desacoplar módulos y facilitar pruebas.

### 1.2. Código limpio y legible
- Sigue las reglas de **Clean Code** (nombres descriptivos, funciones cortas, comentarios útiles, etc.).
- Documenta todas las funciones y clases con docstrings (formato Google o NumPy).
- Utiliza tipado fuerte (`typing`, `Optional`, `Union`, etc.) en todas las funciones y métodos.
- Usa `pydantic` para validación y modelos de datos.

### 1.3. Pruebas
- **No uses mocks para servicios externos** a menos que sea estrictamente necesario.
- Los tests de integración deben usar servicios reales (Ollama, Pinecone, Redis, Google Sheets) y ser autónomos (limpiar y poblar datos antes/después).
- Los tests deben seguir el patrón **Given / When / Then**.
- Los tests unitarios deben ser rápidos y no depender de servicios externos.

### 1.4. Commits y versionado
- Sigue **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, etc.).
- Los commits deben ser atómicos (una sola responsabilidad por commit).
- Las releases se versionan con `MAJOR.MINOR.PATCH` (SemVer).
- Las ramas de release se crean desde `develop` y se fusionan a `master` con `--no-ff`.

---

## 2. Estructura del proyecto

```
app/                         # Código fuente principal (renombrado desde src/)
├── agent/                   # Agente conversacional (LangGraph)
│   ├── executor.py          # Bucle interactivo y gestión de estado
│   ├── graph.py             # Definición del grafo LangGraph
│   ├── nodes.py             # Nodos del grafo (RAG, inventory, upsell, respuesta)
│   ├── state.py             # Estado del agente (TypedDict)
│   └── __init__.py          # Interfaz pública (con imports perezosos)
├── core/                    # Configuración, modelos y excepciones
│   ├── config.py            # Pydantic Settings (variables de entorno)
│   ├── models.py            # Modelos Pydantic (QueryRequest, AgentResponse, etc.)
│   ├── exceptions.py        # Jerarquía de excepciones personalizadas
│   └── enums.py             # Enums compartidos (Environments, LogLevels, etc.)
├── entrypoints/             # Puntos de entrada
│   ├── api.py               # API REST con FastAPI
│   ├── cli.py               # CLI interactivo y consulta única
│   └── __init__.py          # Exporta app y main
├── inventory/               # Inventario (Google Sheets, caché Redis)
│   ├── client.py            # Cliente Google Sheets
│   ├── cache.py             # Gestor de caché en Redis
│   ├── updates.py           # Orquestador de actualizaciones
│   ├── schema.py            # Modelos Pydantic (Medicamento, Inventario)
│   └── __init__.py
├── memory/                  # Memoria conversacional
│   ├── base.py              # Interfaz abstracta BaseMemory
│   ├── buffer.py            # Memoria en RAM
│   ├── persistent.py        # Memoria persistente con Redis
│   └── __init__.py
├── rag/                     # RAG (Indexación y recuperación)
│   ├── indexer.py           # Indexa documentos en Pinecone
│   ├── retriever.py         # Recupera fragmentos con soporte para MMR/threshold
│   ├── embeddings.py        # Configuración de embeddings (Ollama)
│   ├── prompts.py           # Gestor de prompts (RAGPrompt)
│   └── enums.py             # SearchType (similarity, mmr, threshold)
├── tools/                   # Herramientas para el agente
│   ├── format_response.py   # Formateo de respuestas (Markdown, JSON, texto)
│   ├── search_inventory.py  # Búsqueda en inventario
│   ├── search_docs.py       # Búsqueda en documentos (RAG)
│   ├── suggest_upsell.py    # Sugerencias de venta adicional
│   └── __init__.py
├── __init__.py              # Documentación del paquete
├── __main__.py              # Punto de entrada (`python -m app`)
└── py.typed                 # Marca el paquete como tipado (opcional)
```

---

## 3. Reglas específicas por módulo

### 3.1. Configuración (`core/config.py`)
- Usa `pydantic_settings.BaseSettings` con `SettingsConfigDict`.
- Todas las variables de entorno deben tener valores por defecto razonables.
- Las variables de entorno críticas (API keys, credenciales) deben validarse en tiempo de ejecución.
- El objeto `settings` es una instancia global inmutable (`frozen=True`).

### 3.2. RAG (`rag/`)
- **Indexer**: Usa `RecursiveCharacterTextSplitter` con `chunk_size` y `chunk_overlap` configurables.
- **Retriever**: Soporta `SearchType.SIMILARITY`, `SearchType.MMR` y `SearchType.SIMILARITY_SCORE_THRESHOLD`.
- Los tests de integración deben limpiar Pinecone antes de cada ejecución.
- **No uses `langchain-community`**; para cargar archivos de texto, usa Python estándar (`open`).

### 3.3. Memory (`memory/`)
- `BaseMemory` es una interfaz abstracta con métodos `add_message`, `get_messages`, `get_context`, `clear`, `get_token_count`.
- `BufferMemory` almacena en RAM con límites (`max_messages`, `max_tokens`).
- `PersistentMemory` usa Redis con inyección del cliente y `ttl` opcional.
- Los tests de integración deben crear y limpiar claves Redis únicas (`session_id` único).

### 3.4. Inventory (`inventory/`)
- **Client**: Obtiene datos de Google Sheets usando `gspread` y cuenta de servicio.
- Normaliza encabezados (quita espacios, maneja duplicados) antes de crear objetos `Medicamento`.
- **Cache**: Almacena en Redis con TTL configurable.
- **Updater**: Orquestador que decide entre caché y consulta a Google Sheets.
- Las credenciales y el ID de la hoja se configuran en `.env`.

### 3.5. Tools (`tools/`)
- **ResponseFormatter**: Métodos estáticos para formatear respuestas (Markdown, JSON, texto).
- **SearchInventory**: Busca por nombre, código, marca o categoría. Retorna objetos `Medicamento`.
- **SearchDocs**: Consulta RAG y formatea resultados (Markdown o JSON).
- **SuggestUpsell**: Usa reglas (categoría, principio activo, marca) para sugerir productos. Si no hay coincidencias, ofrece productos de respaldo (Electrolit, agua, jugo).
- **No usa IA directamente**; la IA se usa en el agente (orquestador).

### 3.6. Agent (`agent/`)
- **State**: `AgentState` es un `TypedDict` con campos `messages`, `question`, `context`, `inventory_results`, `suggestions`, `final_answer`, `error`, `next_step`, `iterations`.
- **Nodes**: `AgentNodes` recibe `retriever` e `inventory` por constructor. Cada nodo es un método que retorna un dict con campos del estado.
- **Graph**: `build_agent_graph(nodes)` construye el grafo LangGraph con los nodos y aristas.
- **Executor**: `AgentExecutor` maneja el bucle interactivo (CLI) y la invocación del grafo con `thread_id` en `config`.

### 3.7. Entrypoints (`entrypoints/`)
- **API**: FastAPI con endpoints `/health` y `/query`. Usa modelos de `core.models`. Maneja errores de validación con 400.
- **CLI**: Usa `argparse` para modo interactivo y consulta única.
- **Estado**: El estado del agente se mantiene en memoria durante la sesión de la API (se reinicia con cada test).

---

## 4. Estilo y formateo de código

- Usa **Black** para formateo automático (opcional, pero recomendado).
- Usa **Ruff** para linting y orden de imports.
- Límite de líneas: 120 caracteres.
- Orden de imports: estándar → terceros → locales.
- Usa f-strings en lugar de concatenación.
- Prefiere comprensiones de listas sobre bucles manuales cuando sea legible.
- Usa `pathlib.Path` en lugar de `os.path`.

---

## 5. Testing

- **Unit tests**: `tests/unit/` → no requieren servicios externos.
- **Integration tests**: `tests/integration/` → requieren servicios reales (Docker).
- **Fixtures**: Usa `tmp_path` para archivos temporales, y fixtures específicos para limpiar Pinecone, Redis, etc.
- **Marcas**: Usa `@pytest.mark.skip` para tests que no se pueden ejecutar en CI (ej. modo interactivo).
- **Cobertura**: Intenta mantener cobertura >80% en módulos críticos.

---

## 6. Gestión de dependencias

- Usa `uv` como gestor de dependencias.
- Las dependencias de producción van en `dependencies` en `pyproject.toml`.
- Las dependencias de desarrollo van en `dependency-groups.dev`.
- Añade nuevas dependencias con `uv add <paquete>` (o `uv add --dev <paquete>` para desarrollo).
- La versión de Python requerida es >=3.12.

---

## 7. Variables de entorno (`.env`)

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `AGENT_ENVIRONMENT` | `development`, `staging`, `production` | No (default: development) |
| `AGENT_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | No (default: INFO) |
| `IA_MODEL_HOST` | URL de Ollama | Sí |
| `IA_MODEL_EMBEDDED_NAME` | Modelo de embeddings | Sí |
| `IA_MODEL_AGENT_NAME` | Modelo de LLM para el agente | Sí |
| `IA_MODEL_TEMPERATURE` | Temperatura (0.0 - 1.0) | No (default: 0.0) |
| `PINECONE_HOST` | Host de Pinecone | Sí |
| `PINECONE_INDEX_NAME` | Nombre del índice | Sí |
| `PINECONE_INDEX_DIMENSIONS` | Dimensión de vectores | Sí |
| `PINECONE_INDEX_METRIC` | `cosine`, `euclidean`, `dotproduct` | No (default: cosine) |
| `REDIS_HOST` | Host de Redis | Sí |
| `REDIS_PORT` | Puerto de Redis | No (default: 6379) |
| `REDIS_DB_INDEX` | Índice de base de datos Redis | No (default: 0) |
| `REDIS_TTL_SECONDS` | TTL para caché (segundos) | No (default: None) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al archivo JSON de credenciales | Sí (para inventario) |
| `SPREADSHEET_ID` | ID del documento de Google Sheets | Sí (para inventario) |

---

## 8. Flujo de trabajo con Git

- `develop` es la rama principal de integración.
- `master` (o `main`) contiene el código estable, solo se actualiza mediante ramas de release.
- Las ramas de release se nombran `vX.Y.Z` y se fusionan a `master` con `--no-ff`.
- Los tags de release siguen `X.Y.Z` (sin la 'v').

---

## 9. Ejecución y comandos comunes

```bash
# Instalar dependencias
uv sync

# Levantar servicios
docker-compose up -d

# Ejecutar CLI interactivo
python -m app

# Ejecutar consulta única
python -m app --question "Ibuprofeno"

# Iniciar API
python -m app --api

# Ejecutar tests unitarios
pytest tests/unit/ -v

# Ejecutar tests de integración
pytest tests/integration/ -v

# Ejecutar tests específicos
pytest tests/integration/agent/test_nodes.py -v
```

---

## 10. Principios finales

- **No rompas la compatibilidad hacia atrás sin una buena razón y sin documentarlo** en las notas de release.
- **Las mejoras deben ir acompañadas de pruebas**. Si añades una funcionalidad, añade tests. Si corriges un bug, añade un test que lo reproduzca.
- **Mantén la documentación actualizada**. Si cambias el comportamiento, actualiza el README y las notas de release.
- **Sé minimalista**: no añadas dependencias ni funcionalidades que no sean necesarias. Prefiere soluciones simples sobre complejas.
