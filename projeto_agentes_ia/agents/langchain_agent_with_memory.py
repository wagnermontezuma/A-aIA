from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
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

class LangChainAgentWithMemory(BaseAgent):
    """
    Agente LangChain com capacidades de memória conversacional e RAG.
    Implementação completa e funcional com assinaturas de método corretas.
    """

    def __init__(self, instruction: str = None):
        load_dotenv()

        try:
            # Verificar API keys
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")

            # Inicializar sistemas de memória
            self.memory_manager = MemoryManager()
            self.rag_manager = RAGManager(use_advanced=False)  # Usar versão simples

            # Configurar o modelo LLM
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=openai_key
            )

            # Usar memória personalizada
            self.conversation_history = []
            self.max_history = 5

            # Template de prompt otimizado para memória
            self.prompt_template = ChatPromptTemplate.from_template("""
Você é um assistente de IA inteligente e prestativo com memória conversacional avançada.

CAPACIDADES ESPECIAIS:
1. Você pode lembrar de conversas anteriores com o usuário
2. Você tem acesso a conhecimento específico através do sistema RAG
3. Você pode raciocinar sobre informações complexas
4. Você mantém contexto entre diferentes sessões

INSTRUÇÕES DE COMPORTAMENTO:
- SEMPRE considere o contexto de conversas anteriores quando relevante
- Use o conhecimento específico disponível para dar respostas mais precisas
- Seja consistente com informações fornecidas anteriormente
- Se você reconhecer informações do usuário baseadas no contexto, mencione isso NATURALMENTE
- Mantenha um tom amigável e personalizado baseado no histórico
- Demonstre que você lembra de detalhes importantes sobre o usuário

INSTRUÇÃO ESPECÍFICA:
{instruction}

CONTEXTO ADICIONAL (se disponível):
{context}

HISTÓRICO DA CONVERSA ATUAL:
{history}

Pergunta atual: {input}

Resposta (considerando TODO o contexto acima):""")

            self.instruction = instruction or "Seja útil, preciso e forneça respostas bem estruturadas, sempre considerando o contexto e a memória."
            self.user_id = "default_user"
            self.session_id = None

            super().__init__(name="LangChainAgentWithMemory")
            print(f"✅ {self.name} inicializado com sistemas de memória")

        except Exception as e:
            print(f"❌ Erro ao inicializar {self.name}: {e}")
            # Criar um agente simplificado em caso de erro
            super().__init__(name="LangChainAgentWithMemory (Modo Simplificado)")
            self.llm = None
            self.memory_manager = None
            self.rag_manager = None
            self.conversation_history = []

    def _format_history(self) -> str:
        """
        Formata o histórico de conversação para o prompt.
        CORREÇÃO: Método agora aceita 'self' corretamente.
        """
        if not self.conversation_history:
            return "Esta é uma nova conversa - nenhum histórico anterior disponível."

        history_parts = ["=== HISTÓRICO DA CONVERSA ATUAL ==="]
        for i, entry in enumerate(self.conversation_history[-self.max_history:], 1):
            history_parts.append(f"{i}. Usuário: {entry['user']}")
            history_parts.append(f"   Assistente: {entry['assistant'][:100]}...")
            history_parts.append("")

        return "\n".join(history_parts)

    def _add_to_history(self, user_message: str, assistant_response: str):
        """
        Adiciona uma interação ao histórico local.
        CORREÇÃO: Método agora aceita 'self' corretamente.
        """
        self.conversation_history.append({
            "user": user_message,
            "assistant": assistant_response
        })

        # Manter apenas as últimas interações
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        print(f"[{self.name}] Adicionado ao histórico local: {len(self.conversation_history)} interações")

    def _build_context(self, memory_context: str, rag_context: str, related_context: str) -> str:
        """
        Constrói o contexto completo para o agente.
        CORREÇÃO: Método agora aceita 'self' corretamente.
        """
        context_parts = []

        # Adicionar contexto de memória persistente se disponível
        if memory_context and "nova conversa" not in memory_context.lower():
            context_parts.append("=== MEMÓRIA DE CONVERSAS ANTERIORES ===")
            context_parts.append(memory_context)
            context_parts.append("")

        # Adicionar contexto RAG se disponível
        if rag_context:
            context_parts.append("=== CONHECIMENTO ESPECÍFICO RELEVANTE ===")
            context_parts.append(rag_context)
            context_parts.append("")

        # Adicionar conversas relacionadas se disponível
        if related_context:
            context_parts.append("=== CONVERSAS RELACIONADAS ANTERIORES ===")
            context_parts.append(related_context)
            context_parts.append("")

        return "\n".join(context_parts) if context_parts else ""

    def set_user_context(self, user_id: str, session_id: str = None):
        """Define o contexto do usuário para a sessão."""
        print(f"[{self.name}] Definindo contexto: user_id={user_id}, session_id={session_id}")
        self.user_id = user_id
        self.session_id = session_id or f"session_{user_id}_{hash(user_id) % 10000}"
        # Limpar histórico local ao trocar usuário/sessão
        self.conversation_history = []

    def add_knowledge(self, content: str, source: str = "user", metadata: dict = None):
        """Adiciona conhecimento ao sistema RAG."""
        if self.rag_manager:
            return self.rag_manager.add_knowledge(content, source, metadata)
        return None

    async def _run_async(self, query: str) -> str:
        """Método assíncrono para executar o agente com memória completa."""
        if not self.llm:
            return "Agente LangChain não está disponível. Verifique a configuração da API key."

        try:
            print(f"[{self.name}] Processando consulta com memória: '{query[:50]}...'")

            # Obter contexto de memória persistente se disponível
            full_context = ""
            if self.memory_manager:
                try:
                    print(f"[{self.name}] Buscando contexto de memória para user_id={self.user_id}")

                    memory_context = self.memory_manager.get_context_for_agent(
                        self.user_id, self.session_id, limit=3
                    )

                    rag_context = ""
                    if self.rag_manager:
                        rag_context = self.rag_manager.get_relevant_context(query, limit=2)

                    related_context = self.memory_manager.search_relevant_context(
                        self.user_id, query, limit=2
                    )

                    full_context = self._build_context(memory_context, rag_context, related_context)

                    if full_context:
                        print(f"[{self.name}] Contexto de memória aplicado com sucesso ({len(full_context)} caracteres)")
                    else:
                        print(f"[{self.name}] Nenhum contexto de memória encontrado")

                except Exception as memory_error:
                    print(f"[{self.name}] Erro ao aplicar contexto de memória: {memory_error}")
                    # Continuar sem contexto se houver erro

            # Formatar histórico local da sessão atual
            history = self._format_history()

            # Criar prompt final com todos os contextos
            final_prompt = self.prompt_template.format(
                instruction=self.instruction,
                context=full_context,
                history=history,
                input=query
            )

            print(f"[{self.name}] Executando LLM com contexto completo")

            # Executar o LLM
            response = await self.llm.ainvoke(final_prompt)
            final_response = response.content if hasattr(response, 'content') else str(response)

            # Adicionar ao histórico local da sessão
            self._add_to_history(query, final_response)

            # Salvar na memória persistente se disponível
            if self.memory_manager:
                try:
                    self.memory_manager.save_interaction(
                        user_id=self.user_id,
                        session_id=self.session_id or "default_session",
                        user_message=query,
                        agent_response=final_response,
                        agent_type="LangChain",
                        metadata={
                            "has_rag_context": bool(self.rag_manager and full_context),
                            "session_history_length": len(self.conversation_history)
                        }
                    )
                    print(f"[{self.name}] Interação salva na memória persistente")
                except Exception as save_error:
                    print(f"[{self.name}] Erro ao salvar na memória: {save_error}")

            print(f"[{self.name}] Resposta gerada com sucesso")
            return final_response

        except Exception as e:
            error_msg = f"Erro ao executar agente LangChain: {str(e)}"
            print(f"[{self.name}] {error_msg}")

            # Fallback simples
            try:
                print(f"[{self.name}] Tentando fallback simples")
                response = await self.llm.ainvoke(f"Responda à seguinte pergunta: {query}")
                return response.content if hasattr(response, 'content') else str(response)
            except Exception:
                return f"Erro no agente LangChain: {error_msg}"