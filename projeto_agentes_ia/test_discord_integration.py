# test_discord_integration.py
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

async def test_discord_integration():
    """Testa a integração do Discord com os agentes."""
    load_dotenv()

    print("=== Teste de Integração Discord ===\n")

    # Verificar se o token está configurado
    if not os.getenv("DISCORD_BOT_TOKEN"):
        print("❌ DISCORD_BOT_TOKEN não configurado no arquivo .env")
        print("Adicione: DISCORD_BOT_TOKEN=seu_token_aqui")
        return

    try:
        # Testar imports
        from agents.agent_manager import AgentManager
        print("✅ Import do AgentManager realizado com sucesso")

        # Testar AgentManager
        manager = AgentManager()
        print("✅ AgentManager inicializado")

        # Testar agentes disponíveis
        agent_info = manager.get_agent_info()
        print(f"✅ Agentes disponíveis: {agent_info['available_agents']}")

        # Simular interação se houver agentes
        if agent_info['available_agents']:
            test_agent = agent_info['available_agents'][0] # Use o primeiro agente disponível para o teste
            manager.set_agent(test_agent)
            manager.set_user_context("test_discord_user", "test_session")

            response = await manager.run_current_agent_with_context(
                "Teste de integração Discord",
                "test_discord_user",
                "test_session"
            )

            print(f"✅ Teste de agente bem-sucedido: {response[:100]}...")

        # Testar import do bot Discord
        from discord_bot.bot import AgentEIABot
        print("✅ Import do bot Discord realizado com sucesso")

        print("\n🤖 Bot Discord pronto para execução!")
        print("Execute: python run_discord_bot.py")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discord_integration())