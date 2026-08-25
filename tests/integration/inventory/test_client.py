"""
Tests de integración para InventoryClient.

Requiere:
- Variables de entorno GOOGLE_APPLICATION_CREDENTIALS y SPREADSHEET_ID definidas.
- La hoja "INV-TI.RE" debe existir y contener inventario.
"""

import pytest

from src.inventory.client import InventoryClient
from src.inventory.schema import Medicamento, Inventario


class TestInventoryClient:
    """Pruebas de integración para el cliente de inventario."""

    def test_fetch_medicamentos_returns_list(self) -> None:
        """
        Given: Un cliente configurado con credenciales y spreadsheet_id, usando la hoja 'INV-TI.RE'.
        When: Se llama a fetch_medicamentos().
        Then: Se obtiene una lista de objetos Medicamento no vacía.
        """
        # Given
        client = InventoryClient(sheet_name="INV-TI.RE")

        # When
        medicamentos = client.fetch_medicamentos()

        # Then
        assert isinstance(medicamentos, list)
        assert len(medicamentos) > 0
        assert all(isinstance(m, Medicamento) for m in medicamentos)

        # Verificar que algunos campos no estén vacíos en el primer elemento
        first = medicamentos[0]
        assert first.codigo is not None and first.codigo != ""
        assert first.producto is not None and first.producto != ""
        assert first.marca is not None
        assert first.precio_compra >= 0
        assert first.precio_publico >= 0

    def test_fetch_inventory_returns_inventario(self) -> None:
        """
        Given: Un cliente configurado para la hoja 'INV-TI.RE'.
        When: Se llama a fetch_inventory().
        Then: Devuelve un objeto Inventario con medicamentos y timestamp.
        """
        # Given
        client = InventoryClient(sheet_name="INV-TI.RE")

        # When
        inventario = client.fetch_inventory()

        # Then
        assert isinstance(inventario, Inventario)
        assert len(inventario.medicamentos) > 0
        assert inventario.ultima_actualizacion is not None

    def test_fetch_raw_values_returns_non_empty(self) -> None:
        """
        Given: Cliente con hoja 'INV-TI.RE'.
        When: Se obtienen valores crudos.
        Then: La lista tiene al menos 2 filas (encabezado + datos).
        """
        client = InventoryClient(sheet_name="INV-TI.RE")
        rows = client.fetch_raw_values()
        assert len(rows) >= 2  # al menos encabezado + una fila

    def test_fetch_as_dict_returns_dict_list(self) -> None:
        """
        Given: Cliente configurado.
        When: Se obtiene el inventario como diccionarios.
        Then: La lista no está vacía y los diccionarios tienen claves esperadas.
        """
        client = InventoryClient(sheet_name="INV-TI.RE")
        records = client.fetch_as_dict()
        assert len(records) > 0
        # Verificar que al menos tenga campos comunes (usando el primer registro)
        first = records[0]
        # Puede que el encabezado tenga nombres específicos como "CÓDIGO"
        assert "CÓDIGO" in first or "PRODUCTO" in first

    def test_print_first_three_medicamentos(self) -> None:
        """
        Given: Un cliente configurado con la hoja 'INV-TI.RE'.
        When: Se obtienen todos los medicamentos.
        Then: Se imprimen los primeros 3 en formato JSON con CÓDIGO, LOTE y PRODUCTO.
        """
        # Given
        import json
        client = InventoryClient(sheet_name="INV-TI.RE")

        # When
        medicamentos = client.fetch_medicamentos()

        # Then
        assert len(medicamentos) >= 3, "Se necesitan al menos 3 medicamentos para la muestra."

        # Extraer los primeros 3 y formatear con los alias
        first_three = []
        for med in medicamentos[:3]:
            # Usamos los alias del modelo (definidos en Field) para las claves
            first_three.append({
                "CÓDIGO": med.codigo,
                "LOTE": med.lote,
                "PRODUCTO": med.producto,
            })

        # Imprimir en JSON legible
        print("\n" + "=" * 60)
        print("Primeros 3 medicamentos del inventario:")
        print(json.dumps(first_three, indent=2, ensure_ascii=False))
        print("=" * 60 + "\n")
