# tests/unit/tools/test_format_response.py
"""
Tests unitarios para la herramienta de formateo de respuestas.

Verifica la correcta conversión de datos a Markdown, JSON, texto plano,
formateo de medicamentos, respuestas del agente y mensajes de error.
"""

import json

import pytest

from src.tools.format_response import ResponseFormatter
from src.inventory.schema import Medicamento


class TestResponseFormatter:
    """Suite de tests para ResponseFormatter."""

    # ------------------------------------------------------------
    # to_markdown
    # ------------------------------------------------------------

    def test_to_markdown_with_string(self) -> None:
        """
        Given: Un string simple.
        When: Se llama a to_markdown.
        Then: Retorna el string sin modificaciones adicionales.
        """
        # Given
        text = "Esto es un texto de prueba."

        # When
        result = ResponseFormatter.to_markdown(text)

        # Then
        assert result == text

    def test_to_markdown_with_title(self) -> None:
        """
        Given: Un string y un título.
        When: Se llama a to_markdown.
        Then: Retorna el título como encabezado seguido del contenido.
        """
        # Given
        text = "Contenido de prueba."
        title = "Título de prueba"

        # When
        result = ResponseFormatter.to_markdown(text, title=title)

        # Then
        expected = f"## {title}\n\n{text}"
        assert result == expected

    def test_to_markdown_with_dict(self) -> None:
        """
        Given: Un diccionario.
        When: Se llama a to_markdown.
        Then: Retorna el JSON del diccionario en Markdown.
        """
        # Given
        data = {"nombre": "Ibuprofeno", "dosis": "400mg"}

        # When
        result = ResponseFormatter.to_markdown(data)

        # Then
        expected = json.dumps(data, indent=2, ensure_ascii=False)
        assert result == expected

    def test_to_markdown_with_list_of_strings(self) -> None:
        """
        Given: Una lista de strings.
        When: Se llama a to_markdown.
        Then: Retorna una lista con viñetas.
        """
        # Given
        items = ["Item 1", "Item 2", "Item 3"]

        # When
        result = ResponseFormatter.to_markdown(items)

        # Then
        expected = "- Item 1\n- Item 2\n- Item 3"
        assert result == expected

    def test_to_markdown_with_list_of_dicts(self) -> None:
        """
        Given: Una lista de diccionarios.
        When: Se llama a to_markdown.
        Then: Retorna el JSON de la lista en Markdown.
        """
        # Given
        data = [{"a": 1}, {"b": 2}]

        # When
        result = ResponseFormatter.to_markdown(data)

        # Then
        expected = json.dumps(data, indent=2, ensure_ascii=False)
        assert result == expected

    def test_to_markdown_with_code_block(self) -> None:
        """
        Given: Un string y as_code=True.
        When: Se llama a to_markdown.
        Then: Retorna el string envuelto en bloque de código.
        """
        # Given
        text = "print('Hola')"

        # When
        result = ResponseFormatter.to_markdown(text, as_code=True)

        # Then
        expected = "```\nprint('Hola')\n```"
        assert result == expected

    # ------------------------------------------------------------
    # to_json
    # ------------------------------------------------------------

    def test_to_json_with_dict(self) -> None:
        """
        Given: Un diccionario.
        When: Se llama a to_json.
        Then: Retorna el string JSON con indentación y ensure_ascii=False.
        """
        # Given
        data = {"nombre": "Paracetamol", "precio": 15.50}

        # When
        result = ResponseFormatter.to_json(data)

        # Then
        expected = json.dumps(data, indent=2, ensure_ascii=False)
        assert result == expected

    def test_to_json_with_custom_indent(self) -> None:
        """
        Given: Un diccionario y indent=4.
        When: Se llama a to_json.
        Then: Retorna JSON con indentación de 4 espacios.
        """
        # Given
        data = {"a": 1}
        indent = 4

        # When
        result = ResponseFormatter.to_json(data, indent=indent)

        # Then
        expected = json.dumps(data, indent=indent, ensure_ascii=False)
        assert result == expected

    def test_to_json_with_non_ascii_ensure(self) -> None:
        """
        Given: Un diccionario con caracteres no ASCII y ensure_ascii=True.
        When: Se llama a to_json.
        Then: Retorna JSON con escapes Unicode.
        """
        # Given
        data = {"nombre": "ibuprofeno café"}

        # When
        result = ResponseFormatter.to_json(data, ensure_ascii=True)

        # Then
        expected = json.dumps(data, indent=2, ensure_ascii=True)
        assert result == expected

    def test_to_json_with_object_with_default_serializer(self) -> None:
        """
        Given: Un objeto que no es serializable por JSON directamente (ej. datetime).
        When: Se llama a to_json.
        Then: Retorna JSON usando el default=str.
        """
        # Given
        from datetime import datetime
        data = {"fecha": datetime(2026, 8, 25)}

        # When
        result = ResponseFormatter.to_json(data)

        # Then
        assert "2026-08-25" in result

    # ------------------------------------------------------------
    # to_plain_text
    # ------------------------------------------------------------

    def test_to_plain_text_with_string(self) -> None:
        """
        Given: Un string.
        When: Se llama a to_plain_text.
        Then: Retorna el mismo string.
        """
        text = "Texto plano"
        result = ResponseFormatter.to_plain_text(text)
        assert result == text

    def test_to_plain_text_with_dict(self) -> None:
        """
        Given: Un diccionario.
        When: Se llama a to_plain_text.
        Then: Retorna el diccionario formateado como líneas clave: valor.
        """
        # Given
        data = {"a": 1, "b": 2}

        # When
        result = ResponseFormatter.to_plain_text(data)

        # Then
        expected = "a: 1\nb: 2"
        assert result == expected

    def test_to_plain_text_with_list_of_strings(self) -> None:
        """
        Given: Una lista de strings.
        When: Se llama a to_plain_text.
        Then: Retorna los elementos en líneas separadas.
        """
        # Given
        items = ["uno", "dos", "tres"]

        # When
        result = ResponseFormatter.to_plain_text(items)

        # Then
        expected = "uno\ndos\ntres"
        assert result == expected

    def test_to_plain_text_with_other_type(self) -> None:
        """
        Given: Un entero.
        When: Se llama a to_plain_text.
        Then: Retorna el string del entero.
        """
        result = ResponseFormatter.to_plain_text(42)
        assert result == "42"

    # ------------------------------------------------------------
    # format_medicamentos
    # ------------------------------------------------------------

    @pytest.fixture
    def sample_medicamentos(self) -> list[Medicamento]:
        """Crea una lista de medicamentos de prueba."""
        return [
            Medicamento(
                codigo="001",
                producto="Paracetamol 500mg",
                tipo_venta="LIBRE VENTA",
                marca="Genérico",
                stock=10,
                stock_real=10,
                precio_compra=5.0,
                precio_publico=15.0,
                vendidos_piezas=0,
            ),
            Medicamento(
                codigo="002",
                producto="Ibuprofeno 400mg",
                tipo_venta="LIBRE VENTA",
                marca="MarcaX",
                stock=5,
                stock_real=5,
                precio_compra=8.0,
                precio_publico=25.0,
                vendidos_piezas=2,
            ),
        ]

    def test_format_medicamentos_empty_list(self) -> None:
        """
        Given: Lista vacía de medicamentos.
        When: Se llama a format_medicamentos.
        Then: Retorna mensaje "No se encontraron medicamentos."
        """
        result = ResponseFormatter.format_medicamentos([])
        assert result == "No se encontraron medicamentos."

    def test_format_medicamentos_table(self, sample_medicamentos: list[Medicamento]) -> None:
        """
        Given: Lista de medicamentos.
        When: Se llama a format_medicamentos con format_type="table".
        Then: Retorna una tabla Markdown.
        """
        # When
        result = ResponseFormatter.format_medicamentos(
            sample_medicamentos,
            format_type="table",
        )

        # Then
        assert "| Código | Producto" in result
        assert "|--------" in result
        assert "| 001    | Paracetamol 500mg" in result
        assert "| 002    | Ibuprofeno 400mg" in result
        assert "$15.00" in result
        assert "$25.00" in result

    def test_format_medicamentos_list(self, sample_medicamentos: list[Medicamento]) -> None:
        """
        Given: Lista de medicamentos.
        When: Se llama a format_medicamentos con format_type="list".
        Then: Retorna viñetas con detalles.
        """
        # When
        result = ResponseFormatter.format_medicamentos(
            sample_medicamentos,
            format_type="list",
        )

        # Then
        assert "- **Paracetamol 500mg** (Genérico)" in result
        assert "- **Ibuprofeno 400mg** (MarcaX)" in result
        assert "Código: 001" in result
        assert "Código: 002" in result
        assert "Stock: 10 unidades" in result
        assert "Precio: $15.00" in result

    def test_format_medicamentos_max_items(self, sample_medicamentos: list[Medicamento]) -> None:
        """
        Given: Lista de medicamentos y max_items=1.
        When: Se llama a format_medicamentos.
        Then: Solo muestra el primer medicamento y agrega nota.
        """
        # When
        result = ResponseFormatter.format_medicamentos(
            sample_medicamentos,
            format_type="table",
            max_items=1,
        )

        # Then
        assert "| 001    | Paracetamol 500mg" in result
        assert "| 002 | Ibuprofeno 400mg" not in result
        assert "*Mostrando 1 de 2 medicamentos.*" in result

    def test_format_medicamentos_table_without_items(self) -> None:
        """Dado una lista vacía, retorna mensaje de no encontrados."""
        result = ResponseFormatter.format_medicamentos([])
        assert result == "No se encontraron medicamentos."

    # ------------------------------------------------------------
    # agent_response
    # ------------------------------------------------------------

    def test_agent_response_without_sources(self) -> None:
        """
        Given: Contenido de respuesta.
        When: Se llama a agent_response sin sources.
        Then: Retorna solo el contenido.
        """
        content = "Respuesta del agente."
        result = ResponseFormatter.agent_response(content)
        assert result == content

    def test_agent_response_with_sources(self) -> None:
        """
        Given: Contenido y lista de fuentes.
        When: Se llama a agent_response.
        Then: Retorna contenido seguido de lista de fuentes.
        """
        content = "Respuesta del agente."
        sources = ["Fuente 1", "Fuente 2"]

        result = ResponseFormatter.agent_response(content, sources=sources)

        expected = "Respuesta del agente.\n\n---\n**Fuentes:**\n- Fuente 1\n- Fuente 2"
        assert result == expected

    # ------------------------------------------------------------
    # error
    # ------------------------------------------------------------

    def test_error_without_details(self) -> None:
        """
        Given: Mensaje de error sin detalles.
        When: Se llama a error.
        Then: Retorna mensaje formateado con ❌.
        """
        message = "No se pudo conectar"
        result = ResponseFormatter.error(message)

        expected = "❌ **Error:** No se pudo conectar"
        assert result == expected

    def test_error_with_details(self) -> None:
        """
        Given: Mensaje de error con detalles.
        When: Se llama a error.
        Then: Retorna mensaje con detalles en línea adicional.
        """
        message = "Error de red"
        details = "Timeout después de 30s"
        result = ResponseFormatter.error(message, details=details)

        expected = "❌ **Error:** Error de red\n\n*Detalles:* Timeout después de 30s"
        assert result == expected
