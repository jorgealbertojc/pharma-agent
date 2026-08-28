"""
Configuración del modelo de embeddings para RAG.

Este módulo proporciona una función para obtener el modelo de embeddings
configurado con los parámetros del archivo .env (host y modelo).
"""

from langchain_ollama import OllamaEmbeddings
from app.core.config import settings


def get_embeddings() -> OllamaEmbeddings:
    """
    Retorna una instancia de OllamaEmbeddings configurada con las variables de entorno.

    Returns:
        OllamaEmbeddings: Objeto listo para generar embeddings.

    Raises:
        ValueError: Si el modelo de embeddings no está configurado en .env.
    """
    if not settings.IA_MODEL_EMBEDDED_NAME:
        raise ValueError("IA_MODEL_EMBEDDED_NAME no está definido en la configuración.")

    return OllamaEmbeddings(
        model=settings.IA_MODEL_EMBEDDED_NAME,
        base_url=settings.IA_MODEL_HOST,
    )
