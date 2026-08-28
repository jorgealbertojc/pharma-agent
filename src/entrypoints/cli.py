# src/entrypoints/cli.py
"""
Punto de entrada para la línea de comandos (CLI) del agente farmacéutico.

Permite ejecutar el agente en modo interactivo (bucle de preguntas/respuestas)
o realizar una consulta única pasando la pregunta como argumento.
"""

import argparse
import sys
import logging

from src.agent.executor import AgentExecutor
from src.core.config import settings

# Configurar logging para CLI (más silencioso por defecto)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def run_interactive() -> None:
    """
    Ejecuta el agente en modo interactivo (bucle infinito).
    """
    executor = AgentExecutor()
    executor.run()


def run_single_query(question: str) -> None:
    """
    Ejecuta una consulta única y muestra la respuesta.

    Args:
        question: Pregunta del usuario.
    """
    executor = AgentExecutor()
    # Procesar la pregunta directamente (reutiliza la lógica interna)
    try:
        executor._process_question(question)
        final_answer = executor.state.get("final_answer") if executor.state else None
        if final_answer:
            print(final_answer)
        else:
            error = executor.state.get("error") if executor.state else None
            if error:
                print(f"Error: {error}", file=sys.stderr)
            else:
                print("No se pudo generar una respuesta.", file=sys.stderr)
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Punto de entrada principal del CLI.
    """
    parser = argparse.ArgumentParser(
        description="Agente farmacéutico - consulta medicamentos, inventario y sugerencias."
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Pregunta única para el agente (si no se proporciona, entra en modo interactivo)."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activar modo debug (logs más detallados)."
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.question:
        run_single_query(args.question)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
