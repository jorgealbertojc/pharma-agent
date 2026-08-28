# tests/unit/inventory/test_schema.py
"""
Tests unitarios para el módulo de esquemas de inventario.

Verifica la creación de objetos Medicamento, la validación de campos,
y los métodos de búsqueda y filtrado de Inventario.
"""

import pytest

from app.inventory.schema import Medicamento, Inventario


class TestMedicamento:
    """Pruebas para el modelo Medicamento."""

    def test_create_medicamento_with_aliases(self) -> None:
        """
        Given: Datos con los alias del CSV (mayúsculas y caracteres especiales).
        When: Se crea un Medicamento.
        Then: Los campos se asignan correctamente a los atributos.
        """
        # Given
        data = {
            "CÓDIGO": "12345",
            "LOTE": "ABC123",
            "CAD": "jul-2026",
            "PRODUCTO": "Paracetamol 500mg",
            "QUE ES": "LIBRE VENTA",
            "MARCA": "Genérico",
            "STOCK": "10",
            "STOCK REAL": "8",
            "PRECIO COMPRA": "5.50",
            "PRECIO PÚBLICO": "15.00",
            "PRECIO DIDI": "14.50",
            "COSTO REAL POR VENDER": "55.00",
            "VENDIDOS PIEZAS": "2",
            "¿ESTÁ AGOTADO?": "",
            "CATEGORIA": "ANALGÉSICO",
            "RESURTIR": "RESURTIR",
        }

        # When
        med = Medicamento(**data)

        # Then
        assert med.codigo == "12345"
        assert med.lote == "ABC123"
        assert med.caducidad == "jul-2026"
        assert med.producto == "Paracetamol 500mg"
        assert med.tipo_venta == "LIBRE VENTA"
        assert med.marca == "Genérico"
        assert med.stock == 10
        assert med.stock_real == 8
        assert med.precio_compra == 5.5
        assert med.precio_publico == 15.0
        assert med.precio_didi == 14.5
        assert med.costo_real_por_vender == 55.0
        assert med.vendidos_piezas == 2
        assert med.agotado is None
        assert med.categoria == "ANALGÉSICO"
        assert med.resurtir == "RESURTIR"

    def test_create_medicamento_with_missing_optional_fields(self) -> None:
        """
        Given: Datos mínimos (solo campos obligatorios).
        When: Se crea un Medicamento.
        Then: Los campos opcionales toman valor None o 0 por defecto.
        """
        # Given
        data = {
            "CÓDIGO": "999",
            "PRODUCTO": "Ibuprofeno",
            "QUE ES": "LIBRE VENTA",
            "MARCA": "MarcaX",
            "STOCK": "5",
            "STOCK REAL": "5",
            "PRECIO COMPRA": "10.0",
            "PRECIO PÚBLICO": "25.0",
            "VENDIDOS PIEZAS": "0",
        }

        # When
        med = Medicamento(**data)

        # Then
        assert med.codigo == "999"
        assert med.lote is None
        assert med.caducidad is None
        assert med.precio_didi is None
        assert med.costo_real_por_vender is None
        assert med.agotado is None
        assert med.categoria is None
        assert med.resurtir is None
        # Los campos numéricos que no se pasan toman valor por defecto
        # (stock_real, vendidos_piezas se pasaron, pero precio_didi no existe)
        assert med.precio_didi is None

    def test_parse_float_with_currency_symbols(self) -> None:
        """
        Given: Precios con símbolos de moneda y comas.
        When: Se crea el Medicamento.
        Then: Los valores se convierten a float correctamente.
        """
        data = {
            "CÓDIGO": "1",
            "PRODUCTO": "test",
            "QUE ES": "LIBRE VENTA",
            "MARCA": "test",
            "STOCK": "1",
            "STOCK REAL": "1",
            "PRECIO COMPRA": "$123.45",
            "PRECIO PÚBLICO": "1,234.56",
            "VENDIDOS PIEZAS": "0",
        }
        med = Medicamento(**data)
        assert med.precio_compra == 123.45
        assert med.precio_publico == 1234.56

    def test_parse_int_with_non_digit_chars(self) -> None:
        """
        Given: Campos de stock con caracteres no numéricos.
        When: Se crea el Medicamento.
        Then: Se extraen solo los dígitos.
        """
        data = {
            "CÓDIGO": "1",
            "PRODUCTO": "test",
            "QUE ES": "LIBRE VENTA",
            "MARCA": "test",
            "STOCK": "10 unidades",
            "STOCK REAL": "8,5",  # tiene coma, pero solo extrae dígitos -> 85
            "PRECIO COMPRA": "1.0",
            "PRECIO PÚBLICO": "2.0",
            "VENDIDOS PIEZAS": "3 piezas",
        }
        med = Medicamento(**data)
        assert med.stock == 10
        assert med.stock_real == 85  # porque solo se toman dígitos, "85"
        assert med.vendidos_piezas == 3

    def test_extra_fields_ignored(self) -> None:
        """
        Given: Datos que incluyen campos extra no definidos.
        When: Se crea el Medicamento.
        Then: Los campos extra se ignoran (Config.extra = 'ignore').
        """
        data = {
            "CÓDIGO": "1",
            "PRODUCTO": "test",
            "QUE ES": "LIBRE VENTA",
            "MARCA": "test",
            "STOCK": "1",
            "STOCK REAL": "1",
            "PRECIO COMPRA": "1.0",
            "PRECIO PÚBLICO": "2.0",
            "VENDIDOS PIEZAS": "0",
            "CAMPO_EXTRA": "valor",
            "OTRO_CAMPO": 123,
        }
        med = Medicamento(**data)
        # No debe haber atributo CAMPO_EXTRA
        assert not hasattr(med, "CAMPO_EXTRA")
        assert not hasattr(med, "OTRO_CAMPO")


