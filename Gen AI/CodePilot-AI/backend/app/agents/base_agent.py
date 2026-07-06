"""Compatibility shim for the agent base class.

The rest of the application imports this module name. The concrete
implementation remains in ``base_agents.py`` so existing architecture is
preserved.
"""

from app.agents.base_agents import BaseAgent

__all__ = ["BaseAgent"]
