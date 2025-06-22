from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Classe base para todos os agentes.
    Define a interface comum que cada agente deve implementar.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def _run_async(self, query: str) -> str:
        """
        Executa a lógica principal do agente de forma assíncrona.

        Args:
            query (str): A entrada (pergunta/tarefa) para o agente.

        Returns:
            str: A saída (resposta) do agente.
        """
        pass
    
    def run(self, query: str) -> str:
        """
        Método síncrono opcional que pode ser implementado pelos agentes.
        Por padrão, não é obrigatório implementar.
        """
        import asyncio
        return asyncio.run(self._run_async(query))