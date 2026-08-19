# app/langchain/memory/utils.py
"""
Utilidades auxiliares para el sistema de memoria conversacional.
"""

from typing import List, Dict


def count_tokens_approx(text: str) -> int:
    """
    Estimación aproximada de tokens (4 caracteres ≈ 1 token).

    Esta es una heurística común para modelos como GPT/LLaMA.
    Para mediciones exactas se necesitaría un tokenizador específico.

    Args:
        text: Texto a medir.

    Returns:
        Número estimado de tokens.
    """
    return len(text) // 4


def truncate_by_tokens(
    messages: List[Dict[str, str]],
    max_tokens: int,
    approx_tokens_per_char: float = 0.25,
) -> List[Dict[str, str]]:
    """
    Trunca la lista de mensajes para que no supere un límite de tokens.

    Elimina mensajes del principio (los más antiguos) hasta que el total
    estimado de tokens sea <= max_tokens.

    Args:
        messages: Lista de mensajes con formato [{"role": "...", "content": "..."}].
        max_tokens: Límite máximo de tokens.
        approx_tokens_per_char: Factor de conversión (defecto: 0.25 ≈ 4 chars/token).

    Returns:
        Lista truncada de mensajes.
    """
    if not messages:
        return messages

    # Calcular tokens totales
    total_tokens = sum(
        len(msg["content"]) * approx_tokens_per_char
        for msg in messages
    )

    if total_tokens <= max_tokens:
        return messages

    # Eliminar mensajes desde el principio hasta cumplir el límite
    truncated = messages.copy()
    while truncated:
        # Calcular tokens de la lista actual
        current_tokens = sum(
            len(msg["content"]) * approx_tokens_per_char
            for msg in truncated
        )
        if current_tokens <= max_tokens:
            break
        # Eliminar el mensaje más antiguo (primero de la lista)
        truncated.pop(0)

    return truncated


def format_messages(
    messages: List[Dict[str, str]],
    include_roles: bool = True,
    separator: str = "\n",
) -> str:
    """
    Formatea una lista de mensajes como texto plano.

    Args:
        messages: Lista de mensajes.
        include_roles: Si se incluye el rol (Usuario/Asistente) en el texto.
        separator: Separador entre mensajes.

    Returns:
        Texto formateado.
    """
    if not messages:
        return ""

    lines = []
    for msg in messages:
        if include_roles:
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content']}")
        else:
            lines.append(msg["content"])

    return separator.join(lines)
