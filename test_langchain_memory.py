import asyncio
import os
from dotenv import load_dotenv
from projeto_agentes_ia.agents.langchain_agent_with_memory import LangChainAgentWithMemory

async def test_langchain_memory():
    """Testa especificamente a memória do agente LangChain."""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não configurada")
        return

    print("=== Teste de Memória do LangChain ===\n")

    try:
        # Inicializar o agente
        agent = LangChainAgentWithMemory()

        # Definir contexto do usuário
        user_id = "test_memory_user"
        session_id = "langchain_memory_test"
        agent.set_user_context(user_id, session_id)

        # Sequência de perguntas para testar memória
        test_sequence = [
            "Meu nome é João e eu trabalho como engenheiro de software.",
            "Eu gosto muito de Python e estou aprendendo sobre IA.",
            "Qual é o meu nome?",
            "Qual é a minha profissão?",
            "Qual linguagem de programação eu gosto?",
            "Sobre o que estou aprendendo?",
            "Você pode me fazer um resumo do que sabe sobre mim?"
        ]

        for i, query in enumerate(test_sequence, 1):
            print(f"--- Pergunta {i} ---")
            print(f"👤 Usuário: {query}")

            try:
                response = await agent._run_async(query)
                print(f"🤖 LangChain: {response}")

                # Verificar se há indícios de memória nas respostas
                if i > 2:  # A partir da terceira pergunta
                    keywords = ["joão", "engenheiro", "python", "ia", "inteligência"]
                    if any(keyword in response.lower() for keyword in keywords):
                        print("✅ Memória detectada na resposta!")
                    else:
                        print("⚠️  Memória não detectada claramente")

                print()

            except Exception as e:
                print(f"❌ Erro: {e}\n")

            await asyncio.sleep(1)  # Pausa entre perguntas

        print("=== Teste de Memória Concluído ===")

    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")

if __name__ == "__main__":
    asyncio.run(test_langchain_memory())