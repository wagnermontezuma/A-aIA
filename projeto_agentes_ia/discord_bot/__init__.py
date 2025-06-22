# discord_bot/__init__.py
"""
Bot Discord integrado com agentes ADK e LangChain.
Permite conversas inteligentes com memória através de comandos slash.
"""

from .bot import AgentEIABot, run_bot

__all__ = ['AgentEIABot', 'run_bot']