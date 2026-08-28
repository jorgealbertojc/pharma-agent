# src/rag/retriever.py
"""
Recuperador de documentos desde Pinecone.
"""

from typing import List, Optional, Any, Union

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from app.core.config import settings as default_settings
from app.rag.embeddings import get_embeddings
from app.rag.enums import SearchType


class Retriever:
    """
    Recuperador de fragmentos relevantes desde Pinecone.

    Args:
        k: Número de fragmentos a recuperar (top-k). Default 4.
        search_type: Estrategia de búsqueda (ver SearchType).
        score_threshold: Umbral mínimo de puntuación (solo para SIMILARITY_SCORE_THRESHOLD).
        fetch_k: Número de documentos a recuperar inicialmente (solo para MMR).
        lambda_mult: Factor de diversidad en MMR (0 = máximo diversidad, 1 = máxima similitud).
        embeddings: Modelo de embeddings (si no se pasa, se usa el de configuración).
        settings: Instancia de Settings (si no se pasa, se usa la global).
    """

    def __init__(
        self,
        k: int = 4,
        search_type: SearchType = SearchType.SIMILARITY,
        score_threshold: Optional[float] = None,
        fetch_k: Optional[int] = None,
        lambda_mult: float = 0.5,
        embeddings: Optional[Any] = None,
        settings = None,
    ):
        self.k = k
        self.search_type = search_type
        self.score_threshold = score_threshold
        self.fetch_k = fetch_k
        self.lambda_mult = lambda_mult
        self.settings = settings or default_settings

        # Validar configuración necesaria
        if not self.settings.PINECONE_HOST:
            raise ValueError("PINECONE_HOST no está definido en la configuración.")
        if not self.settings.PINECONE_INDEX_NAME:
            raise ValueError("PINECONE_INDEX_NAME no está definido en la configuración.")

        # Inicializar embeddings
        self.embeddings = embeddings if embeddings is not None else get_embeddings()

        # Conectar con Pinecone
        pinecone = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        self.index = pinecone.Index(host=self.settings.PINECONE_HOST)

        # Crear el vectorstore
        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
        )

        # Construir search_kwargs según el tipo
        search_kwargs = {"k": self.k}

        if self.search_type == SearchType.SIMILARITY_SCORE_THRESHOLD:
            if self.score_threshold is None:
                raise ValueError(
                    "score_threshold es obligatorio para search_type='similarity_score_threshold'"
                )
            search_kwargs["score_threshold"] = self.score_threshold

        if self.search_type == SearchType.MMR:
            if self.fetch_k is not None:
                search_kwargs["fetch_k"] = self.fetch_k
            if self.lambda_mult is not None:
                search_kwargs["lambda_mult"] = self.lambda_mult

        # Construir el retriever de LangChain
        self.retriever = self.vectorstore.as_retriever(
            search_type=self.search_type.value,  # <- Convertimos a string para LangChain
            search_kwargs=search_kwargs,
        )

    def retrieve(self, query: str) -> List[Document]:
        """Recupera fragmentos relevantes."""
        if not query or not query.strip():
            return []
        return self.retriever.invoke(query)

    def retrieve_with_scores(self, query: str) -> List[tuple[Document, float]]:
        """Recupera fragmentos con puntuaciones (solo para SIMILARITY)."""
        if self.search_type != SearchType.SIMILARITY:
            raise ValueError(
                f"retrieve_with_scores solo está disponible con search_type='similarity'. "
                f"Actual: {self.search_type}"
            )
        if not query or not query.strip():
            return []
        return self.vectorstore.similarity_search_with_score(query, k=self.k)

    def retrieve_as_context(self, query: str) -> str:
        """Recupera y formatea como texto plano."""
        docs = self.retrieve(query)
        if not docs:
            return "No se encontró información relevante."
        return "\n\n".join([doc.page_content for doc in docs])
