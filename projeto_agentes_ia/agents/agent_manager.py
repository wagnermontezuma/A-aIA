from typing import Dict, Optional
from .adk_agent_with_memory import ADKAgentWithMemory
from .langchain_agent_with_memory import LangChainGeminiAgent  # Nova importação
from .base_agent import BaseAgent
import os

class AgentManager:
    """
    Gerenciador para múltiplos agentes de IA.
    Permite alternar entre diferentes tipos de agentes.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.current_agent: Optional[str] = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Inicializa todos os agentes disponíveis com Google Gemini unificado."""
        instruction = """
        Você é um assistente de IA inteligente e prestativo.
        Responda às perguntas dos usuários de forma clara, precisa e informativa.
        Se você não souber algo, seja honesto sobre isso.
        Mantenha suas respostas organizadas e fáceis de entender.
        Use sua memória para fornecer respostas mais personalizadas e contextuais.
        """
        
        # Inicializar agente ADK com memória (Google Gemini)
        try:
            if os.getenv("GOOGLE_API_KEY"):
                self.agents["adk"] = ADKAgentWithMemory(instruction=instruction)
                print("✅ Agente ADK (Google Gemini) inicializado com sucesso")
            else:
                print("⚠️  Agente ADK não inicializado - GOOGLE_API_KEY não encontrada")
        except Exception as e:
            print(f"❌ Erro ao inicializar agente ADK: {e}")
        
        # Inicializar agente LangChain com Gemini (mesmo modelo do ADK)
        try:
            if os.getenv("GOOGLE_API_KEY"):
                self.agents["langchain"] = LangChainGeminiAgent(instruction=instruction)
                print("✅ Agente LangChain (Google Gemini) inicializado com sucesso")
            else:
                print("⚠️  Agente LangChain não inicializado - GOOGLE_API_KEY não encontrada")
        except Exception as e:
            print(f"❌ Erro ao inicializar agente LangChain-Gemini: {e}")
        
        # Definir agente padrão
        if "adk" in self.agents:
            self.current_agent = "adk"
        elif "langchain" in self.agents:
            self.current_agent = "langchain"
        else:
            print("❌ Nenhum agente foi inicializado com sucesso")
    
    def set_agent(self, agent_type: str) -> bool:
        """
        Define qual agente usar.
        
        Args:
            agent_type: "adk" ou "langchain"
            
        Returns:
            True se o agente foi definido com sucesso, False caso contrário
        """
        if agent_type in self.agents:
            self.current_agent = agent_type
            print(f"✅ Agente alterado para: {agent_type}")
            return True
            
        else:
            print(f"❌ Agente '{agent_type}' não disponível")
            return False
        
    def get_current_agent(self) -> Optional[BaseAgent]:
            """Retorna o agente atualmente selecionado."""
            if self.current_agent and self.current_agent in self.agents:
                return self.agents[self.current_agent]
            return None
        
    def get_agent_info(self) -> Dict:
        """Retorna informações sobre os agentes disponíveis."""
        info = {
            "available_agents": list(self.agents.keys()),
            "current_agent": self.current_agent,
            "agents_status": {}
        }
        
        for agent_type, agent in self.agents.items():
            info["agents_status"][agent_type] = {
                "name": agent.name,
                "available": True,
                "description": self._get_agent_description(agent_type)
            }
        
        return info
        
    def _get_agent_description(self, agent_type: str) -> str:
        """Retorna a descrição de um tipo de agente."""
        descriptions = {
            "adk": "Google ADK - Gemini 2.0 Flash com busca integrada e memória",
            "langchain": "LangChain + Google Gemini 2.0 Flash com ferramentas e memória avançada"
        }
        return descriptions.get(agent_type, "Agente de IA")
        
    def add_knowledge_to_current_agent(self, content: str, source: str = "user", metadata: dict = None):
        """Adiciona conhecimento ao agente atual."""
        current = self.get_current_agent()
        if current and hasattr(current, 'add_knowledge'):
            return current.add_knowledge(content, source, metadata)
        return None
        
    def set_user_context(self, user_id: str, session_id: str = None):
        """Define contexto do usuário para todos os agentes."""
        for agent in self.agents.values():
            if hasattr(agent, 'set_user_context'):
                agent.set_user_context(user_id, session_id)
        
    async def run_current_agent_with_context(self, query: str, user_id: str, session_id: str = None) -> str:
        """Executa o agente atual com contexto de usuário."""
        current = self.get_current_agent()
        if not current:
            return "Nenhum agente disponível no momento."
        
        try:
            # Definir contexto se o agente suportar
            if hasattr(current, 'set_user_context'):
                current.set_user_context(user_id, session_id)
            
            # Executar o método assíncrono
            return await current._run_async(query)
            
        except Exception as e:
            return f"Erro ao executar agente: {str(e)}"