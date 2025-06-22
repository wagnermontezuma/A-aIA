import asyncio
import os
from dotenv import load_dotenv
from agents.agent_manager import AgentManager

async def test_memory_system():
    """Testa o sistema de memória dos agentes."""
    load_dotenv()

    print("=== Teste do Sistema de Memória dos Agentes ===\n")

    # Inicializar o gerenciador
    agent_manager = AgentManager()

    # Definir contexto do usuário
    user_id = "test_user_123"
    session_id = "session_memory_test"
    agent_manager.set_user_context(user_id, session_id)

    # Adicionar conhecimento específico
    print("📚 Adicionando conhecimento específico...")
    knowledge_content = """
    João Silva é um cliente da empresa há 3 anos.
    Ele trabalha como engenheiro de software em São Paulo.
    Suas preferências incluem: Python, React, e tecnologias de IA.
    Projeto atual: Sistema de recomendação usando machine learning.
    Orçamento aprovado: R$ 50.000 para consultoria em IA.
    """

    agent_manager.add_knowledge_to_current_agent(
        knowledge_content,
        source="crm_system",
        metadata={"client_id": "joao_silva_001", "type": "client_profile"}
    )

    # Sequência de perguntas para testar memória
    test_conversations = [
        "Olá! Meu nome é João Silva e sou engenheiro de software.",
        "Estou interessado em implementar IA no meu projeto atual.",
        "Qual seria o custo aproximado para uma consultoria?",
        "Você lembra qual é minha linguagem de programação preferida?",
        "E sobre meu orçamento aprovado, você tem essa informação?"
    ]

    print(f"🤖 Testando com agente: {agent_manager.current_agent}\n")

    for i, query in enumerate(test_conversations, 1):
        print(f"--- Conversa {i} ---")
        print(f"👤 Usuário: {query}")

        try:
            response = await agent_manager.run_current_agent_with_context(
                query, user_id, session_id
            )
            print(f"🤖 Agente: {response}")
            print()

            # Pausa entre perguntas
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Erro: {e}\n")

    # Testar troca de agente e continuidade de memória
    print("🔄 Trocando para o outro agente...")
    other_agent = "langchain" if agent_manager.current_agent == "adk" else "adk"

    if other_agent in agent_manager.agents:
        agent_manager.set_agent(other_agent)
        agent_manager.set_user_context(user_id, session_id)

        print(f"🤖 Agora testando com: {agent_manager.current_agent}")

        test_query = "Você consegue me lembrar do que conversamos antes sobre meu projeto?"
        print(f"👤 Usuário: {test_query}")

        try:
            response = await agent_manager.run_current_agent_with_context(
                test_query, user_id, session_id
            )
            print(f"🤖 Agente: {response}")
        except Exception as e:
            print(f"❌ Erro: {e}")

    print("\n=== Teste de Memória Concluído ===")

if __name__ == "__main__":
    asyncio.run(test_memory_system())