# finsight/backend/agents/__init__.py
"""
This package contains the AI agents for the FinSight application.
The `run_orchestrator` function is the main entry point.
"""
from .orchestrator import run_orchestrator

__all__ = ["orchestrator"]
