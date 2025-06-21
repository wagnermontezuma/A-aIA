from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from agents.langchain_agent import LangChainAgent

# Define o estado do grafo: um dicionário que será passado entre os nós.
class AgentState(TypedDict):
    query: str
    next_node: str
    result: str

class LangGraphOrchestrator:
    """Orquestrador que usa LangGraph para gerenciar um fluxo de trabalho."""
    
    def __init__(self):
        # 1. Definir os agentes (nós do grafo)
        router_template = """Você é um roteador de tarefas. Com base na consulta do usuário, decida se a próxima etapa deve ser uma 'pesquisa' ou 'finalizar'. Responda apenas com 'pesquisa' ou 'finalizar'. Consulta: {query}"""
        self.router_agent = LangChainAgent("RouterAgent", "gpt-3.5-turbo", router_template)

        search_template = """Você é um assistente de pesquisa. Pesquise e responda à seguinte consulta: {query}"""
        self.search_agent = LangChainAgent("SearchAgent", "gpt-3.5-turbo", search_template)

        # 2. Definir as funções dos nós
        def router_node(state: AgentState):
            next_step = self.router_agent.run(state['query'])
            return {"next_node": next_step.lower()}

        def search_node(state: AgentState):
            result = self.search_agent.run(state['query'])
            return {"result": result}
        
        # 3. Construir o grafo
        workflow = StateGraph(AgentState)
        workflow.add_node("router", router_node)
        workflow.add_node("searcher", search_node)

        # 4. Definir as arestas (fluxo)
        workflow.set_entry_point("router")
        
        # Aresta condicional: decide para onde ir a partir do roteador
        def decide_next_node(state: AgentState):
            if state['next_node'] == 'pesquisa':
                return "searcher"
            return END

        workflow.add_conditional_edges("router", decide_next_node)
        workflow.add_edge("searcher", END)
        
        # Compila o grafo em um objeto executável
        self.app = workflow.compile()

    def execute(self, initial_query: str) -> str:
        final_state = self.app.invoke({"query": initial_query})
        return final_state.get("result", "O fluxo terminou sem um resultado claro.")