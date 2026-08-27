# src/tools/suggest_upsell.py
"""
Herramienta para sugerir productos de venta adicional (upsell) basada en el medicamento solicitado.

Esta herramienta recomienda productos complementarios o alternativos,
priorizando la compatibilidad y seguridad. Si no hay una recomendación clara,
ofrece un producto de respaldo genérico (ej. Electrolit, agua) para acompañar
la toma del medicamento.
"""

from typing import List, Optional, Dict, Any

from src.inventory.schema import Inventario, Medicamento
from .format_response import ResponseFormatter
from .search_inventory import SearchInventory


class SuggestUpsell:
    """
    Sugeridor de venta adicional basado en el inventario.

    Args:
        inventory: Objeto Inventario con todos los medicamentos.
        search_docs: (Opcional) Instancia de SearchDocs para consultar
                     información de compatibilidad (RAG). Si no se pasa,
                     la recomendación se basa únicamente en categorías.
        formatter: Instancia de ResponseFormatter (opcional).
    """

    # Productos de respaldo seguros y genéricos (orden de preferencia)
    FALLBACK_PRODUCTS = [
        "Electrolit",
        "Agua purificada",
        "Jugo de naranja",
        "Gel antibacterial",
    ]

    def __init__(
        self,
        inventory: Inventario,
        search_docs: Optional[Any] = None,
        formatter: Optional[ResponseFormatter] = None,
    ):
        self.inventory = inventory
        self.search_docs = search_docs
        self.formatter = formatter or ResponseFormatter()
        self.searcher = SearchInventory(inventory)

    def suggest(self, query: str) -> str:
        """
        Genera una sugerencia de producto para venta adicional.

        Args:
            query: Nombre o código del medicamento solicitado por el cliente.

        Returns:
            Mensaje formateado en Markdown con la recomendación.
            Si no se encuentra el medicamento, sugiere un producto de respaldo.
        """
        # 1. Buscar el medicamento solicitado
        medicamentos = self.searcher.search(query)
        if not medicamentos:
            return self._fallback_response(
                f"No encontré '{query}' en el inventario. "
                "¿Te interesaría alguno de estos productos?"
            )

        # 2. Tomar el primer resultado (el más relevante)
        medicamento = medicamentos[0]

        # 3. Buscar productos relacionados (misma categoría o mismo principio activo)
        relacionados = self._find_related(medicamento)

        if relacionados:
            # Ordenar por stock y precio (priorizar los que tienen más stock)
            relacionados.sort(key=lambda m: (m.stock, -m.precio_publico), reverse=True)
            top = relacionados[:3]  # máximo 3 sugerencias

            # Formatear la respuesta
            header = f"Basado en tu interés por **{medicamento.producto}**, te recomiendo:"
            table = self.formatter.format_medicamentos(top, format_type="table")
            return f"{header}\n\n{table}"

        # 4. Si no hay relacionados, ofrecer un producto de respaldo
        return self._fallback_response(
            f"Además de **{medicamento.producto}**, ¿te gustaría agregar algo para acompañarlo?"
        )

    def _find_related(self, medicamento: Medicamento) -> List[Medicamento]:
        """
        Encuentra medicamentos relacionados con el dado.

        Estrategia:
        1. Misma categoría (si existe).
        2. Mismo principio activo (extraído del nombre).
        3. Misma marca.

        Args:
            medicamento: Medicamento base.

        Returns:
            Lista de medicamentos relacionados (excluyendo el propio).
        """
        relacionados: List[Medicamento] = []
        seen_codes = {medicamento.codigo}

        # 1. Por categoría
        if medicamento.categoria:
            for m in self.inventory.medicamentos:
                if m.codigo not in seen_codes and m.categoria == medicamento.categoria:
                    relacionados.append(m)
                    seen_codes.add(m.codigo)

        # 2. Por principio activo (extraer del nombre)
        # Buscar palabras clave como "IBUPROFENO", "PARACETAMOL", etc.
        # (simplificado: buscar en el nombre del medicamento base y comparar)
        palabras_clave = self._extract_keywords(medicamento.producto)
        if palabras_clave:
            for m in self.inventory.medicamentos:
                if m.codigo not in seen_codes:
                    for kw in palabras_clave:
                        if kw in m.producto.upper() or kw in m.producto:
                            relacionados.append(m)
                            seen_codes.add(m.codigo)
                            break

        # 3. Por marca (solo si hay pocos relacionados)
        if len(relacionados) < 2 and medicamento.marca:
            for m in self.inventory.medicamentos:
                if m.codigo not in seen_codes and m.marca == medicamento.marca:
                    relacionados.append(m)
                    seen_codes.add(m.codigo)

        return relacionados

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrae posibles principios activos del nombre del medicamento.
        (Implementación simple: busca palabras en mayúsculas o entre paréntesis)
        """
        import re
        keywords = set()
        # Palabras en mayúsculas (posibles principios activos)
        for word in re.findall(r'\b[A-ZÁÉÍÓÚÑ]{3,}\b', text):
            keywords.add(word)
        # Palabras entre paréntesis
        for match in re.findall(r'\(([^)]+)\)', text):
            for word in match.split('/'):
                word = word.strip().upper()
                if len(word) > 2:
                    keywords.add(word)
        # También buscar números con mg o g
        for match in re.findall(r'\b\d+[MG]+\b', text.upper()):
            keywords.add(match)
        return list(keywords)

    def _fallback_response(self, message: str) -> str:
        """
        Genera una respuesta de respaldo cuando no hay recomendaciones claras.

        Args:
            message: Mensaje contextual previo.

        Returns:
            Texto formateado con la sugerencia de productos de respaldo.
        """
        # Buscar los productos de respaldo en el inventario
        fallback_items = []
        for name in self.FALLBACK_PRODUCTS:
            results = self.searcher.search(name)
            if results:
                fallback_items.extend(results[:1])  # tomar el primero de cada

        if fallback_items:
            header = f"{message}\n\n**Productos recomendados para acompañar:**"
            table = self.formatter.format_medicamentos(fallback_items, format_type="table")
            return f"{header}\n\n{table}"

        # Si ni siquiera hay productos de respaldo, mensaje genérico
        return f"{message}\n\nTe recomiendo consultar con el farmacéutico para más opciones."
