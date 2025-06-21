# force_restart_bot.py
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import importlib
import gc

def force_restart_bot():
    """Reinicia o bot com limpeza completa de cache."""
    print("🔄 Iniciando reinicialização forçada do bot...")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar token
    if not os.getenv("DISCORD_BOT_TOKEN"):
        print("❌ DISCORD_BOT_TOKEN não encontrado")
        return
    
    print("🧹 Limpando cache Python...")
    
    # Forçar garbage collection
    gc.collect()
    
    print("🔄 Reiniciando bot com sincronização forçada...")
    print("⏳ Aguarde a sincronização dos comandos...")
    print("💡 Após inicializar, use Ctrl+R ou Cmd+R no Discord")
    print()
    
    # Importar e executar o bot
    try:
        # Adicionar o diretório do bot ao path para importação
        bot_dir = Path(__file__).parent / "projeto_agentes_ia" / "discord_bot"
        sys.path.append(str(bot_dir.parent)) # Adiciona a raiz do projeto
        
        # Recarregar módulos se necessário (para garantir que as mudanças sejam aplicadas)
        if 'discord_bot.bot' in sys.modules:
            importlib.reload(sys.modules['discord_bot.bot'])
        
        from discord_bot.bot import run_bot
        run_bot()
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    force_restart_bot()