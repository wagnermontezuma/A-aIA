import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_memory_components():
    """Testa os componentes de memória individualmente."""
    print("=== Teste dos Componentes de Memória ===\n")

    try:
        # Testar MemoryManager
        from memory.memory_manager import MemoryManager, ConversationEntry

        memory_manager = MemoryManager()
        print("✅ MemoryManager inicializado com sucesso")

        # Testar entrada de conversa
        entry = ConversationEntry(
            timestamp="2025-01-01T12:00:00",
            user_id="test_user",
            session_id="test_session",
            user_message="Olá!",
            agent_response="Olá! Como posso ajudar?",
            agent_type="test"
        )

        memory_manager.save_interaction(
            user_id="test_user",
            session_id="test_session",
            user_message="Teste de memória",
            agent_response="Memória funcionando!",
            agent_type="test"
        )
        print("✅ Interação salva na memória")

        # Testar recuperação de contexto
        context = memory_manager.get_context_for_agent("test_user", "test_session")
        print(f"✅ Contexto recuperado: {len(context)} caracteres")

    except Exception as e:
        print(f"❌ Erro no teste de memória: {e}")

    try:
        # Testar RAGManager
        from memory.rag_system import RAGManager

        rag_manager = RAGManager(use_advanced=False)  # Usar versão simples
        print("✅ RAGManager inicializado com sucesso")

        # Adicionar conhecimento
        doc_id = rag_manager.add_knowledge(
            "Python é uma linguagem de programação de alto nível.",
            source="manual_test"
        )
        print(f"✅ Conhecimento adicionado: {doc_id[:8]}...")

        # Buscar conhecimento
        context = rag_manager.get_relevant_context("Python programação")
        print(f"✅ Contexto RAG recuperado: {len(context)} caracteres")

    except Exception as e:
        print(f"❌ Erro no teste de RAG: {e}")

async def test_agents_with_memory():
    """Testa os agentes com memória."""
    load_dotenv()

    print("\n=== Teste dos Agentes com Memória ===\n")

    # Testar agente ADK com memória
    try:
        from agents.adk_agent_with_memory import ADKAgentWithMemory

        if os.getenv("GOOGLE_API_KEY"):
            print("🤖 Testando Agente ADK com Memória...")

            adk_agent = ADKAgentWithMemory()
            adk_agent.set_user_context("test_user", "adk_session")

            # Adicionar conhecimento
            adk_agent.add_knowledge(
                "O usuário prefere Python e está aprendendo IA.",
                source="user_profile"
            )

            # Testar conversa
            response = await adk_agent._run_async("Qual é minha linguagem preferida?")
            print(f"✅ ADK Resposta: {response[:100]}...")

        else:
            print("⚠️  GOOGLE_API_KEY não configurada - pulando teste ADK")

    except Exception as e:
        print(f"❌ Erro no teste ADK: {e}")

    # Testar agente LangChain com memória
    try:
        from agents.langchain_agent_with_memory import LangChainAgentWithMemory

        if os.getenv("OPENAI_API_KEY"):
            print("\n🤖 Testando Agente LangChain com Memória...")

            lc_agent = LangChainAgentWithMemory()
            lc_agent.set_user_context("test_user", "lc_session")

            # Adicionar conhecimento
            lc_agent.add_knowledge(
                "O usuário está desenvolvendo um projeto de chatbot.",
                source="project_info"
            )

            # Testar conversa
            response = await lc_agent._run_async("Sobre o que estou trabalhando?")
            print(f"✅ LangChain Resposta: {response[:100]}...")

        else:
            print("⚠️  OPENAI_API_KEY não configurada - pulando teste LangChain")

    except Exception as e:
        print(f"❌ Erro no teste LangChain: {e}")

async def test_agent_manager_with_memory():
    """Testa o gerenciador de agentes com memória."""
    print("\n=== Teste do Gerenciador de Agentes com Memória ===\n")

    try:
        from agents.agent_manager import AgentManager

        manager = AgentManager()
        print("✅ AgentManager inicializado")

        # Configurar contexto
        manager.set_user_context("test_user", "manager_session")

        # Adicionar conhecimento
        if hasattr(manager, 'add_knowledge_to_current_agent'):
            manager.add_knowledge_to_current_agent(
                "Este é um teste do sistema de memória integrado.",
                source="integration_test"
            )
            print("✅ Conhecimento adicionado ao agente atual")

        # Testar execução com contexto
        if hasattr(manager, 'run_current_agent_with_context'):
            response = await manager.run_current_agent_with_context(
                "Você lembra do que acabamos de adicionar?",
                "test_user",
                "manager_session"
            )
            print(f"✅ Resposta com contexto: {response[:100]}...")

    except Exception as e:
        print(f"❌ Erro no teste do gerenciador: {e}")

def main():
    """Função principal de teste."""
    print("🚀 Iniciando testes do sistema de memória...\n")

    # Testar componentes básicos
    test_memory_components()

    # Testar agentes (assíncrono)
    asyncio.run(test_agents_with_memory())

    # Testar gerenciador (assíncrono)
    asyncio.run(test_agent_manager_with_memory())

    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    main()