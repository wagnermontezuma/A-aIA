# agents/adk_agent.py
from google.adk.agents import Agent  # Use Agent ao invés de LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from .base_agent import BaseAgent
import asyncio
import os
from dotenv import load_dotenv

class SimpleADKAgent(BaseAgent):
    """
    Implementação corrigida do agente ADK que resolve o bug de sessão.
    Usa apenas métodos assíncronos para evitar problemas de threading.
    """

    def __init__(self, instruction: str):
        load_dotenv()

        # Usar Agent ao invés de LlmAgent (conforme documentação oficial)
        self.agent = Agent(
            name="simple_adk_agent",
            model="gemini-2.0-flash-exp",
            description="Um agente simples para responder consultas",
            instruction=instruction,
            tools=[google_search]  # Adicionar ferramentas se necessário
        )

        # Configurações da aplicação
        self.app_name = "projeto_agentes_ia"
        self.user_id = "test_user"

        # Inicializar serviços
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        super().__init__(name="SimpleADKAgent")

    def run(self, query: str) -> str:
        """
        Executa o agente de forma síncrona (wrapper para o método assíncrono).
        """
        return asyncio.run(self._run_async(query))

    async def _run_async(self, query: str) -> str:
        """
        Método assíncrono que executa o agente corretamente.
        """
        try:
            print(f"[{self.name}] Processando consulta: '{query[:50]}...'")

            # Gerar ID de sessão único
            session_id = f"session_{abs(hash(query)) % 10000}"

            # CORREÇÃO: Usar await para criar a sessão (conforme issue #117)
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )

            print(f"[{self.name}] Sessão criada: {session_id}")

            # Preparar o conteúdo da mensagem
            content = types.Content(
                role='user',
                parts=[types.Part(text=query)]
            )

            # CORREÇÃO: Usar run_async ao invés de run para evitar problemas de threading
            events_async = self.runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=content
            )

            # Processar eventos assíncronos
            final_response = ""
            async for event in events_async:
                print(f"[{self.name}] Evento recebido: {type(event).__name__}")

                if event.is_final_response():
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            if hasattr(event.content.parts, 'text'):
                                final_response = event.content.parts.text
                            elif isinstance(event.content.parts, list):
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        final_response += part.text
                        elif hasattr(event.content, 'text'):
                            final_response = event.content.text
                    break

            if not final_response:
                return "Não foi possível obter uma resposta do agente."

            print(f"[{self.name}] Resposta gerada com sucesso")
            return final_response

        except Exception as e:
            error_msg = f"Erro ao executar agente: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            return f"Desculpe, ocorreu um erro: {error_msg}"