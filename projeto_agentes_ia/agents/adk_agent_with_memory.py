from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.genai import types
from .base_agent import BaseAgent
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório de memória ao path
memory_path = Path(__file__).parent.parent / "memory"
sys.path.append(str(memory_path))

from memory_manager import MemoryManager
from rag_system import RAGManager

class ADKAgentWithMemory(BaseAgent):
    """
    Agente ADK com capacidades de memória conversacional e RAG.
    Implementação completa e funcional com todos os métodos necessários.
    """

    def __init__(self, instruction: str = None):
        load_dotenv()

        try:
            # Inicializar sistemas de memória
            self.memory_manager = MemoryManager()
            self.rag_manager = RAGManager(use_advanced=False)  # Usar versão simples

            # Instrução base melhorada
            base_instruction = """
Você é um assistente de IA inteligente e prestativo com memória conversacional.

CAPACIDADES ESPECIAIS:
1. Você pode lembrar de conversas anteriores com o usuário
2. Você tem acesso a conhecimento específico através do sistema RAG
3. Você pode usar busca na internet quando necessário

INSTRUÇÕES DE COMPORTAMENTO:
- Sempre considere o contexto de conversas anteriores quando relevante
- Use o conhecimento específico disponível para dar respostas mais precisas
- Seja consistente com informações fornecidas anteriormente
- Se você lembrar de algo específico sobre o usuário, mencione isso naturalmente
- Mantenha um tom amigável e personalizado baseado no histórico

FORMATO DE RESPOSTA:
- Seja claro e organizado
- Use o contexto anterior quando apropriado
- Cite fontes quando usar conhecimento específico
"""

            final_instruction = f"{base_instruction}\n\nINSTRUÇÃO ESPECÍFICA:\n{instruction}" if instruction else base_instruction

            # Criar o agente ADK
            self.agent = Agent(
                name="adk_memory_agent",
                model="gemini-2.0-flash-exp",
                description="Agente ADK com memória conversacional e RAG",
                instruction=final_instruction,
                tools=[google_search]
            )

            # Configurações da aplicação
            self.app_name = "projeto_agentes_ia_memory"
            self.user_id = "default_user"

            # Inicializar serviços
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )

            super().__init__(name="ADKAgentWithMemory")
            print(f"✅ {self.name} inicializado com sistemas de memória")

        except Exception as e:
            print(f"❌ Erro ao inicializar {self.name}: {e}")
            # Criar um agente simplificado em caso de erro
            super().__init__(name="ADKAgentWithMemory (Modo Simplificado)")
            self.agent = None
            self.memory_manager = None
            self.rag_manager = None

    def set_user_context(self, user_id: str, session_id: str = None):
        """Define o contexto do usuário para a sessão."""
        self.user_id = user_id
        self.session_id = session_id or f"session_{user_id}_{hash(user_id) % 10000}"

    def add_knowledge(self, content: str, source: str = "user", metadata: dict = None):
        """Adiciona conhecimento ao sistema RAG."""
        if self.rag_manager:
            return self.rag_manager.add_knowledge(content, source, metadata)
        return None

    def _build_contextualized_query(self, query: str, memory_context: str,
                                      rag_context: str, related_context: str) -> str:
        """
        Constrói uma consulta contextualizada com memória e RAG.
        MÉTODO QUE ESTAVA AUSENTE - AGORA IMPLEMENTADO.
        """
        parts = []

        # Adicionar contexto de memória se disponível
        if memory_context and "nova conversa" not in memory_context.lower():
            parts.append("=== CONTEXTO DE CONVERSAS ANTERIORES ===")
            parts.append(memory_context)
            parts.append("")

        # Adicionar contexto RAG se disponível
        if rag_context:
            parts.append("=== CONHECIMENTO RELEVANTE ===")
            parts.append(rag_context)
            parts.append("")

        # Adicionar conversas relacionadas se disponível
        if related_context:
            parts.append("=== CONVERSAS RELACIONADAS ===")
            parts.append(related_context)
            parts.append("")

        # Construir a consulta final
        if parts:
            context_section = "\n".join(parts)
            contextualized_query = f"""{context_section}

=== NOVA PERGUNTA ===
{query}

=== INSTRUÇÕES ===
Responda considerando todo o contexto acima quando relevante.
Se você reconhecer informações do usuário baseadas no contexto, mencione isso naturalmente.
Seja consistente com informações fornecidas anteriormente."""
        else:
            contextualized_query = query

        return contextualized_query

    async def _run_async(self, query: str) -> str:
        """Método assíncrono que executa o agente com contexto de memória."""
        if not self.agent:
            return "Agente ADK não está disponível. Verifique a configuração."

        try:
            print(f"[{self.name}] Processando consulta: '{query[:50]}...'")

            # Gerar ID de sessão único
            session_id = getattr(self, 'session_id', None) or f"session_{abs(hash(query)) % 10000}"

            # Criar sessão
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=session_id
            )

            # Obter contexto de memória se disponível
            contextualized_query = query
            if self.memory_manager:
                try:
                    memory_context = self.memory_manager.get_context_for_agent(
                        self.user_id, session_id, limit=3
                    )

                    rag_context = ""
                    if self.rag_manager:
                        rag_context = self.rag_manager.get_relevant_context(query, limit=2)

                    related_context = self.memory_manager.search_relevant_context(
                        self.user_id, query, limit=2
                    )

                    contextualized_query = self._build_contextualized_query(
                        query, memory_context, rag_context, related_context
                    )

                    print(f"[{self.name}] Contexto de memória aplicado com sucesso")

                except Exception as memory_error:
                    print(f"[{self.name}] Erro ao aplicar contexto de memória: {memory_error}")
                    # Continuar sem contexto se houver erro

            # Preparar o conteúdo da mensagem
            content = types.Content(
                role='user',
                parts=[types.Part(text=contextualized_query)]
            )

            # Executar o agente
            events_async = self.runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=content
            )

            # Processar eventos assíncronos
            final_response = ""
            async for event in events_async:
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
                final_response = "Não foi possível obter uma resposta do agente."

            # Salvar interação na memória se disponível
            if self.memory_manager:
                try:
                    self.memory_manager.save_interaction(
                        user_id=self.user_id,
                        session_id=session_id,
                        user_message=query,
                        agent_response=final_response,
                        agent_type="ADK",
                        metadata={"has_rag_context": bool(self.rag_manager)}
                    )
                    print(f"[{self.name}] Interação salva na memória")
                except Exception as save_error:
                    print(f"[{self.name}] Erro ao salvar na memória: {save_error}")

            print(f"[{self.name}] Resposta gerada com sucesso")
            return final_response

        except Exception as e:
            error_msg = f"Erro ao executar agente: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            return f"Desculpe, ocorreu um erro: {error_msg}"