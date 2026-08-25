# src/rag/enums.py
"""
Enums específicos del módulo RAG (Recuperación Aumentada).
"""

from enum import Enum


class SearchType(str, Enum):
    """
    Estrategias de búsqueda soportadas por el retriever.

    - SIMILARITY: Búsqueda por similitud de coseno estándar.
    - MMR: Maximum Marginal Relevance. Diversifica los resultados.
    - SIMILARITY_SCORE_THRESHOLD: Filtra por puntuación mínima.
    """
    SIMILARITY: str = "similarity"
    MMR: str = "mmr"
    SIMILARITY_SCORE_THRESHOLD: str = "similarity_score_threshold"
