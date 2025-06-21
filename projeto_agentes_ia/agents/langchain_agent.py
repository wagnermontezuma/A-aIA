# agents/langchain_agent.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_tavily.tavily_search import TavilySearch  # Nova importação
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from .base_agent import BaseAgent
import asyncio
import os
from dotenv import load_dotenv

class LangChainAgent(BaseAgent):
    """
    Implementação corrigida do agente LangChain com Tavily atualizado.
    """
    
    def __init__(self, instruction: str = None):
        load_dotenv()
        
        try:
            # Verificar se as API keys estão configuradas
            openai_key = os.getenv("OPENAI_API_KEY")
            tavily_key = os.getenv("TAVILY_API_KEY")
            
            if not openai_key:
                raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
            if not tavily_key:
                raise ValueError("TAVILY_API_KEY não encontrada no arquivo .env")
            
            # Configurar o modelo LLM
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",  # Modelo mais acessível
                temperature=0.1,
                api_key=openai_key
            )
            
            # Configurar ferramentas com a nova versão do Tavily
            self.search_tool = TavilySearch(
                max_results=3,
                api_key=tavily_key
            )
            
            self.tools = [self.search_tool]
            
            # Criar prompt personalizado (fallback se o hub não funcionar)
            prompt_template = """
            Você é um assistente de IA útil e experiente. Sua tarefa é responder às perguntas do usuário da melhor maneira possível, utilizando as ferramentas disponíveis quando necessário.

            Você tem acesso às seguintes ferramentas:
            {tools}

            Para responder à pergunta do usuário, siga este formato de raciocínio e ação (ReAct):

            Question: A pergunta do usuário.
            Thought: Pense passo a passo sobre como responder à pergunta. Considere se você precisa usar uma ferramenta.
            Action: O nome da ferramenta a ser usada (se necessário), deve ser uma das [{tool_names}]. Se não precisar de uma ferramenta, omita esta linha.
            Action Input: A entrada para a ferramenta (se uma ferramenta for usada). Se não precisar de uma ferramenta, omita esta linha.
            Observation: O resultado da ação (se uma ferramenta foi usada).
            ... (Este ciclo Thought/Action/Action Input/Observation pode se repetir)
            Thought: Agora que usei a(s) ferramenta(s) (ou determinei que não era necessário), posso formular a resposta final.
            Final Answer: A resposta final para a pergunta original do usuário.

            Se você não precisar usar uma ferramenta, vá diretamente para o Thought final e Final Answer.

            Instrução adicional: {instruction}

            Comece!

            Question: {input}
            Thought: {agent_scratchpad}
            """
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            
            # Criar o agente
            self.agent = create_react_agent(self.llm, self.tools, prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )
            
            super().__init__(name="LangChainAgent")
            print(f"✅ {self.name} inicializado com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar LangChainAgent: {e}")
            # Criar um agente simplificado sem ferramentas como fallback
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            ) if os.getenv("OPENAI_API_KEY") else None
            self.agent_executor = None
            super().__init__(name="LangChainAgent (Modo Simplificado)")
    
    def run(self, query: str) -> str:
        """
        Executa o agente LangChain de forma síncrona.
        """
        return asyncio.run(self._run_async(query))
    
    async def _run_async(self, query: str) -> str:
        """
        Método assíncrono para executar o agente LangChain.
        """
        try:
            print(f"[{self.name}] Processando consulta: '{query[:50]}...'")
            
            # Se o agente executor não está disponível, usar LLM diretamente
            if not self.agent_executor:
                if self.llm:
                    response = await self.llm.ainvoke(query)
                    return response.content
                else:
                    return "Agente LangChain não está configurado corretamente. Verifique as API keys."
            
            # Executar o agente com ferramentas
            result = await self.agent_executor.ainvoke({
                "input": query,
                "instruction": "Seja útil, preciso e forneça respostas bem estruturadas."
            })
            
            # Extrair a resposta
            response = result.get("output", "Não foi possível gerar uma resposta.")
            
            print(f"[{self.name}] Resposta gerada com sucesso")
            return response
            
        except Exception as e:
            error_msg = f"Erro ao executar agente LangChain: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            
            # Fallback: tentar usar apenas o LLM
            if self.llm:
                try:
                    response = await self.llm.ainvoke(f"Responda à seguinte pergunta: {query}")
                    return response.content
                except Exception as fallback_error:
                    return f"Erro no agente LangChain: {str(e)}"
            
            return f"Desculpe, ocorreu um erro: {error_msg}"