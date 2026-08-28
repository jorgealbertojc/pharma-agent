# src/tools/format_response.py
"""
Herramienta para formatear respuestas del agente en diferentes formatos.

Permite convertir datos (medicamentos, inventario, texto) a Markdown,
JSON, texto plano, y estructuras para el agente.
"""

import json
from typing import List, Dict, Any, Optional, Union

from app.inventory.schema import Medicamento


class ResponseFormatter:
    """
    Formatea respuestas para el agente en diversos formatos.

    Métodos estáticos para convertir datos a Markdown, JSON,
    texto plano y formatos específicos para interacción con el usuario.
    """

    @staticmethod
    def to_markdown(
        data: Union[str, Dict[str, Any], List[Any]],
        title: Optional[str] = None,
        as_code: bool = False,
    ) -> str:
        """
        Convierte datos a formato Markdown.

        Args:
            data: Texto, diccionario o lista de datos.
            title: Título opcional (se añade como encabezado).
            as_code: Si es True, envuelve el contenido en bloque de código.

        Returns:
            Texto en Markdown.
        """
        parts = []

        if title:
            parts.append(f"## {title}\n")

        if isinstance(data, str):
            content = data
        elif isinstance(data, dict):
            content = json.dumps(data, indent=2, ensure_ascii=False)
        elif isinstance(data, list):
            # Si es lista de strings, convertirlos a viñetas
            if all(isinstance(item, str) for item in data):
                content = "\n".join(f"- {item}" for item in data)
            else:
                content = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            content = str(data)

        if as_code:
            content = f"```\n{content}\n```"

        parts.append(content)
        return "\n".join(parts)

    @staticmethod
    def to_json(data: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
        """
        Convierte datos a JSON.

        Args:
            data: Datos a serializar.
            indent: Espacios de indentación.
            ensure_ascii: Si se debe escapar caracteres no ASCII.

        Returns:
            Cadena JSON.
        """
        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, default=str)

    @staticmethod
    def to_plain_text(data: Any) -> str:
        """
        Convierte datos a texto plano simple.

        Args:
            data: Datos a convertir.

        Returns:
            Texto plano.
        """
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return "\n".join(f"{k}: {v}" for k, v in data.items())
        if isinstance(data, list):
            return "\n".join(str(item) for item in data)
        return str(data)

    @staticmethod
    def format_medicamentos(
        medicamentos: List[Medicamento],
        format_type: str = "table",
        max_items: Optional[int] = None,
    ) -> str:
        """
        Formatea una lista de medicamentos en formato legible.

        Args:
            medicamentos: Lista de objetos Medicamento.
            format_type: "table" (tabla Markdown) o "list" (viñetas).
            max_items: Número máximo de elementos a mostrar.

        Returns:
            Texto formateado.
        """
        if not medicamentos:
            return "No se encontraron medicamentos."

        items = medicamentos[:max_items] if max_items else medicamentos

        if format_type == "table":
            # Construir tabla Markdown
            headers = ["Código", "Producto", "Marca", "Stock", "Precio"]
            rows = [
                [
                    m.codigo,
                    m.producto,
                    m.marca,
                    str(m.stock),
                    f"${m.precio_publico:.2f}",
                ]
                for m in items
            ]

            # Anchos de columna (mínimo)
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell))

            # Línea de separación
            separator = "|".join("-" * (w + 2) for w in col_widths)
            header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
            separator_line = "|" + separator + "|"

            table = [header_line, separator_line]
            for row in rows:
                table.append("| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) + " |")

            result = "\n".join(table)
        else:
            # Formato lista con viñetas
            lines = []
            for m in items:
                lines.append(
                    f"- **{m.producto}** ({m.marca})\n"
                    f"  - Código: {m.codigo}\n"
                    f"  - Stock: {m.stock} unidades\n"
                    f"  - Precio: ${m.precio_publico:.2f}"
                )
            result = "\n\n".join(lines)

        if max_items and len(medicamentos) > max_items:
            result += f"\n\n*Mostrando {max_items} de {len(medicamentos)} medicamentos.*"

        return result

    @staticmethod
    def agent_response(content: str, sources: Optional[List[str]] = None) -> str:
        """
        Formatea la respuesta final del agente, incluyendo fuentes opcionales.

        Args:
            content: Contenido de la respuesta.
            sources: Lista de fuentes (opcional).

        Returns:
            Texto formateado en Markdown.
        """
        parts = [content]

        if sources:
            parts.append("\n---\n**Fuentes:**")
            for src in sources:
                parts.append(f"- {src}")

        return "\n".join(parts)

    @staticmethod
    def error(message: str, details: Optional[str] = None) -> str:
        """
        Formatea un mensaje de error.

        Args:
            message: Mensaje principal de error.
            details: Detalles adicionales (opcional).

        Returns:
            Texto en Markdown con formato de error.
        """
        result = f"❌ **Error:** {message}"
        if details:
            result += f"\n\n*Detalles:* {details}"
        return result
