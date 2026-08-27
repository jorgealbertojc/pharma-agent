# src/tools/search_docs.py
"""
Herramienta para buscar información en documentos (RAG).

Permite consultar la base de conocimiento externa (libros, prospectos, guías)
y obtener fragmentos relevantes para responder preguntas sobre medicamentos,
contraindicaciones, dosis, etc.
"""

from typing import List, Optional

from src.rag.retriever import Retriever
from .format_response import ResponseFormatter


class SearchDocs:
    """
    Buscador en documentos a través del sistema RAG.

    Args:
        retriever: Instancia del Retriever de RAG (inyectada).
        formatter: Instancia de ResponseFormatter (opcional, se crea por defecto).
    """

    def __init__(self, retriever: Retriever, formatter: Optional[ResponseFormatter] = None):
        self.retriever = retriever
        self.formatter = formatter or ResponseFormatter()

    def search(self, query: str) -> List[str]:
        """
        Busca fragmentos relevantes en los documentos indexados.

        Args:
            query: Texto de la pregunta o consulta.

        Returns:
            Lista de fragmentos de texto (cada uno es un Document.page_content).
            Si la consulta está vacía, retorna lista vacía.
        """
        query = query.strip()
        if not query:
            return []

        docs = self.retriever.retrieve(query)
        return [doc.page_content for doc in docs]

    def search_as_context(self, query: str) -> str:
        """
        Busca y devuelve el contexto concatenado como un solo texto.

        Args:
            query: Texto de la consulta.

        Returns:
            Contexto formateado como bloque de texto, listo para inyectar en un prompt.
            Si no hay resultados, retorna "No se encontró información relevante."
        """
        query = query.strip()
        if not query:
            return "No se encontró información relevante."

        return self.retriever.retrieve_as_context(query)

    def search_and_format(
        self,
        query: str,
        format_type: str = "markdown",
        max_items: Optional[int] = None,
        title: Optional[str] = None,
    ) -> str:
        fragments = self.search(query)
        if max_items:
            fragments = fragments[:max_items]

        if format_type == "json":
            return self.formatter.to_json({"query": query, "results": fragments})

        # Formato Markdown
        if not fragments:
            return self.formatter.to_markdown(
                "No se encontró información relevante en los documentos.",
                title=title or "Resultados de búsqueda",
            )

        title_block = f"## {title}\n\n" if title else ""
        items = "\n".join(f"- {fragment[:200]}..." for fragment in fragments)
        return f"{title_block}{items}\n\n*Se encontraron {len(fragments)} fragmentos relevantes.*"
