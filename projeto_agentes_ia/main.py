# main.py
import os
from dotenv import load_dotenv
from agents.conversational_adk_agent import ConversationalADKAgent

def test_conversational_agent():
    """Testa o agente conversacional com múltiplas interações."""
    load_dotenv()

    # Verifica se a chave da API está configurada
    if not os.getenv("GOOGLE_API_KEY"):
        print("Erro: Configure a variável GOOGLE_API_KEY no arquivo .env")
        return

    print("=== Teste do Agente Conversacional ADK ===\n")

    # Inicializa o agente
    agent = ConversationalADKAgent(name="AssistenteInteligente")

    # Lista de perguntas para testar a conversação
    perguntas = [
        "Qual é a diferença entre inteligência artificial e machine learning?",
        "Pode dar exemplos práticos de cada um?",
        "Quais são as principais linguagens de programação usadas em IA?",
        "Como posso começar a estudar IA sendo iniciante?"
    ]

    # Executa as perguntas em sequência
    for i, pergunta in enumerate(perguntas, 1):
        print(f"--- Pergunta {i} ---")
        print(f"Usuário: {pergunta}")

        resposta = agent.run(pergunta, maintain_context=True)
        print(f"Assistente: {resposta}\n")

        # Pausa entre perguntas (opcional)
        input("Pressione Enter para continuar...")

    # Mostra resumo da conversa
    print("--- Resumo da Conversa ---")
    print(agent.get_conversation_summary())

if __name__ == "__main__":
    test_conversational_agent()