# debug_chat_error.py
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

async def test_chat_functionality():
    """Testa a funcionalidade de chat diretamente."""
    print("=== Teste de Diagnóstico do Chat ===\n")
    
    try:
        from agents.agent_manager import AgentManager
        
        print("1. Inicializando AgentManager...")
        manager = AgentManager()
        print("✅ AgentManager inicializado")
        
        print("2. Definindo contexto do usuário...")
        user_id = "debug_user"
        session_id = "debug_session"
        manager.set_user_context(user_id, session_id)
        print("✅ Contexto definido")
        
        print("3. Testando método run_current_agent_with_context...")
        if hasattr(manager, 'run_current_agent_with_context'):
            print("✅ Método existe")
            
            test_query = "Olá, como você está?"
            print(f"4. Executando consulta: '{test_query}'")
            
            response = await manager.run_current_agent_with_context(
                test_query, user_id, session_id
            )
            
            print(f"✅ Resposta recebida: {response[:100]}...")
            
        else:
            print("❌ Método run_current_agent_with_context não existe")
            print("Testando método alternativo...")
            
            response = await manager.run_current_agent(test_query)
            print(f"✅ Resposta alternativa: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_chat_functionality())