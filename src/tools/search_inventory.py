# src/tools/search_inventory.py
"""
Herramienta para buscar medicamentos en el inventario.

Permite realizar búsquedas por nombre, código, marca o categoría,
y devuelve los resultados formateados o en bruto.
"""

from typing import List, Optional

from src.inventory.schema import Inventario, Medicamento
from .format_response import ResponseFormatter


class SearchInventory:
    """
    Buscador de medicamentos en el inventario.

    Args:
        inventory: Objeto Inventario que contiene la lista de medicamentos.
        formatter: Instancia de ResponseFormatter (opcional, se crea por defecto).
    """

    def __init__(self, inventory: Inventario):
        self.inventory = inventory
        self.formatter = ResponseFormatter()

    def search(self, query: str) -> List[Medicamento]:
        """
        Busca medicamentos por coincidencia en nombre, marca o código.

        Primero intenta coincidencia exacta por código, luego búsqueda parcial
        por nombre y marca. Los resultados se combinan sin duplicados.

        Args:
            query: Texto de búsqueda (case-insensitive).

        Returns:
            Lista de medicamentos que coinciden con la búsqueda.
            Si query está vacío, retorna lista vacía.
        """
        query = query.strip()
        if not query:
            return []

        results: List[Medicamento] = []
        seen_codes: set[str] = set()

        # 1. Búsqueda exacta por código
        by_code = self.inventory.buscar_por_codigo(query)
        if by_code:
            results.append(by_code)
            seen_codes.add(by_code.codigo)

        # 2. Búsqueda parcial por nombre o marca
        by_name = self.inventory.buscar_por_nombre(query)
        for med in by_name:
            if med.codigo not in seen_codes:
                results.append(med)
                seen_codes.add(med.codigo)

        return results

    def search_by_category(self, category: str) -> List[Medicamento]:
        """
        Busca medicamentos por categoría exacta (case-insensitive).

        Args:
            category: Nombre de la categoría (ej. "ANTIGRIPALES").

        Returns:
            Lista de medicamentos de esa categoría.
            Si la categoría está vacía, retorna lista vacía.
        """
        category = category.strip()
        if not category:
            return []
        return self.inventory.filtrar_por_categoria(category)

    def search_and_format(
        self,
        query: str,
        format_type: str = "table",
        max_items: Optional[int] = None,
    ) -> str:
        """
        Busca medicamentos y devuelve el resultado formateado.

        Args:
            query: Texto de búsqueda.
            format_type: "table" o "list" (para format_medicamentos).
            max_items: Número máximo de resultados a mostrar.

        Returns:
            Texto formateado en Markdown con los resultados.
            Si no hay resultados, retorna mensaje informativo.
        """
        results = self.search(query)
        if not results:
            return self.formatter.to_markdown(
                "No se encontraron medicamentos que coincidan con la búsqueda.",
                title="Resultados de búsqueda",
            )

        return self.formatter.format_medicamentos(
            results,
            format_type=format_type,
            max_items=max_items,
        )

    def search_by_category_and_format(
        self,
        category: str,
        format_type: str = "table",
        max_items: Optional[int] = None,
    ) -> str:
        """
        Busca medicamentos por categoría y devuelve el resultado formateado.

        Args:
            category: Nombre de la categoría.
            format_type: "table" o "list".
            max_items: Número máximo de resultados a mostrar.

        Returns:
            Texto formateado en Markdown con los resultados.
        """
        results = self.search_by_category(category)
        if not results:
            return self.formatter.to_markdown(
                f"No se encontraron medicamentos en la categoría '{category}'.",
                title="Resultados por categoría",
            )

        return self.formatter.format_medicamentos(
            results,
            format_type=format_type,
            max_items=max_items,
        )
