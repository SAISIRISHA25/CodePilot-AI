"""Compatibility shim for the planning agent.

The original implementation lives in the typo-named module
``plannung_agent.py``. This module preserves the public import path the
rest of the application expects.
"""

from app.agents.plannung_agent import PlanningAgent

__all__ = ["PlanningAgent"]
