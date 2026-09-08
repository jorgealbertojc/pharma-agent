"""
OpenSearch vector store for RAG using LangChain.

This module provides a wrapper around OpenSearchVectorSearch from LangChain,
replacing Pinecone as the vector database for document retrieval.
"""

from typing import Optional, List, Any

from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from opensearchpy import OpenSearch, RequestsHttpConnection

from app.core.config import settings
from app.core.exceptions import RAGError


class OpenSearchVectorStore:
    """
    Vector store using OpenSearch via LangChain.

    Args:
        index_name: Name of the OpenSearch index.
        embedding: Embedding function (e.g., from Ollama or Bedrock).
        endpoint_url: Full URL of the OpenSearch endpoint (e.g., http://localhost:9400).
        http_auth: Optional authentication tuple (user, password) or (access_key, secret_key).
        use_ssl: Whether to use SSL (default False for local).
        verify_certs: Whether to verify SSL certificates (default False for local).
        dimensions: Vector dimensions (must match embedding model).
        metric: Similarity metric (cosine, euclidean, dotproduct).
    """

    def __init__(
        self,
        index_name: str,
        embedding: Any,
        endpoint_url: str,
        http_auth: Optional[tuple] = None,
        use_ssl: bool = False,
        verify_certs: bool = False,
        dimensions: Optional[int] = None,
        metric: str = "cosine",
    ):
        self.index_name = index_name
        self.embedding = embedding
        self.endpoint_url = endpoint_url
        self.http_auth = http_auth
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.dimensions = dimensions or settings.OPENSEARCH_INDEX_DIMENSIONS
        self.metric = metric or settings.OPENSEARCH_INDEX_METRIC

        self._vector_store: Optional[OpenSearchVectorSearch] = None

    def _get_client(self) -> OpenSearchVectorSearch:
        """Lazy initialization of the vector store client."""
        if self._vector_store is None:
            self._vector_store = OpenSearchVectorSearch(
                opensearch_url=self.endpoint_url,
                index_name=self.index_name,
                embedding_function=self.embedding,
                http_auth=self.http_auth,
                use_ssl=self.use_ssl,
                verify_certs=self.verify_certs,
                connection_class=RequestsHttpConnection,
            )
        return self._vector_store

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        try:
            vector_store = self._get_client()
            ids = vector_store.add_documents(documents)
            return ids
        except Exception as e:
            raise RAGError(f"Failed to add documents to OpenSearch: {e}") from e

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        score_threshold: Optional[float] = None,
    ) -> List[Document]:
        """Perform similarity search."""
        try:
            vector_store = self._get_client()
            if score_threshold is not None:
                docs = vector_store.similarity_search_with_relevance_scores(
                    query, k=k, score_threshold=score_threshold
                )
                return [doc for doc, _ in docs]
            return vector_store.similarity_search(query, k=k)
        except Exception as e:
            raise RAGError(f"Failed to perform similarity search: {e}") from e

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple[Document, float]]:
        """Perform similarity search with scores."""
        try:
            vector_store = self._get_client()
            return vector_store.similarity_search_with_relevance_scores(query, k=k)
        except Exception as e:
            raise RAGError(f"Failed to perform similarity search with scores: {e}") from e

    def delete_index(self) -> None:
        """Delete the entire index."""
        try:
            vector_store = self._get_client()
            vector_store.delete_index()
        except Exception as e:
            raise RAGError(f"Failed to delete OpenSearch index: {e}") from e

    def index_exists(self) -> bool:
        """Check if the index exists."""
        try:
            vector_store = self._get_client()
            return vector_store.index_exists()
        except Exception:
            return False
