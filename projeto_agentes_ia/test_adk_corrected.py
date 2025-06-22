# test_adk_corrected.py
import os
from dotenv import load_dotenv
from agents.adk_agent import SimpleADKAgent

def test_corrected_adk_agent():
    """Testa o agente ADK corrigido usando o padrão Runner oficial."""
    load_dotenv()

    # Verificar se a API key está configurada
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY não encontrada no arquivo .env")
        print("Configure sua chave de API do Google para testar o agente.")
        return

    try:
        print("=== Teste do Agente ADK Corrigido ===\n")

        # Criar o agente com instrução específica
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
                result = agent.run(query)
                print(f"Resposta: {result}")
                print("✅ Sucesso!\n")
            except Exception as e:
                print(f"❌ Erro: {e}\n")

        print("=== Teste Concluído ===")

    except Exception as e:
        print(f"❌ Erro na inicialização do agente: {e}")
        print("Verifique se todas as dependências estão instaladas corretamente.")

if __name__ == "__main__":
    test_corrected_adk_agent()