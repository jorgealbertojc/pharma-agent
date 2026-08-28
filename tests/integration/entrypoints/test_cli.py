"""
Tests de integración para el punto de entrada CLI.

Estos tests verifican el comportamiento del CLI sin usar subprocess
(excepto para el modo interactivo), capturando la salida directamente
con capsys y monkeypatch.
"""

import sys
import subprocess
import pytest

from src.entrypoints.cli import main


class TestCLI:
    """Suite de pruebas para el CLI."""

    def test_cli_help(self, capsys, monkeypatch) -> None:
        """
        Given: El CLI ejecutado con el argumento --help.
        When: Se ejecuta main() con sys.argv modificado.
        Then: Se muestra la ayuda y el código de salida es 0.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--help'])

        # When
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Then
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Agente farmacéutico" in captured.out

    def test_cli_question_single_query(self, capsys, monkeypatch) -> None:
        """
        Given: Una pregunta válida pasada con --question.
        When: Se ejecuta main() con la pregunta.
        Then: Se imprime una respuesta no vacía sin errores.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--question', 'ibuprofeno'])

        # When
        main()

        # Then
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0
        assert "Error" not in captured.out

    def test_cli_question_with_debug(self, capsys, monkeypatch) -> None:
        """
        Given: Una pregunta con el flag --debug.
        When: Se ejecuta main() con la pregunta y debug activado.
        Then: No hay errores y la salida contiene al menos la respuesta.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--question', 'paracetamol', '--debug'])

        # When
        main()

        # Then
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0

    def test_cli_question_unknown_product(self, capsys, monkeypatch) -> None:
        """
        Given: Una pregunta sobre un producto inexistente.
        When: Se ejecuta main() con esa pregunta.
        Then: El agente maneja la situación sin errores y devuelve un mensaje informativo.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--question', 'producto_inexistente_xyz'])

        # When
        main()

        # Then
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0

    @pytest.mark.skip(reason="El modo interactivo requiere entrada estándar y timeout, no es adecuado para CI/local")
    def test_cli_no_question_enters_interactive_mode(self) -> None:
        """
        Given: El CLI ejecutado sin --question.
        When: Se ejecuta el comando con subprocess y timeout de 8 segundos.
        Then: Entra en modo interactivo y muestra el mensaje de bienvenida.
        """
        # Given / When
        try:
            subprocess.run(
                [sys.executable, "-m", "src.entrypoints.cli"],
                capture_output=True,
                text=True,
                timeout=240,  # Aumentado para dar tiempo a la inicialización
            )
        except subprocess.TimeoutExpired as e:
            # Then
            output = e.stdout if e.stdout else ""
            assert "Agente farmacéutico iniciado" in output, \
                f"El mensaje de bienvenida no apareció en la salida (recibido: {output[:100]})"
        else:
            pytest.fail("El CLI debería haber entrado en modo interactivo y no terminar inmediatamente.")
