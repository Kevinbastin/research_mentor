from __future__ import annotations

"""
Main orchestrator shim.

This keeps the project layout aligned with the plan while deferring to the
existing CLI entrypoint. You can run:

  uv run python main.py

or the canonical script:

  uv run academic-research-mentor
"""

from academic_research_mentor.cli import main as cli_main


if __name__ == "__main__":
    cli_main()
