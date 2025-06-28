# agents/langchain_agent_with_memory.py - Versão com Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchResults
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

class LangChainGeminiAgent(BaseAgent):
    """
    Agente LangChain com Google Gemini, memória conversacional e ferramentas de busca.
    Unifica o uso do Gemini em ambos os agentes (ADK e LangChain).
    """
    
    def __init__(self, instruction: str = None):
        load_dotenv()
        
        try:
            # Verificar API key do Google (mesma do ADK)
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env")
            
            # Inicializar sistemas de memória
            self.memory_manager = MemoryManager()
            self.rag_manager = RAGManager(use_advanced=False)
            
            # Configurar o modelo Gemini via LangChain
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",  # Mesmo modelo do ADK
                temperature=0.1,
                google_api_key=google_api_key,
                convert_system_message_to_human=True  # Compatibilidade com system messages
            )
            
            # Configurar ferramentas de busca
            self.tools = []
            try:
                # Usar DuckDuckGo como ferramenta de busca (gratuita)
                self.search_tool = DuckDuckGoSearchResults(
                    max_results=3,
                    backend="api"
                )
                self.tools.append(self.search_tool)
                print(f"✅ Ferramenta de busca DuckDuckGo configurada")
            except Exception as e:
                print(f"⚠️ Erro ao configurar busca: {e}")
            
            # Usar memória personalizada para histórico da sessão
            self.conversation_history = []
            self.max_history = 5
            
            # Template de prompt otimizado para Gemini
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", """Você é um assistente de IA inteligente e prestativo com memória conversacional e acesso à internet.

MODELO: Google Gemini 2.0 Flash (via LangChain)

CAPACIDADES ESPECIAIS:
1. Você pode lembrar de conversas anteriores com o usuário
2. Você tem acesso a conhecimento específico através do sistema RAG
3. Você pode buscar informações atualizadas na internet quando necessário
4. Você mantém contexto entre diferentes sessões
5. Você usa o mesmo modelo Gemini que o agente ADK

INSTRUÇÕES DE COMPORTAMENTO:
- SEMPRE considere o contexto de conversas anteriores quando relevante
- Use ferramentas de busca na internet para informações atualizadas, notícias, eventos atuais
- Use o conhecimento específico disponível para dar respostas mais precisas
- Seja consistente com informações fornecidas anteriormente
- Se você reconhecer informações do usuário baseadas no contexto, mencione isso NATURALMENTE
- Mantenha um tom amigável e personalizado baseado no histórico
- Demonstre que você lembra de detalhes importantes sobre o usuário

QUANDO USAR BUSCA NA INTERNET:
- Para informações atuais (notícias, eventos, preços, horários)
- Para verificar fatos recentes
- Para informações específicas que podem ter mudado
- Para responder perguntas sobre eventos atuais

VANTAGENS DO GEMINI:
- Modelo multimodal avançado
- Integração nativa com ferramentas Google
- Performance otimizada
- Mesmo modelo usado pelo agente ADK

INSTRUÇÃO ESPECÍFICA:
{instruction}

