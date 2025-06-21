import asyncio
import os
from dotenv import load_dotenv
from agents.agent_manager import AgentManager

async def test_memory_functionality():
    """Testa se a memória está funcionando corretamente."""
    load_dotenv()
    
    print("=== Teste de Validação da Memória ===\n")
    
    # Inicializar o gerenciador
    manager = AgentManager()
    
    # Definir contexto do usuário
    user_id = "test_memory_user"
    session_id = "memory_test_session"
    
    # Teste com ambos os agentes
    agents_to_test = ["adk", "langchain"]
    
    for agent_type in agents_to_test:
        if agent_type in manager.agents:
            print(f"\n🤖 Testando memória com agente: {agent_type.upper()}")
            manager.set_agent(agent_type)
            manager.set_user_context(user_id, session_id)
            
            # Sequência de perguntas para testar memória
            test_sequence = [
                "Meu nome é João e eu gosto de futebol.",
                "Qual é o meu nome?",
                "Do que eu gosto?",
                "Você lembra de mim?"
            ]
            
            for i, query in enumerate(test_sequence, 1):
                print(f"\n--- Pergunta {i} ---")
                print(f"👤 Usuário: {query}")
                
                try:
                    response = await manager.run_current_agent_with_context(
                        query, user_id, session_id
                    )
                    print(f"🤖 {agent_type.upper()}: {response}")
                    
                    # Verificar se há indícios de memória nas respostas
                    if i > 1:  # A partir da segunda pergunta
                        if "joão" in response.lower() or "futebol" in response.lower():
                            print("✅ Memória detectada na resposta!")
                        else:
                            print("⚠️  Memória não detectada na resposta")
                    
                except Exception as e:
                    print(f"❌ Erro: {e}")
                
                await asyncio.sleep(1)  # Pausa entre perguntas
        else:
            print(f"⚠️  Agente {agent_type} não disponível")
    
    print("\n=== Teste de Memória Concluído ===")

if __name__ == "__main__":
    asyncio.run(test_memory_functionality())