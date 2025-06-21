# test_langchain_fixed.py
import os
import asyncio
from dotenv import load_dotenv
from agents.langchain_agent import LangChainAgent

async def test_langchain_agent():
    """Testa o agente LangChain corrigido."""
    load_dotenv()
    
    # Verificar API keys
    missing_keys = []
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.getenv("TAVILY_API_KEY"):
        missing_keys.append("TAVILY_API_KEY")
    
    if missing_keys:
        print(f"❌ API keys faltando: {', '.join(missing_keys)}")
        print("Configure essas chaves no arquivo .env para testar o agente LangChain")
        return
    
    try:
        print("=== Teste do Agente LangChain Corrigido ===\n")
        
        # Criar o agente
        agent = LangChainAgent()
        
        # Lista de perguntas de teste
        test_queries = [
            "Qual é a capital do Brasil?",
            "Explique o que é inteligência artificial em uma frase simples.",
            "Quanto é 25 + 17?",
            "Qual é a diferença entre Python e JavaScript?"
        ]
        
        # Executar cada pergunta
        for i, query in enumerate(test_queries, 1):
            print(f"--- Teste {i} ---")
            print(f"Pergunta: {query}")
            
            try:
                result = await agent._run_async(query)
                print(f"Resposta: {result}")
                print("✅ Sucesso!\n")
            except Exception as e:
                print(f"❌ Erro: {e}\n")
        
        print("=== Teste Concluído ===")
        
    except Exception as e:
        print(f"❌ Erro na inicialização do agente: {e}")

def main():
    """Wrapper síncrono para o teste assíncrono."""
    asyncio.run(test_langchain_agent())

if __name__ == "__main__":
    main()