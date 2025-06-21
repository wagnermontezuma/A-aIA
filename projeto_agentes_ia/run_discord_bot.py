# run_discord_bot.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    """Executa o bot Discord."""
    load_dotenv()

    print("🤖 Iniciando AgentEIA Discord Bot...")
    print("🔧 Verificando configurações...")

    # Verificar API keys
    required_keys = ["DISCORD_BOT_TOKEN"]
    optional_keys = ["GOOGLE_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY"]

    missing_required = []
    missing_optional = []

    for key in required_keys:
        if not os.getenv(key):
            missing_required.append(key)

    for key in optional_keys:
        if not os.getenv(key):
            missing_optional.append(key)

    if missing_required:
        print(f"❌ Chaves obrigatórias ausentes: {', '.join(missing_required)}")
        print("Configure essas chaves no arquivo .env:")
        print("DISCORD_BOT_TOKEN=SEU_TOKEN_AQUI") # Use um placeholder aqui
        return

    if missing_optional:
        print(f"⚠️  Chaves opcionais ausentes: {', '.join(missing_optional)}")
        print("Alguns agentes podem não funcionar completamente.")

    print("✅ Configurações verificadas")
    print("🚀 Iniciando bot...")
    print("📱 Use /agenteia modelo:adk pergunta:sua pergunta no Discord!")
    print("🔧 Para parar o bot: Ctrl+C")
    print()

    # Importar e executar o bot
    try:
        from discord_bot.bot import run_bot
        run_bot()
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todos os arquivos foram criados corretamente.")
    except Exception as e:
        print(f"❌ Erro ao executar o bot: {e}")

if __name__ == "__main__":
    main()