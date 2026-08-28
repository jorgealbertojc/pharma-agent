#!/usr/bin/env python3
"""
Punto de entrada principal del paquete `app`.

Permite ejecutar el agente en modo CLI (por defecto) o iniciar la API REST.
"""

import sys
import argparse

from app.entrypoints.cli import main as cli_main


def run_api() -> None:
    """Inicia el servidor API usando uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn no está instalado. Ejecuta: uv add uvicorn")
        sys.exit(1)
    uvicorn.run("app.entrypoints.api:app", host="0.0.0.0", port=8000, reload=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pharma Agent - entrada principal."
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Iniciar el servidor API en lugar del CLI interactivo."
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Pregunta única para el CLI (modo consulta única)."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activar modo debug."
    )

    args, unknown = parser.parse_known_args()

    if args.api:
        run_api()
    else:
        # Si se pasa --question, se delega al CLI con los argumentos originales
        if args.question:
            sys.argv = [sys.argv[0], "--question", args.question]
            if args.debug:
                sys.argv.append("--debug")
        cli_main()


if __name__ == "__main__":
    main()
