# test_adk_async.py
import asyncio
import os
from dotenv import load_dotenv
from agents.adk_agent import SimpleADKAgent

async def test_adk_agent_async():
    """Testa o agente ADK usando métodos assíncronos corretamente."""
    load_dotenv()

    # Verificar se a API key está configurada
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY não encontrada no arquivo .env")
        return

    try:
        print("=== Teste Assíncrono do Agente ADK ===\n")

        # Criar o agente
        instruction = """
        Você é um assistente útil e inteligente.
        Responda às perguntas de forma clara, concisa e informativa.
        Se não souber algo, seja honesto sobre isso.
        """

        agent = SimpleADKAgent(instruction=instruction)

        # Lista de perguntas de teste
        test_queries = [
            "Qual é a capital do Brasil?",
            "Explique o que é inteligência artificial em uma frase simples.",
            "Quanto é 15 + 27?",
            "Qual é a diferença entre Python e JavaScript?"
        ]

        # Executar cada pergunta
        for i, query in enumerate(test_queries, 1):
            print(f"--- Teste {i} ---")
            print(f"Pergunta: {query}")

            try:
                # Usar o método assíncrono interno diretamente
                result = await agent._run_async(query)
                print(f"Resposta: {result}")
                print("✅ Sucesso!\n")
            except Exception as e:
                print(f"❌ Erro: {e}\n")

        print("=== Teste Concluído ===")

    except Exception as e:
        print(f"❌ Erro na inicialização do agente: {e}")

def test_adk_agent_sync():
    """Wrapper síncrono para o teste assíncrono."""
    asyncio.run(test_adk_agent_async())

if __name__ == "__main__":
    test_adk_agent_sync()