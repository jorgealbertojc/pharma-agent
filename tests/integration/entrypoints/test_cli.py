# tests/integration/entrypoints/test_cli.py
"""
Integration tests for the CLI entrypoint.

These tests verify the CLI behavior without using subprocess
(except for interactive mode), capturing output directly
with capsys and monkeypatch.
"""

import subprocess
import sys

import pytest

from app.entrypoints.cli import main


class TestCLI:
    """Test suite for the CLI."""

    def test_cli_help(self, capsys, monkeypatch) -> None:
        """
        Given: The CLI executed with the --help argument.
        When: main() is run with modified sys.argv.
        Then: Help is displayed and exit code is 0.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--help'])

        # When
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Then
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Pharmacy agent" in captured.out  # Updated to match new English description

    def test_cli_question_single_query(self, capsys, monkeypatch) -> None:
        """
        Given: A valid question passed with --question.
        When: main() is run with the question.
        Then: A non-empty response is printed without errors.
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
        Given: A question with the --debug flag.
        When: main() is run with the question and debug enabled.
        Then: No errors occur and the output contains at least the response.
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
        Given: A question about a non-existent product.
        When: main() is run with that question.
        Then: The agent handles the situation without errors and returns an informative message.
        """
        # Given
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--question', 'producto_inexistente_xyz'])

        # When
        main()

        # Then
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0

    @pytest.mark.skip(reason="Interactive mode requires stdin and timeout; not suitable for CI/local")
    def test_cli_no_question_enters_interactive_mode(self) -> None:
        """
        Given: The CLI executed without --question.
        When: The command is run with subprocess and an 8-second timeout.
        Then: It enters interactive mode and shows the welcome message.
        """
        # Given / When
        try:
            subprocess.run(
                [sys.executable, "-m", "app.entrypoints.cli"],
                capture_output=True,
                text=True,
                timeout=240,  # Increased to allow initialization
            )
        except subprocess.TimeoutExpired as e:
            # Then
            output = e.stdout if e.stdout else ""
            assert "Pharmacy agent started" in output, \
                f"Welcome message did not appear in output (received: {output[:100]})"
        else:
            pytest.fail("CLI should have entered interactive mode and not terminated immediately.")
