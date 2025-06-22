# agents/conversational_adk_agent.py
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
# Removendo imports relacionados ao Runner e SessionService
# from google.adk.runner import Runner
# from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part # Mantendo Content e Part para criar o input
from .base_agent import BaseAgent
import os
from dotenv import load_dotenv
import asyncio
# Importando InvocationContext, necessário para run_async
from google.adk.types import InvocationContext

class ConversationalADKAgent(BaseAgent):
    """
    Agente ADK especializado em conversação inteligente usando Gemini 2.5 Flash.
    Otimizado para fornecer as melhores respostas com capacidades de busca.
    """

    def __init__(self, name: str = "ConversationalAgent"):
        load_dotenv()

        # Instrução detalhada para otimizar a qualidade das respostas
        instruction = """
        Você é um assistente conversacional altamente inteligente e útil. Sua missão é fornecer sempre a melhor resposta possível para o usuário.

        DIRETRIZES PARA EXCELÊNCIA:
        1. COMPREENSÃO: Analise cuidadosamente a pergunta do usuário para entender o contexto e a intenção
        2. PESQUISA: Use a ferramenta de busca quando precisar de informações atualizadas ou específicas
        3. RACIOCÍNIO: Aplique pensamento crítico e lógico para estruturar sua resposta
        4. CLAREZA: Seja claro, conciso e organize sua resposta de forma lógica
        5. PRECISÃO: Forneça informações precisas e cite fontes quando apropriado
        6. PERSONALIZAÇÃO: Adapte o tom e nível de detalhe ao contexto da pergunta
        7. COMPLETUDE: Certifique-se de responder completamente à pergunta

        COMPORTAMENTOS ESPERADOS:
        - Se a pergunta for ambígua, peça esclarecimentos
        - Para tópicos complexos, divida a resposta em seções organizadas
        - Para informações técnicas, forneça exemplos práticos quando possível
        - Sempre mantenha um tom profissional e prestativo
        - Se não souber algo, seja honesto e ofereça alternativas

        Lembre-se: Sua meta é ser o melhor assistente possível, fornecendo valor real em cada interação.
        """

        # Configuração do agente com Gemini 2.5 Flash
        self.agent = LlmAgent(
            model="gemini-2.5-flash",  # Modelo gratuito mais recente
            name="conversational_expert_agent",
            description="Agente especializado em conversação inteligente e respostas de alta qualidade",
            instruction=instruction,
            tools=[google_search]  # Ferramenta de busca para informações atualizadas
        )

        super().__init__(name=name)

        # Histórico de conversação para contexto
        self.conversation_history = []

    async def run(self, query: str, maintain_context: bool = True) -> str:
        """
        Executa o agente conversacional com a consulta fornecida de forma assíncrona.
        """
        try:
            print(f"[{self.name}] Processando consulta: '{query[:50]}...'")

            # Adiciona contexto da conversa anterior se solicitado
            if maintain_context and self.conversation_history:
                context_query = self._build_contextual_query(query)
            else:
                context_query = query

            # Criar um InvocationContext (simplificado para este exemplo)
            # Em uma aplicação real, o contexto seria gerenciado pelo Runner ou framework.
            # Aqui, criamos um contexto mínimo necessário para chamar run_async.
            # Pode ser necessário ajustar dependendo da implementação exata do ADK.
            # Assumindo que InvocationContext pode ser instanciado diretamente ou mockado.
            # Se a instanciação direta falhar, pode ser necessário um mock ou outra abordagem.
            try:
                 # Tentativa de instanciar InvocationContext (pode falhar dependendo da versão/estrutura)
                 # Importação movida para o topo
                 context = InvocationContext(
                     query=Content.from_parts([Part.from_text(context_query)]),
                     agent=self.agent, # Passa a si mesmo como agente atual
                     tool_results=[], # Sem resultados de ferramentas prévios neste ponto
                     app_name="projeto_agentes_ia",
                     user_id="test_user", # ID de usuário fixo para teste
                     session_id="test_session" # ID de sessão fixo para teste
                 )
            except TypeError as e:
                 print(f"[{self.name}] Erro ao instanciar InvocationContext diretamente: {e}")
                 print(f"[{self.name}] Tentando criar um contexto mínimo ou mockado...")
                 # Se a instanciação direta falhar, pode ser necessário um mock ou uma estrutura de contexto mínima
                 # Esta parte pode precisar de ajuste dependendo da API exata do InvocationContext
                 # Para um teste básico, podemos tentar passar apenas os argumentos essenciais se a classe permitir
                 # Ou pode ser necessário um mock se a classe for complexa ou interna
                 # Por enquanto, vamos assumir que a primeira tentativa de InvocationContext funciona ou que um mock seria usado em um teste real.
                 # Se o erro persistir aqui, precisaremos investigar como obter/criar um InvocationContext válido.
                 return f"Erro interno: Não foi possível criar o contexto de invocação necessário. Detalhes: {e}"


            # Executar o agente usando run_async
            event_stream = self.agent.run_async(parent_context=context)

            # Processar os eventos para obter a resposta final
            final_response = ""
            async for event in event_stream:
                # Verifica se o evento é uma resposta final e contém conteúdo de texto
                if hasattr(event, 'is_final_response') and event.is_final_response() and hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text # Concatenar partes de texto
                    # Se encontrarmos uma resposta final, podemos parar de processar eventos para esta consulta
                    break
                # Opcional: processar outros tipos de eventos (ex: tool_code, tool_result) se necessário
                # elif hasattr(event, 'tool_code') and event.tool_code:
                #     print(f"[{self.name}] Evento de ferramenta: {event.tool_code}")
                # elif hasattr(event, 'tool_result') and event.tool_result:
                #      print(f"[{self.name}] Resultado da ferramenta: {event.tool_result}")


            result = final_response or "Não foi possível obter uma resposta."

            # Atualiza o histórico de conversação APENAS se a execução do runner foi bem sucedida e houve resposta
            if maintain_context and final_response: # Verifica se houve resposta antes de adicionar ao histórico
                self.conversation_history.append({
                    "query": query,
                    "response": result
                })

                # Mantém apenas as últimas 5 interações para evitar context overflow
                if len(self.conversation_history) > 5:
                    self.conversation_history = self.conversation_history[-5:]

            print(f"[{self.name}] Resposta gerada com sucesso")
            return result

        except Exception as e:
            error_msg = f"Erro ao processar a consulta: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            return f"Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."

    def _build_contextual_query(self, current_query: str) -> str:
        """
        Constrói uma consulta com contexto das conversas anteriores.
        """
        if not self.conversation_history:
            return current_query

        context = "CONTEXTO DA CONVERSA ANTERIOR:\n"
        for i, interaction in enumerate(self.conversation_history[-3:], 1):  # Últimas 3 interações
            context += f"{i}. Pergunta: {interaction['query']}\n"
            context += f"   Resposta: {interaction['response'][:100]}...\n\n"

        contextual_query = f"{context}NOVA PERGUNTA: {current_query}\n\nResponda considerando o contexto acima quando relevante."
        return contextual_query

    def reset_conversation(self):
        """
        Limpa o histórico de conversação.
        """
        self.conversation_history = []
        print(f"[{self.name}] Histórico de conversação limpo")

    def get_conversation_summary(self) -> str:
        """
        Retorna um resumo da conversa atual.
        """
        if not self.conversation_history:
            return "Nenhuma conversa iniciada ainda."

        summary = f"Resumo da conversa ({len(self.conversation_history)} interações):\n"
        for i, interaction in enumerate(self.conversation_history, 1):
            summary += f"{i}. {interaction['query'][:50]}...\n"

        return summary