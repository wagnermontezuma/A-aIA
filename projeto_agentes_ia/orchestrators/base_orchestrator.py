from abc import ABC, abstractmethod
from typing import List
from agents.base_agent import BaseAgent

class BaseOrchestrator(ABC):
    """
    Classe base abstrata para todos os orquestradores.
    Define a interface para coordenar o fluxo de trabalho entre agentes.
    """
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents

    @abstractmethod
    def execute(self, initial_query: str) -> str:
        """
        Executa o fluxo de trabalho orquestrado.

        Args:
            initial_query (str): A consulta inicial para iniciar o fluxo.

        Returns:
            str: O resultado final do fluxo de trabalho.
        """
        pass