CONTEXTO ADICIONAL (se disponível):
{context}"""),
                
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Criar agente com ferramentas se disponíveis
            if self.tools:
                self.agent = create_tool_calling_agent(
                    llm=self.llm,
                    tools=self.tools,
                    prompt=self.prompt_template
                )
                
                self.agent_executor = AgentExecutor(
                    agent=self.agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3,
                    return_intermediate_steps=False
                )
                print(f"✅ Agente LangChain-Gemini com ferramentas criado")
            else:
                # Agente sem ferramentas como fallback
                self.agent = None
                self.agent_executor = None
                print(f"⚠️ Agente LangChain-Gemini criado sem ferramentas")
            
            self.instruction = instruction or "Seja útil, preciso e forneça respostas bem estruturadas, sempre considerando o contexto e a memória. Use busca na internet quando necessário para informações atualizadas."
            self.user_id = "default_user"
            self.session_id = None
            
            super().__init__(name="LangChainGeminiAgent")
            print(f"✅ {self.name} inicializado com Google Gemini 2.0 Flash")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar {self.name}: {e}")
            # Criar um agente simplificado em caso de erro
            super().__init__(name="LangChainGeminiAgent (Modo Simplificado)")
            self.llm = None
            self.memory_manager = None
            self.rag_manager = None
            self.conversation_history = []
            self.agent_executor = None
    
    def _format_chat_history(self) -> list:
        """Formata o histórico para o formato de mensagens do LangChain."""
        if not self.conversation_history:
            return []
        
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = []
        for entry in self.conversation_history[-self.max_history:]:
            messages.append(HumanMessage(content=entry['user']))
            messages.append(AIMessage(content=entry['assistant']))
        
        return messages
    
    def _add_to_history(self, user_message: str, assistant_response: str):
        """Adiciona uma interação ao histórico local."""
        self.conversation_history.append({
            "user": user_message,
            "assistant": assistant_response
        })
        
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        print(f"[{self.name}] Adicionado ao histórico local: {len(self.conversation_history)} interações")
    
    def _build_context(self, memory_context: str, rag_context: str, related_context: str) -> str:
        """Constrói o contexto completo para o agente."""
        context_parts = []
        
        if memory_context and "nova conversa" not in memory_context.lower():
            context_parts.append("=== MEMÓRIA DE CONVERSAS ANTERIORES ===")
            context_parts.append(memory_context)
            context_parts.append("")
        
        if rag_context:
            context_parts.append("=== CONHECIMENTO ESPECÍFICO RELEVANTE ===")
            context_parts.append(rag_context)
            context_parts.append("")
        
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
        self.conversation_history = []
    
    def add_knowledge(self, content: str, source: str = "user", metadata: dict = None):
        """Adiciona conhecimento ao sistema RAG."""
        if self.rag_manager:
            return self.rag_manager.add_knowledge(content, source, metadata)
        return None
    
    async def _run_async(self, query: str) -> str:
        """Método assíncrono para executar o agente com memória e Gemini."""
        if not self.llm:
            return "Agente LangChain-Gemini não está disponível. Verifique a configuração da API key."
        
        try:
            print(f"[{self.name}] Processando consulta com Gemini: '{query[:50]}...'")
            
            # Obter contexto de memória persistente
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
                    
                except Exception as memory_error:
                    print(f"[{self.name}] Erro ao aplicar contexto de memória: {memory_error}")
            
            # Usar agente com ferramentas se disponível
            if self.agent_executor:
                print(f"[{self.name}] Executando agente Gemini com ferramentas")
                
                # Formatar histórico para o agente
                chat_history = self._format_chat_history()
                
                # Executar consulta com o agente executor
                response = await self.agent_executor.ainvoke({
                    "input": query,
                    "context": full_context,
                    "instruction": self.instruction,
                    "chat_history": chat_history
                })
                
                final_response = response.get("output", "Não foi possível gerar uma resposta.")
                
            else:
                # Fallback para LLM direto sem ferramentas
                print(f"[{self.name}] Executando Gemini direto (sem ferramentas)")
                
                # Formatar histórico
                history = self._format_chat_history()
                
                # Criar mensagens para o Gemini
                messages = []
                
                # Adicionar system message
                system_content = self.prompt_template.messages[0].format(
                    instruction=self.instruction,
                    context=full_context
                )
                messages.append(("system", system_content))
                
                # Adicionar histórico
                messages.extend([(msg.type, msg.content) for msg in history])
                
                # Adicionar pergunta atual
                messages.append(("human", query))
                
                response = await self.llm.ainvoke(messages)
                final_response = response.content if hasattr(response, 'content') else str(response)
            
            # Adicionar ao histórico local
            self._add_to_history(query, final_response)
            
            # Salvar na memória persistente
            if self.memory_manager:
                try:
                    self.memory_manager.save_interaction(
                        user_id=self.user_id,
                        session_id=self.session_id or "default_session",
                        user_message=query,
                        agent_response=final_response,
                        agent_type="LangChain-Gemini",
                        metadata={
                            "has_rag_context": bool(self.rag_manager and full_context),
                            "has_search_tools": bool(self.tools),
                            "model": "gemini-2.0-flash-exp",
                            "session_history_length": len(self.conversation_history)
                        }
                    )
                    print(f"[{self.name}] Interação salva na memória persistente")
                except Exception as save_error:
                    print(f"[{self.name}] Erro ao salvar na memória: {save_error}")
            
            print(f"[{self.name}] Resposta gerada com Gemini com sucesso")
            return final_response
            
        except Exception as e:
            error_msg = f"Erro ao executar agente LangChain-Gemini: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            
            # Fallback simples
            try:
                print(f"[{self.name}] Tentando fallback simples com Gemini")
                response = await self.llm.ainvoke([("human", f"Responda à seguinte pergunta: {query}")])
                return response.content if hasattr(response, 'content') else str(response)
            except Exception:
                return f"Erro no agente LangChain-Gemini: {error_msg}"