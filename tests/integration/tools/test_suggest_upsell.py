# tests/integration/tools/test_suggest_upsell.py
"""
Tests de integración para SuggestUpsell.

Requiere:
- Variables de entorno GOOGLE_APPLICATION_CREDENTIALS y SPREADSHEET_ID definidas.
- Conexión a Google Sheets para obtener el inventario real.
- No requiere Pinecone (a menos que se pase search_docs, pero no se usa en estos tests).
"""

import pytest

from app.inventory.client import InventoryClient
from app.inventory.schema import Inventario
from app.tools.suggest_upsell import SuggestUpsell


@pytest.fixture(scope="module")
def inventario_real() -> Inventario:
    """Obtiene el inventario real desde Google Sheets una sola vez por módulo."""
    client = InventoryClient(sheet_name="INV-TI.RE")
    return client.fetch_inventory()


@pytest.fixture(scope="function")
def suggester(inventario_real: Inventario) -> SuggestUpsell:
    """Crea una instancia de SuggestUpsell con el inventario real."""
    return SuggestUpsell(inventory=inventario_real)


class TestSuggestUpsell:
    """Suite de tests de integración para SuggestUpsell."""

    def test_suggest_existing_product_returns_related(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto existente en el inventario (ej. ibuprofeno).
        When: Se solicita una sugerencia para ese producto.
        Then: Se obtienen productos relacionados (misma categoría, principio activo o marca).
        """
        # Given
        searcher = suggester

        # When
        result = searcher.suggest("ibuprofeno")

        # Then
        assert isinstance(result, str)
        assert len(result) > 0
        # Debe mencionar el producto base o tener sugerencias
        # (puede ser que no haya relacionados, entonces mostrará fallback)
        assert "ibuprofeno" in result.lower() or "Basado en tu interés" in result or "te recomiendo" in result

    def test_suggest_non_existent_product_uses_fallback(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto que no existe en el inventario.
        When: Se solicita una sugerencia.
        Then: Se obtiene un mensaje de fallback con productos genéricos o recomendación.
        """
        # Given
        searcher = suggester

        # When
        result = searcher.suggest("producto_inexistente_xyz")

        # Then
        assert isinstance(result, str)
        assert "No encontré" in result or "fallback" in result.lower()
        # Normalizar a minúsculas para buscar keywords
        result_lower = result.lower()
        fallback_keywords = ["electrolit", "agua", "jugo", "recomiendo", "recomendados"]
        assert any(keyword in result_lower for keyword in fallback_keywords), \
            f"La respuesta no contiene ninguna keyword de fallback: {result}"

    def test_suggest_returns_markdown_format(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto existente.
        When: Se solicita una sugerencia.
        Then: La respuesta está formateada en Markdown (contiene tablas o viñetas).
        """
        # Given
        searcher = suggester

        # When
        result = searcher.suggest("paracetamol")

        # Then
        assert isinstance(result, str)
        # Debe contener caracteres de Markdown: `|` para tabla o `**` para negritas
        assert "|" in result or "**" in result, "La respuesta debería estar formateada en Markdown"

    def test_suggest_does_not_recommend_same_product(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto existente.
        When: Se solicita una sugerencia y hay relacionados.
        Then: El producto base no aparece en la lista de sugerencias.
        """
        # Given
        searcher = suggester
        # Elegir un medicamento que sabemos tiene categoría o marca para forzar relacionados
        # Usamos un código conocido: "7501075710250" (ACETIF / PARACETAMOL)
        query = "ACETIF"

        # When
        result = searcher.suggest(query)
        # Buscar el nombre del producto base en el resultado
        # (podríamos obtenerlo del inventario, pero simplificamos)
        # Obtener el medicamento base
        medicamentos = searcher.searcher.search(query)
        if not medicamentos:
            pytest.skip("No se encontró el producto base para esta prueba")
        base = medicamentos[0]
        base_name = base.producto

        # Then
        # Si hay productos relacionados, el nombre del base no debe aparecer en la tabla
        if "te recomiendo" in result:
            # Extraer la tabla o la lista de recomendados
            # (asumimos que el nombre del base no aparece en la lista)
            # Una verificación simple: contar ocurrencias del nombre del base
            occurrences = result.lower().count(base_name.lower())
            # Puede aparecer en el encabezado, pero no en la tabla (puede haber 1 ocurrencia en el encabezado)
            # Si hay más de 1, significa que también está en la lista de recomendados (mal)
            assert occurrences <= 1, f"El producto base '{base_name}' aparece más de una vez, probablemente en la tabla de sugerencias."

    def test_suggest_fallback_when_no_related(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto que no tiene relacionados (categoría única, sin marca similar).
        When: Se solicita una sugerencia.
        Then: Se obtiene un mensaje de fallback con productos genéricos.
        """
        # Given
        searcher = suggester
        # Buscar un producto que probablemente no tenga relacionados
        # Por ejemplo, un producto con categoría nula o única
        # Usamos un código de un producto que vimos en el CSV que tiene categoría vacía
        # "759684031250" (ACEITE CLASICO DE RICINO) - categoría vacía
        query = "ACEITE CLASICO DE RICINO"

        # When
        result = searcher.suggest(query)

        # Then
        # Debe decir "te recomiendo" o usar fallback
        # Si no hay relacionados, debe mostrar mensaje de acompañamiento
        assert "te recomiendo" in result or "acompañarlo" in result or "productos recomendados" in result

    def test_suggest_limits_results_to_three(self, suggester: SuggestUpsell) -> None:
        """
        Given: Un producto con muchos relacionados.
        When: Se solicita una sugerencia.
        Then: La respuesta muestra como máximo 3 productos sugeridos.
        """
        # Given
        searcher = suggester
        # Elegir un producto con muchos relacionados (ej. "JALOMA" tiene muchos)
        query = "JALOMA"

        # When
        result = searcher.suggest(query)

        # Then
        # Contar cuántas líneas de tabla o viñetas aparecen
        # Si hay tabla, contar filas (excluyendo encabezados)
        # Si hay viñetas, contar ítems
        rows = result.count("|")  # aproximación
        # Si hay tabla, el número de filas de datos es (count("|") // número_columnas) - 1
        # Simplificamos: si hay "|", contamos cuántas líneas con "|" hay
        if "|" in result:
            lines = result.split("\n")
            table_lines = [line for line in lines if "|" in line and "---" not in line]
            # Los encabezados también tienen "|", pero los datos también.
            # Restamos 1 (encabezado) y 1 (separador) -> 2 líneas no son datos
            # Puede haber hasta 3 líneas de datos si hay 3 recomendados
            data_lines = [line for line in table_lines if "---" not in line]
            # El primer data line es el encabezado, los demás son datos
            if len(data_lines) > 1:
                # Restamos 1 por el encabezado
                items = len(data_lines) - 1
                assert items <= 3, f"Se encontraron {items} sugerencias, pero el máximo es 3"
        else:
            # Si no hay tabla, contar viñetas o líneas con "-"
            items = result.count("- ")
            assert items <= 3, f"Se encontraron {items} sugerencias, pero el máximo es 3"
