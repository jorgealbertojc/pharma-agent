# app/rag/__init__.py
"""
Módulo RAG para indexación y consulta de documentos.

Este módulo proporciona una interfaz limpia para:
- Indexar documentos de texto en Pinecone (vectorstore)
- Realizar consultas RAG (Recuperación + Generación) sobre el índice

Uso básico:
    import rag

    # Indexar un documento
    rag.index(file_path="documents/libro.txt")

    # Consultar
    respuesta = rag.query("¿Quién es el protagonista?")
    print(respuesta)
"""

from .index import index_document
from .query import query

# ------------------------------------------------------------
# Funciones públicas del módulo (alias para facilitar el uso)
# ------------------------------------------------------------

def index(file_path, **kwargs):
    """
    Índice un documento en Pinecone.

    Args:
        file_path: Ruta al archivo de texto.
        **kwargs: Parámetros adicionales para index_document:
            - chunk_size: int (por defecto 500)
            - chunk_overlap: int (por defecto 50)
            - pinecone_host: str (opcional)
            - pinecone_index_name: str (opcional)
            - ollama_host: str (opcional)
            - embedding_model: str (opcional)

    Returns:
        int: Número de fragmentos indexados.
    """
    return index_document(file_path, **kwargs)


# Exponer explícitamente lo que se puede importar con "from rag import *"
__all__ = [
    "index",
    "query",
    "index_document",  # Por si alguien quiere la función completa
]
