# tests/integration/tools/test_search_inventory.py
"""
Tests de integración para SearchInventory.

Requiere conexión a Google Sheets para obtener el inventario real.
Estos tests verifican que la herramienta de búsqueda funcione correctamente
con datos reales del inventario.
"""

import pytest

from app.inventory.client import InventoryClient
from app.inventory.schema import Inventario
from app.tools.search_inventory import SearchInventory


@pytest.fixture(scope="module")
def inventario_real() -> Inventario:
    """
    Obtiene el inventario real desde Google Sheets.
    Se ejecuta una sola vez por módulo para evitar múltiples llamadas a la API.
    """
    client = InventoryClient(sheet_name="INV-TI.RE")
    return client.fetch_inventory()


class TestSearchInventory:
    """Suite de tests de integración para SearchInventory."""

    def test_search_by_name(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real con datos.
        When: Se busca por nombre parcial "ibuprofeno".
        Then: Se obtienen medicamentos que contienen "ibuprofeno" en el nombre.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        results = searcher.search("ibuprofeno")

        # Then
        assert len(results) > 0, "Debería haber al menos un medicamento con ibuprofeno"
        for med in results:
            assert "ibuprofeno" in med.producto.lower(), f"Producto: {med.producto}"

    def test_search_by_code(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca por un código conocido.
        Then: Se obtiene el medicamento con ese código exacto.
        """
        # Given
        searcher = SearchInventory(inventario_real)
        # Código conocido del archivo CSV de ejemplo
        codigo_conocido = "7501075710250"  # ACETIF / PARACETAMOL

        # When
        results = searcher.search(codigo_conocido)

        # Then
        assert len(results) == 1, f"Debería encontrar exactamente 1 medicamento con código {codigo_conocido}"
        assert results[0].codigo == codigo_conocido

    def test_search_by_marca(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca por nombre de marca (ej. "JALOMA").
        Then: Se obtienen medicamentos de esa marca.
        """
        # Given
        searcher = SearchInventory(inventario_real)
        marca = "JALOMA"

        # When
        results = searcher.search(marca)

        # Then
        assert len(results) > 0, f"Debería haber al menos un medicamento de la marca {marca}"
        for med in results:
            assert marca in med.marca.upper() or marca in med.marca, f"Marca: {med.marca}"

    def test_search_by_category(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca por categoría "ANTIGRIPALES".
        Then: Se obtienen medicamentos de esa categoría.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        results = searcher.search_by_category("ANTIGRIPALES")

        # Then
        assert len(results) > 0, "Debería haber al menos un medicamento en la categoría ANTIGRIPALES"
        for med in results:
            assert med.categoria == "ANTIGRIPALES", f"Categoría: {med.categoria}"

    def test_search_no_results(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca un texto que no existe.
        Then: Se obtiene lista vacía.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        results = searcher.search("xyzxyzxyz")

        # Then
        assert len(results) == 0

    def test_search_and_format_table(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca "paracetamol" y se formatea como tabla.
        Then: El resultado es un string con formato tabla Markdown.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        result = searcher.search_and_format("paracetamol", format_type="table")

        # Then
        assert "|" in result, "El resultado debería contener una tabla Markdown"
        assert "paracetamol" in result.lower(), "El resultado debería contener el término de búsqueda"

    def test_search_and_format_list(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca "paracetamol" y se formatea como lista.
        Then: El resultado es un string con viñetas.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        result = searcher.search_and_format("paracetamol", format_type="list")

        # Then
        assert "- **" in result, "El resultado debería contener viñetas con negritas"
        assert "paracetamol" in result.lower(), "El resultado debería contener el término de búsqueda"

    def test_search_by_category_and_format(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca categoría "ANTIGRIPALES" y se formatea como tabla.
        Then: El resultado es un string con tabla Markdown.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        result = searcher.search_by_category_and_format("ANTIGRIPALES", format_type="table")

        # Then
        assert "|" in result, "El resultado debería contener una tabla Markdown"
        assert "No se encontraron" not in result, "El resultado no debería ser un mensaje de error"

    def test_search_empty_query(self, inventario_real: Inventario) -> None:
        """
        Given: Un inventario real.
        When: Se busca con una cadena vacía.
        Then: Se obtiene lista vacía.
        """
        # Given
        searcher = SearchInventory(inventario_real)

        # When
        results = searcher.search("")
        results2 = searcher.search("   ")

        # Then
        assert len(results) == 0
        assert len(results2) == 0
