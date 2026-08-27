# src/tools/__init__.py
"""
Módulo de herramientas para el agente farmacéutico.

Proporciona utilidades para:
- Formatear respuestas en Markdown, JSON y texto plano.
- Buscar medicamentos en el inventario.
- Consultar documentos externos (RAG) para obtener información.
- Sugerir productos de venta adicional (upsell) basados en el inventario y reglas de compatibilidad.
"""

from .format_response import ResponseFormatter
from .search_inventory import SearchInventory
from .search_docs import SearchDocs
from .suggest_upsell import SuggestUpsell

__all__ = [
    "ResponseFormatter",
    "SearchInventory",
    "SearchDocs",
    "SuggestUpsell",
]