class TestInventario:
    """Pruebas para el modelo Inventario."""

    @pytest.fixture
    def sample_inventario(self) -> Inventario:
        """Crea un inventario con algunos medicamentos de prueba."""
        med1 = Medicamento(
            codigo="001",
            producto="Paracetamol 500mg",
            marca="Genérico",
            tipo_venta="LIBRE VENTA",
            stock=10,
            stock_real=10,
            precio_compra=5.0,
            precio_publico=15.0,
            vendidos_piezas=0,
            categoria="ANALGÉSICO",
        )
        med2 = Medicamento(
            codigo="002",
            producto="Ibuprofeno 400mg",
            marca="MarcaX",
            tipo_venta="RECETA",
            stock=5,
            stock_real=5,
            precio_compra=8.0,
            precio_publico=25.0,
            vendidos_piezas=2,
            categoria="ANTIINFLAMATORIO",
        )
        med3 = Medicamento(
            codigo="003",
            producto="Omeprazol 20mg",
            marca="Genérico",
            tipo_venta="LIBRE VENTA",
            stock=0,
            stock_real=0,
            precio_compra=3.0,
            precio_publico=10.0,
            vendidos_piezas=5,
            categoria="GASTRO",
        )
        return Inventario(medicamentos=[med1, med2, med3])

    def test_buscar_por_nombre(self, sample_inventario: Inventario) -> None:
        """
        Given: Un inventario con varios medicamentos.
        When: Se busca por nombre parcial.
        Then: Devuelve los medicamentos que coinciden (case-insensitive).
        """
        # When
        resultados = sample_inventario.buscar_por_nombre("paracetamol")
        # Then
        assert len(resultados) == 1
        assert resultados[0].codigo == "001"

        # Buscar por marca
        resultados = sample_inventario.buscar_por_nombre("marcax")
        assert len(resultados) == 1
        assert resultados[0].codigo == "002"

        # Buscar sin resultados
        resultados = sample_inventario.buscar_por_nombre("xyz")
        assert len(resultados) == 0

    def test_buscar_por_codigo(self, sample_inventario: Inventario) -> None:
        """
        Given: Un inventario con varios medicamentos.
        When: Se busca por código exacto.
        Then: Devuelve el medicamento correspondiente o None.
        """
        # When
        med = sample_inventario.buscar_por_codigo("002")
        # Then
        assert med is not None
        assert med.producto == "Ibuprofeno 400mg"

        # Código inexistente
        med = sample_inventario.buscar_por_codigo("999")
        assert med is None

    def test_filtrar_por_categoria(self, sample_inventario: Inventario) -> None:
        """
        Given: Un inventario con varias categorías.
        When: Se filtra por categoría.
        Then: Devuelve los medicamentos de esa categoría (case-insensitive).
        """
        # When
        resultados = sample_inventario.filtrar_por_categoria("antiinflamatorio")
        # Then
        assert len(resultados) == 1
        assert resultados[0].codigo == "002"

        # Categoría sin resultados
        resultados = sample_inventario.filtrar_por_categoria("vitaminas")
        assert len(resultados) == 0

        # Categoría vacía
        resultados = sample_inventario.filtrar_por_categoria("")
        assert len(resultados) == 0
