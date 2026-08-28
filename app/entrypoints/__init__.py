# src/entrypoints/__init__.py
"""
Punto de entrada de la aplicación.

Este paquete expone los diferentes puntos de entrada (entrypoints) de la aplicación:
- API REST (FastAPI)
- CLI (línea de comandos)
"""

from .api import app
from .cli import main

__all__ = [
    "app",   # Aplicación FastAPI para servir el agente
    "main",  # Función principal del CLI
]
