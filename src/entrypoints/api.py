# src/entrypoints/api.py
"""
API REST para el agente farmacéutico.

Expone el agente como un servicio web utilizando FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import AppException, AgentError
from src.core.models import QueryRequest, AgentResponse, ErrorResponse
from src.agent.executor import AgentExecutor
from src.agent.state import create_initial_state, add_message_to_state
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Dependencias globales (singleton)
# ------------------------------------------------------------

_executor: Optional[AgentExecutor] = None


def get_executor() -> AgentExecutor:
    """
    Retorna la instancia global del ejecutor del agente.
    Se inicializa una sola vez al arrancar la API.
    """
    global _executor
    if _executor is None:
        logger.info("Inicializando AgentExecutor...")
        _executor = AgentExecutor()
    return _executor


# ------------------------------------------------------------
# Lifespan (manejo de inicio/cierre)
# ------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Configura el ciclo de vida de la aplicación.
    """
    # Inicializar el agente al arrancar
    logger.info("Iniciando API del agente farmacéutico...")
    executor = get_executor()
    logger.info("AgentExecutor inicializado correctamente.")
    yield
    # Limpieza al cerrar (opcional)
    logger.info("Cerrando API...")


# ------------------------------------------------------------
# Aplicación FastAPI
# ------------------------------------------------------------

app = FastAPI(
    title="Pharma Agent API",
    description="API para consultar al agente farmacéutico con capacidades RAG, inventario y sugerencias.",
    version="0.0.4",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Maneja errores de validación de Pydantic y devuelve 400 en lugar de 422.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Error de validación", "errors": errors},
    )


# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------

@app.get(
    "/health",
    summary="Verificar estado del servicio",
    description="Retorna el estado de la API y del agente subyacente.",
    response_model=dict,
    tags=["Health"],
)
async def health_check() -> dict:
    """
    Endpoint de salud para verificar que la API está funcionando.
    """
    try:
        executor = get_executor()
        status_ok = executor.graph is not None
        return {
            "status": "ok" if status_ok else "degraded",
            "agent_ready": status_ok,
            "version": app.version,
        }
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agente no disponible",
        )


@app.post(
    "/query",
    summary="Consultar al agente farmacéutico",
    description="Envía una pregunta al agente y recibe una respuesta estructurada con contexto.",
    response_model=AgentResponse,
    responses={
        200: {"description": "Respuesta exitosa", "model": AgentResponse},
        400: {"description": "Error de validación", "model": ErrorResponse},
        500: {"description": "Error interno del servidor", "model": ErrorResponse},
    },
    tags=["Agent"],
)
async def query(request: QueryRequest) -> AgentResponse:
    """
    Procesa una consulta del usuario y retorna la respuesta del agente.

    Args:
        request: Objeto con la pregunta y session_id opcional.

    Returns:
        AgentResponse con la respuesta generada.

    Raises:
        HTTPException: Si ocurre un error durante el procesamiento.
    """
    try:
        executor = get_executor()

        # Si no hay estado, inicializarlo (o usar session_id para persistencia)
        if executor.state is None:
            executor.state = create_initial_state("")

        # Si se proporciona session_id, se podría usar para cargar estado previo (pendiente de implementación)
        # Por ahora, se mantiene el estado en memoria durante la sesión de la API.

        # Procesar la pregunta
        question = request.question.strip()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pregunta no puede estar vacía.",
            )

        # Añadir mensaje del usuario al historial
        executor.state = add_message_to_state(executor.state, HumanMessage(content=question))
        executor.state["question"] = question
        executor.state["final_answer"] = None
        executor.state["error"] = None
        executor.state["context"] = None
        executor.state["inventory_results"] = None
        executor.state["suggestions"] = None
        executor.state["next_step"] = None
        executor.state["iterations"] = 0

        # Invocar el grafo
        result_state = executor.graph.invoke(
            executor.state,
            config={"configurable": {"thread_id": request.session_id or "default"}},
        )
        executor.state = result_state

        final_answer = result_state.get("final_answer")
        error = result_state.get("error")
        context = result_state.get("context")
        inventory_results = result_state.get("inventory_results")
        suggestions = result_state.get("suggestions")

        if final_answer:
            # Añadir respuesta al historial
            executor.state = add_message_to_state(
                executor.state,
                AIMessage(content=final_answer)
            )
            return AgentResponse(
                answer=final_answer,
                sources=[context] if context else None,
                suggestions=suggestions,
                inventory_results=inventory_results,
                error=None,
            )
        else:
            error_msg = error or "No se pudo generar una respuesta."
            return AgentResponse(
                answer="Lo siento, no pude procesar tu pregunta.",
                error=error_msg,
            )

    except AppException as e:
        logger.error(f"Error de aplicación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(error=e.message, details=e.details).model_dump(),
        )
    except Exception as e:
        logger.exception("Error inesperado en /query")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Error interno del servidor",
                details=str(e),
            ).model_dump(),
        )


# ------------------------------------------------------------
# Ejecución directa (para desarrollo)
# ------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.entrypoints.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
