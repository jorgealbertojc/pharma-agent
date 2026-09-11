# app/entrypoints/cli.py
"""
Command-line interface (CLI) entrypoint for the pharmacy agent.

Provides an interactive mode (question/answer loop) and a single-query
mode by passing the question as an argument.
"""

import argparse
import logging
import sys

from app.agent.executor import AgentExecutor

# Configure logging for CLI (quieter by default)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def run_interactive() -> None:
    """
    Run the agent in interactive mode (infinite loop).
    """
    executor = AgentExecutor()
    executor.run()


def run_single_query(question: str) -> None:
    """
    Run a single query and print the response.

    Args:
        question: User's question.
    """
    executor = AgentExecutor()
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
                print("Could not generate a response.", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Main entrypoint for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Pharmacy agent - query medications, inventory, and suggestions."
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Single question for the agent (if omitted, enters interactive mode).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logs).",
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
