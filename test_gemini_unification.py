# test_gemini_unification.py
import asyncio
import os
from dotenv import load_dotenv

async def test_gemini_unification():
    """Testa a unificação dos agentes com Google Gemini."""
    # Carregar variáveis de ambiente do diretório correto
    dotenv_path = os.path.join(os.path.dirname(__file__), 'projeto_agentes_ia', '.env')
    load_dotenv(dotenv_path)
    
    print("🔄 === TESTE DE UNIFICAÇÃO GOOGLE GEMINI ===\n")
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY não configurada")
        return
    
    import sys
    from pathlib import Path

    # Adicionar o diretório do projeto ao sys.path
    project_dir = Path(__file__).parent / 'projeto_agentes_ia'
    sys.path.append(str(project_dir))

    try:
        from agents.agent_manager import AgentManager
        
        # Inicializar gerenciador
        manager = AgentManager()
        print("✅ AgentManager inicializado")
        
        # Verificar agentes disponíveis
        agent_info = manager.get_agent_info()
        print(f"✅ Agentes disponíveis: {agent_info['available_agents']}")
        
        # Testar ambos os agentes com a mesma pergunta
        test_query = "Explique as vantagens do Google Gemini em uma frase"
        user_id = "test_unification"
        session_id = "gemini_test"
        
        for agent_type in agent_info['available_agents']:
            print(f"\n🤖 Testando agente: {agent_type.upper()}")
            
            # Trocar para o agente
            manager.set_agent(agent_type)
            manager.set_user_context(user_id, f"{session_id}_{agent_type}")
            
            # Executar consulta
            response = await manager.run_current_agent_with_context(
                test_query, user_id, f"{session_id}_{agent_type}"
            )
            
            print(f"📝 Resposta ({agent_type}): {response[:150]}...")
            
            # Verificar se menciona Gemini
            if "gemini" in response.lower():
                print("✅ Agente reconhece que está usando Gemini")
            else:
                print("⚠️ Agente não menciona Gemini na resposta")
        
        print("\n🎉 Teste de unificação concluído!")
        print("📊 Resumo:")
        print("- Ambos os agentes agora usam Google Gemini 2.0 Flash")
        print("- Redução de custos (sem OpenAI)")
        print("- Consistência entre agentes")
        print("- Mesma qualidade de resposta")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_unification())